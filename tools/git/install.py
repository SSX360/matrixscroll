#!/usr/bin/env python3
"""Install Matrix Scroll Git hooks into the current repository.

Usage:
    python -m tools.git.install          # install hooks
    python -m tools.git.install --remove # uninstall hooks
    python -m tools.git.install --status # print JSON status
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HOOKS = ("pre-commit", "pre-push")
MARKER = "# matrixscroll-git hook\n"
DEFAULT_CONFIG = {
    "enforce": False,
    "actor_type": "human",
    "tool": "git-cli",
}


def repo_root() -> Path:
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("not inside a git repository")
    return Path(result.stdout.strip())


def hooks_dir(root: Path) -> Path:
    git_dir = root / ".git"
    if (git_dir / "hooks").is_dir():
        return git_dir / "hooks"
    raise SystemExit(".git/hooks not found")


def matrixscroll_dir(root: Path) -> Path:
    return root / ".git" / "matrixscroll"


def template_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "hooks" / name


def install_hook(hooks: Path, name: str) -> None:
    src = template_path(name)
    dst = hooks / name
    content = src.read_text(encoding="utf-8")
    if dst.exists():
        existing = dst.read_text(encoding="utf-8")
        if MARKER in existing and "matrixscroll" in existing:
            return
        backup = dst.with_suffix(dst.suffix + ".matrixscroll.bak")
        shutil.copy2(dst, backup)
    dst.write_text(content, encoding="utf-8")
    try:
        os.chmod(dst, 0o755)
    except OSError:
        pass


def remove_hook(hooks: Path, name: str) -> None:
    dst = hooks / name
    if not dst.exists():
        return
    text = dst.read_text(encoding="utf-8")
    if MARKER not in text:
        return
    backup = dst.with_suffix(dst.suffix + ".matrixscroll.bak")
    if backup.exists():
        shutil.copy2(backup, dst)
        backup.unlink()
    else:
        dst.unlink()


def write_config(root: Path) -> None:
    ms_dir = matrixscroll_dir(root)
    ms_dir.mkdir(parents=True, exist_ok=True)
    (ms_dir / "envelopes").mkdir(exist_ok=True)
    config_path = ms_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2) + "\n",
            encoding="utf-8",
        )


def cmd_install(root: Path) -> int:
    hooks = hooks_dir(root)
    for name in HOOKS:
        install_hook(hooks, name)
    write_config(root)
    print(json.dumps({"ok": True, "installed": list(HOOKS), "root": str(root)}))
    return 0


def cmd_remove(root: Path) -> int:
    hooks = hooks_dir(root)
    for name in HOOKS:
        remove_hook(hooks, name)
    print(json.dumps({"ok": True, "removed": list(HOOKS)}))
    return 0


def cmd_status(root: Path) -> int:
    hooks = hooks_dir(root)
    installed = {}
    for name in HOOKS:
        path = hooks / name
        installed[name] = path.is_file() and MARKER in path.read_text(encoding="utf-8")
    ms_dir = matrixscroll_dir(root)
    envelope_count = len(list((ms_dir / "envelopes").glob("*.json"))) if (ms_dir / "envelopes").is_dir() else 0
    print(json.dumps({
        "ok": True,
        "root": str(root),
        "hooks": installed,
        "envelope_count": envelope_count,
        "config": json.loads((ms_dir / "config.json").read_text(encoding="utf-8")) if (ms_dir / "config.json").is_file() else None,
    }, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install Matrix Scroll Git hooks")
    parser.add_argument("--remove", action="store_true", help="Uninstall hooks")
    parser.add_argument("--status", action="store_true", help="Print hook status JSON")
    args = parser.parse_args(argv)
    root = repo_root()
    if args.status:
        return cmd_status(root)
    if args.remove:
        return cmd_remove(root)
    return cmd_install(root)


if __name__ == "__main__":
    sys.exit(main())
