"""Command-line interface for Matrix Scroll.

Exposed as the ``matrixscroll`` console script. Kept dependency-free
(argparse + json) so it works without spinning up a host application —
useful for support sessions and release-evidence verification.

Subcommands:
  status                 Print the active provider status as JSON.
  verify <manifest.json> Verify a signed manifest; exits 0 on pass, 2 on fail.
  sign <manifest.json>   Sign a manifest from disk; prints the signed JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ._core import sign_manifest, status, verify_manifest
from .policy import VerifyPolicy, verify_manifest_with_policy

try:
    from . import git as _git
except ImportError:  # pragma: no cover
    _git = None  # type: ignore[assignment]


def _cmd_status(_args: argparse.Namespace) -> int:
    print(json.dumps(status(), indent=2, sort_keys=True))
    return 0


def _load_policy(args: argparse.Namespace) -> VerifyPolicy | None:
    policy = VerifyPolicy(require_mode=args.require_mode or None)
    if args.trusted_keys:
        file_policy = VerifyPolicy.from_json_file(args.trusted_keys)
        policy.trusted_public_keys = file_policy.trusted_public_keys
        if file_policy.require_mode and not policy.require_mode:
            policy.require_mode = file_policy.require_mode
        if file_policy.allowed_schemas:
            policy.allowed_schemas = file_policy.allowed_schemas
    if (
        policy.require_mode is None
        and policy.trusted_public_keys is None
        and policy.allowed_schemas is None
    ):
        return None
    return policy


def _cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.manifest)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": f"cannot read manifest: {exc}"}))
        return 2
    policy = _load_policy(args)
    if policy is not None:
        ok, reason = verify_manifest_with_policy(manifest, policy)
        if not ok:
            print(json.dumps({"ok": False, "error": reason or "policy verification failed"}))
            return 2
    else:
        ok = verify_manifest(manifest)
        if not ok:
            print(json.dumps({"ok": False, "error": "cryptographic verification failed"}))
            return 2
    block = manifest.get("signature") or {}
    print(json.dumps({
        "ok": True,
        "device_id": block.get("device_id"),
        "mode": block.get("mode"),
        "signed_at": block.get("signed_at"),
    }, sort_keys=True))
    return 0


def _cmd_hook_install(_args: argparse.Namespace) -> int:
    from . import git as git_mod
    try:
        result = git_mod.install_hooks()
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


def _cmd_hook_status(_args: argparse.Namespace) -> int:
    from . import git as git_mod
    try:
        print(json.dumps(git_mod.hook_status(), indent=2))
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    return 0


def _cmd_envelope_build(args: argparse.Namespace) -> int:
    if _git is None:
        print(json.dumps({"ok": False, "error": "git module unavailable"}))
        return 1
    message = args.message
    envelope = _git.build_commit_envelope(message=message)
    signed = _git.sign_commit_envelope(envelope)
    if args.output:
        Path(args.output).write_text(json.dumps(signed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(signed, indent=2, sort_keys=True))
    return 0


def _cmd_envelope_verify(args: argparse.Namespace) -> int:
    if _git is None:
        print(json.dumps({"ok": False, "error": "git module unavailable"}))
        return 1
    target = args.target
    path = Path(target)
    if path.is_file():
        envelope = json.loads(path.read_text(encoding="utf-8-sig"))
    else:
        env_path = _git.envelope_path(target)
        if not env_path.is_file():
            print(json.dumps({"ok": False, "error": f"no envelope for {target}"}))
            return 2
        envelope = json.loads(env_path.read_text(encoding="utf-8-sig"))
    policy = _load_policy(args)
    if policy is not None:
        ok, reason = verify_manifest_with_policy(envelope, policy)
        if not ok:
            print(json.dumps({"ok": False, "error": reason or "policy verification failed"}))
            return 2
    else:
        ok = verify_manifest(envelope)
        if not ok:
            print(json.dumps({"ok": False, "error": "cryptographic verification failed"}))
            return 2
    block = envelope.get("signature") or {}
    print(json.dumps({
        "ok": True,
        "device_id": block.get("device_id"),
        "mode": block.get("mode"),
        "signed_at": block.get("signed_at"),
    }, sort_keys=True))
    return 0


def _cmd_sign(args: argparse.Namespace) -> int:
    path = Path(args.manifest)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": f"cannot read manifest: {exc}"}))
        return 2
    signed = sign_manifest(manifest)
    print(json.dumps(signed, indent=2, sort_keys=True))
    return 0


def _add_policy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--require-mode",
        metavar="MODE",
        default="",
        help="Require signature mode (e.g. emulated, hardware)",
    )
    parser.add_argument(
        "--trusted-keys",
        metavar="PATH",
        default="",
        help="JSON file with trusted_public_keys and optional policy fields",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="matrixscroll",
        description="Matrix Scroll / SSX360 root-of-trust CLI",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Print active provider status as JSON")

    verify_p = sub.add_parser("verify", help="Verify a signed manifest JSON file")
    verify_p.add_argument("manifest", help="Path to a signed manifest produced by sign_manifest")
    _add_policy_args(verify_p)

    sign_p = sub.add_parser("sign", help="Sign a manifest JSON file with the active provider")
    sign_p.add_argument("manifest", help="Path to a manifest JSON file to sign")

    sub.add_parser("hook", help="Install Matrix Scroll git hooks in the current repo").set_defaults(
        command="hook-install"
    )
    sub.add_parser("hook-install", help="Install Matrix Scroll git hooks in the current repo")
    sub.add_parser("hook-status", help="Print git hook installation status as JSON")

    env_build = sub.add_parser("envelope", help="Build and sign a commit envelope")
    env_build.add_argument("--message", "-m", help="Commit message override")
    env_build.add_argument("--output", "-o", help="Write signed envelope to file")
    env_build.set_defaults(command="envelope-build")

    env_verify = sub.add_parser("envelope-verify", help="Verify a commit envelope by path or commit sha")
    env_verify.add_argument("target", help="Envelope file path or 40-char commit sha")
    _add_policy_args(env_verify)
    env_verify.set_defaults(command="envelope-verify")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        None: _cmd_status,
        "status": _cmd_status,
        "verify": _cmd_verify,
        "sign": _cmd_sign,
        "hook-install": _cmd_hook_install,
        "hook-status": _cmd_hook_status,
        "envelope-build": _cmd_envelope_build,
        "envelope-verify": _cmd_envelope_verify,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
