#!/usr/bin/env python3
"""Backward-compatible wrapper — prefer `matrixscroll hook-install`."""

from matrixscroll.git import hook_status, install_hooks


def main() -> int:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Install Matrix Scroll Git hooks")
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    try:
        if args.status:
            print(json.dumps(hook_status(), indent=2))
        elif args.remove:
            print(json.dumps(install_hooks(remove=True)))
        else:
            print(json.dumps(install_hooks()))
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
