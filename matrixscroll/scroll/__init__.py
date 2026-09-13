"""SSX360 Scroll — Git wrapper with mandatory provenance (Phase 2 stub).

Today: use ``matrixscroll hook-install`` and ``git commit`` directly.
Future: ``scroll commit`` will wrap git commit + auto-envelope signing.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def commit(
    message: str,
    *,
    actor_type: str = "human",
    tool: str = "scroll",
    allow_empty: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Run ``git commit`` then sign the resulting commit envelope.

    Phase 1 thin wrapper: delegates to git + existing Matrix Scroll hooks/envelope
    builders. Does not replace Git.
    """
    import os

    from .. import git as git_mod

    root = repo_root or Path.cwd()
    prev_actor = os.environ.get("MATRIXSCROLL_ACTOR_TYPE")
    prev_tool = os.environ.get("MATRIXSCROLL_TOOL")
    os.environ["MATRIXSCROLL_ACTOR_TYPE"] = actor_type
    os.environ["MATRIXSCROLL_TOOL"] = tool
    cmd = ["git", "commit", "-m", message]
    if allow_empty:
        cmd.insert(2, "--allow-empty")
    try:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        if proc.returncode != 0:
            return {
                "ok": False,
                "error": "git_commit_failed",
                "stderr": proc.stderr.strip(),
            }

        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        envelope = git_mod.build_commit_envelope(commit_sha=sha, root=root)
    finally:
        if prev_actor is None:
            os.environ.pop("MATRIXSCROLL_ACTOR_TYPE", None)
        else:
            os.environ["MATRIXSCROLL_ACTOR_TYPE"] = prev_actor
        if prev_tool is None:
            os.environ.pop("MATRIXSCROLL_TOOL", None)
        else:
            os.environ["MATRIXSCROLL_TOOL"] = prev_tool
    signed = git_mod.sign_commit_envelope(envelope)
    path = git_mod.save_envelope(signed, root)
    return {"ok": True, "sha": sha, "envelope_path": str(path), "envelope": signed}


def main(argv: list[str] | None = None) -> int:
    """Minimal ``scroll commit -m`` entrypoint for early adopters."""
    import argparse

    parser = argparse.ArgumentParser(prog="scroll", description="SSX360 Scroll — Git + provenance wrapper")
    sub = parser.add_subparsers(dest="command")
    commit_p = sub.add_parser("commit", help="git commit + auto-envelope (Phase 1 wrapper)")
    commit_p.add_argument("-m", "--message", required=True)
    commit_p.add_argument("--actor-type", default="human", choices=["human", "agent", "ci"])
    commit_p.add_argument("--tool", default="scroll")
    commit_p.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args(argv)
    if args.command != "commit":
        parser.print_help()
        return 1
    result = commit(
        args.message,
        actor_type=args.actor_type,
        tool=args.tool,
        allow_empty=args.allow_empty,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
