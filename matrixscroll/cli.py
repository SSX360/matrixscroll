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
import subprocess
import sys
from pathlib import Path

from ._core import sign_manifest, status, verify_manifest
from .policy import VerifyPolicy, verify_manifest_with_policy
from ._claim import cmd_claim, cmd_identity, resolve_identity
from ._payment import sign_payment

try:
    from . import git as _git
    from . import gate as _gate
except ImportError:  # pragma: no cover
    _git = None  # type: ignore[assignment]
    _gate = None  # type: ignore[assignment]


def _cmd_status(_args: argparse.Namespace) -> int:
    print(json.dumps(status(), indent=2, sort_keys=True))
    return 0


def _load_policy(args: argparse.Namespace) -> VerifyPolicy | None:
    policy = VerifyPolicy(
        require_mode=args.require_mode or None,
        verify_agent_scope=bool(getattr(args, "verify_agent_scope", False)),
    )
    if args.trusted_keys:
        file_policy = VerifyPolicy.from_json_file(args.trusted_keys)
        policy.trusted_public_keys = file_policy.trusted_public_keys
        if file_policy.require_mode and not policy.require_mode:
            policy.require_mode = file_policy.require_mode
        if file_policy.allowed_schemas:
            policy.allowed_schemas = file_policy.allowed_schemas
        if file_policy.require_actor_types:
            policy.require_actor_types = file_policy.require_actor_types
        if file_policy.deny_actor_types:
            policy.deny_actor_types = file_policy.deny_actor_types
        if file_policy.require_delegation_for_actor_types:
            policy.require_delegation_for_actor_types = file_policy.require_delegation_for_actor_types
        if file_policy.verify_agent_scope:
            policy.verify_agent_scope = True
    if policy.is_empty():
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
    res = {
        "ok": True,
        "device_id": block.get("device_id"),
        "mode": block.get("mode"),
        "signed_at": block.get("signed_at"),
    }
    if getattr(args, "identity", False):
        res["identity"] = resolve_identity(block)
    print(json.dumps(res, sort_keys=True))
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
    res = {
        "ok": True,
        "device_id": block.get("device_id"),
        "mode": block.get("mode"),
        "signed_at": block.get("signed_at"),
    }
    if getattr(args, "identity", False):
        res["identity"] = resolve_identity(block)
    print(json.dumps(res, sort_keys=True))
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


def _cmd_envelope_export_guac(args: argparse.Namespace) -> int:
    from . import guac_export as guac_mod

    try:
        result = guac_mod.export_guac_jsonl(Path(args.bundle), Path(args.output))
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


def _cmd_envelope_publish_rekor(args: argparse.Namespace) -> int:
    from . import rekor_publish as rekor_mod

    bundle = Path(args.bundle)
    try:
        if args.rekor_cli:
            result = rekor_mod.publish_rekor_cli(bundle, rekor_url=args.rekor_url or None)
        else:
            out = Path(args.output) if args.output else bundle / ".rekor-dry-run"
            result = rekor_mod.publish_rekor_dry_run(bundle, out)
    except (RuntimeError, FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


def _cmd_envelope_export(args: argparse.Namespace) -> int:
    if _gate is None:
        print(json.dumps({"ok": False, "error": "gate module unavailable"}))
        return 1
    try:
        result = _gate.export_envelope_bundle(
            args.base,
            args.head,
            Path(args.output),
        )
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_envelope_publish_notes(args: argparse.Namespace) -> int:
    if _gate is None:
        print(json.dumps({"ok": False, "error": "gate module unavailable"}))
        return 1
    try:
        result = _gate.publish_envelopes_to_notes(
            args.base,
            args.head,
            notes_ref=args.notes_ref,
        )
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_envelope_fetch_notes(args: argparse.Namespace) -> int:
    if _gate is None:
        print(json.dumps({"ok": False, "error": "gate module unavailable"}))
        return 1
    try:
        result = _gate.fetch_notes(args.remote, notes_ref=args.notes_ref)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_envelope_verify_range(args: argparse.Namespace) -> int:
    if _gate is None:
        print(json.dumps({"ok": False, "error": "gate module unavailable"}))
        return 1
    policy = _load_policy(args)
    bundle_dir = Path(args.bundle) if args.bundle else None
    try:
        summary = _gate.verify_envelope_range(
            args.base,
            args.head,
            source=args.source,
            notes_ref=args.notes_ref,
            bundle_dir=bundle_dir,
            policy=policy,
        )
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    if args.summary_output:
        Path(args.summary_output).write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("ok") else 2


def _add_range_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base", default="", help="Base ref for commit range (empty = all ancestors)")
    parser.add_argument("--head", required=True, help="Head ref for commit range")
    parser.add_argument(
        "--notes-ref",
        default="refs/notes/matrixscroll",
        help="Git notes ref for envelope transport",
    )


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
    parser.add_argument(
        "--verify-agent-scope",
        action="store_true",
        help="Verify provenance.agent_scope linked manifest signatures",
    )


def _cmd_sign_payment(args: argparse.Namespace) -> int:
    try:
        signed = sign_payment(
            tx_id=args.tx,
            amount=args.amount,
            currency=args.currency,
            merchant=args.merchant,
            payment_type=args.method,
            identifier_hash=args.hash,
            key_path=args.key_path or None
        )
        print(json.dumps(signed, indent=2, sort_keys=True))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _cmd_sign_action(args: argparse.Namespace) -> int:
    from .provenance import build_action_envelope, sign_action_envelope, validate_action_payload

    payload_path = Path(args.payload)
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": f"cannot read payload: {exc}"}))
        return 2
    ok, err = validate_action_payload(args.type, payload)
    if not ok:
        print(json.dumps({"ok": False, "error": err}))
        return 2
    envelope = build_action_envelope(
        args.type,  # type: ignore[arg-type]
        payload,
        actor_type=args.actor_type,
        tool=args.tool,
    )
    signed = sign_action_envelope(envelope)
    if args.output:
        Path(args.output).write_text(json.dumps(signed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(signed, indent=2, sort_keys=True))
    return 0


def _cmd_scroll_commit(args: argparse.Namespace) -> int:
    from .scroll import commit as scroll_commit

    result = scroll_commit(
        args.message,
        actor_type=args.actor_type,
        tool=args.tool,
        allow_empty=args.allow_empty,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="matrixscroll",
        description="Matrix Scroll / SSX360 root-of-trust CLI",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Print active provider status as JSON")

    verify_p = sub.add_parser("verify", help="Verify a signed manifest JSON file")
    verify_p.add_argument("manifest", help="Path to a signed manifest produced by sign_manifest")
    verify_p.add_argument("--identity", action="store_true", help="Resolve the signer's identity certificate and include it in output")
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
    env_verify.add_argument("--identity", action="store_true", help="Resolve the signer's identity certificate and include it in output")
    _add_policy_args(env_verify)
    env_verify.set_defaults(command="envelope-verify")

    env_export = sub.add_parser(
        "envelope-export",
        help="Export local commit envelopes for a range into a filesystem bundle",
    )
    _add_range_args(env_export)
    env_export.add_argument("--output", "-o", required=True, help="Output bundle directory")
    env_export.set_defaults(command="envelope-export")

    env_pub_notes = sub.add_parser(
        "envelope-publish-notes",
        help="Publish local commit envelopes to git notes",
    )
    _add_range_args(env_pub_notes)
    env_pub_notes.set_defaults(command="envelope-publish-notes")

    env_fetch_notes = sub.add_parser(
        "envelope-fetch-notes",
        help="Fetch envelope git notes from a remote",
    )
    env_fetch_notes.add_argument("--remote", default="origin", help="Remote name")
    env_fetch_notes.add_argument(
        "--notes-ref",
        default="refs/notes/matrixscroll",
        help="Git notes ref",
    )
    env_fetch_notes.set_defaults(command="envelope-fetch-notes")

    env_verify_range = sub.add_parser(
        "envelope-verify-range",
        help="Verify commit envelopes for every commit in a range",
    )
    _add_range_args(env_verify_range)
    env_verify_range.add_argument(
        "--source",
        choices=["local", "notes", "bundle"],
        default="local",
        help="Where to load envelopes from",
    )
    env_verify_range.add_argument(
        "--bundle",
        metavar="DIR",
        default="",
        help="Bundle directory when --source=bundle",
    )
    env_verify_range.add_argument(
        "--summary-output",
        metavar="PATH",
        default="",
        help="Write full JSON summary to this file",
    )
    _add_policy_args(env_verify_range)
    env_verify_range.set_defaults(command="envelope-verify-range")

    guac_export = sub.add_parser(
        "envelope-export-guac",
        help="Export verified envelopes from a bundle to GUAC JSONL",
    )
    guac_export.add_argument("--bundle", required=True, help="Envelope bundle directory")
    guac_export.add_argument("--output", "-o", required=True, help="Output JSONL path")
    guac_export.set_defaults(command="envelope-export-guac")

    rekor_pub = sub.add_parser(
        "envelope-publish-rekor",
        help="Publish envelopes to Rekor (dry-run by default)",
    )
    rekor_pub.add_argument("--bundle", required=True, help="Envelope bundle directory")
    rekor_pub.add_argument("--output", "-o", default="", help="Dry-run output directory")
    rekor_pub.add_argument(
        "--rekor-cli",
        action="store_true",
        help="Upload via rekor-cli (requires REKOR_URL)",
    )
    rekor_pub.add_argument("--rekor-url", default="", help="Rekor server URL override")
    rekor_pub.set_defaults(command="envelope-publish-rekor")

    claim_p = sub.add_parser("claim", help="Enroll this key and bind it to a verified identity")
    claim_p.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically")
    claim_p.set_defaults(command="claim")

    identity_p = sub.add_parser("identity", help="Check local verified-identity status")
    identity_p.set_defaults(command="identity")

    pay_p = sub.add_parser("sign-payment", help="Sign a payment transaction attestation")
    pay_p.add_argument("--tx", required=True, help="Transaction ID (starts with tx_)")
    pay_p.add_argument("--amount", type=float, required=True, help="Transaction amount")
    pay_p.add_argument("--currency", required=True, help="Currency code (e.g. USD, BTC)")
    pay_p.add_argument("--merchant", required=True, help="Merchant name")
    pay_p.add_argument("--method", choices=["virtual_card", "crypto_wallet", "bank_account"], required=True, help="Payment method type")
    pay_p.add_argument("--hash", required=True, help="SHA-256 hash of card token or wallet address")
    pay_p.add_argument("--key-path", help="Alternative signing key path")
    pay_p.set_defaults(command="sign-payment")

    sign_action_p = sub.add_parser(
        "sign-action",
        help="Sign a universal provenance action envelope (ci_step, iac_change, etc.)",
    )
    sign_action_p.add_argument(
        "--type",
        required=True,
        choices=["git_commit", "ci_step", "iac_change", "db_migration", "api_call", "contract_deploy"],
        help="Action type per schemas/action-envelope.v1.json",
    )
    sign_action_p.add_argument("--payload", required=True, help="JSON file with action-specific payload")
    sign_action_p.add_argument("--output", "-o", help="Write signed envelope to file")
    sign_action_p.add_argument(
        "--actor-type",
        default="human",
        choices=["human", "agent", "ci"],
        help="Provenance actor label",
    )
    sign_action_p.add_argument("--tool", default="matrixscroll", help="Producing tool name")
    sign_action_p.set_defaults(command="sign-action")

    scroll_p = sub.add_parser("scroll", help="SSX360 Scroll — Git wrapper with auto-envelope (Phase 1)")
    scroll_sub = scroll_p.add_subparsers(dest="scroll_command")
    scroll_commit_p = scroll_sub.add_parser("commit", help="git commit + signed envelope")
    scroll_commit_p.add_argument("-m", "--message", required=True)
    scroll_commit_p.add_argument("--actor-type", default="human", choices=["human", "agent", "ci"])
    scroll_commit_p.add_argument("--tool", default="scroll")
    scroll_commit_p.add_argument("--allow-empty", action="store_true")
    scroll_commit_p.set_defaults(command="scroll-commit")

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
        "envelope-export": _cmd_envelope_export,
        "envelope-publish-notes": _cmd_envelope_publish_notes,
        "envelope-fetch-notes": _cmd_envelope_fetch_notes,
        "envelope-verify-range": _cmd_envelope_verify_range,
        "envelope-export-guac": _cmd_envelope_export_guac,
        "envelope-publish-rekor": _cmd_envelope_publish_rekor,
        "claim": cmd_claim,
        "identity": cmd_identity,
        "sign-payment": _cmd_sign_payment,
        "sign-action": _cmd_sign_action,
        "scroll-commit": _cmd_scroll_commit,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
