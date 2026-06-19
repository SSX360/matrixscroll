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


def _cmd_status(_args: argparse.Namespace) -> int:
    print(json.dumps(status(), indent=2, sort_keys=True))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.manifest)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": f"cannot read manifest: {exc}"}))
        return 2
    ok = verify_manifest(manifest)
    block = manifest.get("signature") or {}
    print(json.dumps({
        "ok": ok,
        "device_id": block.get("device_id"),
        "mode": block.get("mode"),
        "signed_at": block.get("signed_at"),
    }, sort_keys=True))
    return 0 if ok else 2


def _cmd_sign(args: argparse.Namespace) -> int:
    path = Path(args.manifest)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": f"cannot read manifest: {exc}"}))
        return 2
    signed = sign_manifest(manifest)
    print(json.dumps(signed, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="matrixscroll",
        description="Matrix Scroll / SSX360 root-of-trust CLI",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Print active provider status as JSON")

    verify_p = sub.add_parser("verify", help="Verify a signed manifest JSON file")
    verify_p.add_argument("manifest", help="Path to a signed manifest produced by sign_manifest")

    sign_p = sub.add_parser("sign", help="Sign a manifest JSON file with the active provider")
    sign_p.add_argument("manifest", help="Path to a manifest JSON file to sign")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        None: _cmd_status,
        "status": _cmd_status,
        "verify": _cmd_verify,
        "sign": _cmd_sign,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
