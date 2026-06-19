"""Git integration for Matrix Scroll commit envelopes."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ._core import sign_manifest, verify_manifest

COMMIT_ENVELOPE_SCHEMA = "matrixscroll.commit_envelope.v1"


def _run_git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def repo_root() -> Path:
    return Path(_run_git("rev-parse", "--show-toplevel"))


def matrixscroll_dir(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / ".git" / "matrixscroll"


def load_config(root: Path | None = None) -> dict[str, Any]:
    path = matrixscroll_dir(root) / "config.json"
    if not path.is_file():
        return {"enforce": False, "actor_type": "human", "tool": "git-cli"}
    return json.loads(path.read_text(encoding="utf-8"))


def _git_identity(prefix: str) -> dict[str, str]:
    name = _run_git("config", f"{prefix}.name") if prefix else _run_git("config", "user.name")
    email = _run_git("config", f"{prefix}.email") if prefix else _run_git("config", "user.email")
    return {"name": name, "email": email, "date": str(int(time.time()))}


def _repository_info(root: Path) -> dict[str, str]:
    name = root.name
    remote = ""
    try:
        remote = _run_git("config", "--get", "remote.origin.url", cwd=root)
    except RuntimeError:
        pass
    branch = ""
    try:
        branch = _run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)
    except RuntimeError:
        pass
    info: dict[str, str] = {"name": name}
    if remote:
        info["remote_url"] = remote
    if branch:
        info["branch"] = branch
    return info


def compute_commit_id(
    *,
    tree: str,
    parents: list[str],
    author: dict[str, str],
    committer: dict[str, str],
    message: str,
) -> str:
    """Compute Git commit object SHA-1 without creating the commit."""
    lines = [f"tree {tree}"]
    for parent in parents:
        lines.append(f"parent {parent}")
    lines.append(f"author {author['name']} <{author['email']}> {author['date']}")
    lines.append(f"committer {committer['name']} <{committer['email']}> {committer['date']}")
    lines.append("")
    lines.append(message.rstrip("\n"))
    body = "\n".join(lines).encode("utf-8")
    header = f"commit {len(body)}\0".encode("ascii") + body
    return hashlib.sha1(header).hexdigest()


def build_commit_envelope(
    *,
    message: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build an unsigned commit envelope for the current staged state."""
    root = root or repo_root()
    tree = _run_git("write-tree", cwd=root)
    parents: list[str] = []
    try:
        head = _run_git("rev-parse", "HEAD", cwd=root)
        if head:
            parents = [head]
    except RuntimeError:
        pass
    author = _git_identity("user")
    committer = author
    msg = message
    if msg is None:
        msg_file = root / ".git" / "COMMIT_EDITMSG"
        if msg_file.is_file():
            msg = msg_file.read_text(encoding="utf-8")
        else:
            msg = _run_git("log", "-1", "--pretty=%B", cwd=root) if parents else ""
    msg = msg or ""
    expected_id = compute_commit_id(
        tree=tree,
        parents=parents,
        author=author,
        committer=committer,
        message=msg,
    )
    config = load_config(root)
    provenance = {
        "actor_type": os.environ.get("MATRIXSCROLL_ACTOR_TYPE", config.get("actor_type", "human")),
        "tool": os.environ.get("MATRIXSCROLL_TOOL", config.get("tool", "git-cli")),
    }
    tool_version = os.environ.get("MATRIXSCROLL_TOOL_VERSION", "")
    if tool_version:
        provenance["tool_version"] = tool_version
    agent_scope = os.environ.get("MATRIXSCROLL_AGENT_SCOPE", "")
    if agent_scope:
        provenance["agent_scope"] = agent_scope
    return {
        "schema": COMMIT_ENVELOPE_SCHEMA,
        "commit": {
            "expected_id": expected_id,
            "tree": tree,
            "parents": parents,
            "author": author,
            "committer": committer,
            "message": msg,
        },
        "provenance": provenance,
        "repository": _repository_info(root),
    }


def sign_commit_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    return sign_manifest(envelope)


def envelope_path(commit_id: str, root: Path | None = None) -> Path:
    root = root or repo_root()
    return matrixscroll_dir(root) / "envelopes" / f"{commit_id}.json"


def save_envelope(envelope: dict[str, Any], root: Path | None = None) -> Path:
    root = root or repo_root()
    ms_dir = matrixscroll_dir(root)
    (ms_dir / "envelopes").mkdir(parents=True, exist_ok=True)
    commit_id = envelope["commit"].get("expected_id") or envelope["commit"].get("actual_id")
    if not commit_id:
        raise ValueError("envelope missing commit id")
    path = envelope_path(commit_id, root)
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def hook_pre_commit() -> int:
    root = repo_root()
    envelope = build_commit_envelope(root=root)
    signed = sign_commit_envelope(envelope)
    path = save_envelope(signed, root)
    print(json.dumps({"ok": True, "envelope": str(path), "expected_id": signed["commit"]["expected_id"]}))
    return 0


def hook_pre_push(_remote: str = "", _url: str = "") -> int:
    root = repo_root()
    ms_dir = matrixscroll_dir(root)
    env_dir = ms_dir / "envelopes"
    if not env_dir.is_dir():
        print(json.dumps({"ok": True, "verified": 0, "note": "no envelopes directory"}))
        return 0
    failures: list[str] = []
    verified = 0
    for path in sorted(env_dir.glob("*.json")):
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if verify_manifest(envelope):
            verified += 1
        else:
            failures.append(path.name)
    if failures:
        print(json.dumps({"ok": False, "verified": verified, "failures": failures}))
        return 2
    print(json.dumps({"ok": True, "verified": verified}))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python -m matrixscroll.git hook <pre-commit|pre-push>", file=sys.stderr)
        return 1
    if args[0] != "hook":
        print("usage: python -m matrixscroll.git hook <pre-commit|pre-push>", file=sys.stderr)
        return 1
    if len(args) < 2:
        return 1
    if args[1] == "pre-commit":
        return hook_pre_commit()
    if args[1] == "pre-push":
        remote = args[2] if len(args) > 2 else ""
        url = args[3] if len(args) > 3 else ""
        return hook_pre_push(remote, url)
    return 1


if __name__ == "__main__":
    sys.exit(main())
