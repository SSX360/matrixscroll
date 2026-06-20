"""Git integration for Matrix Scroll commit envelopes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .manifest import sign_manifest, verify_manifest

COMMIT_ENVELOPE_SCHEMA = "matrixscroll.commit_envelope.v1"
HOOK_MARKER = "# matrixscroll-git hook\n"
DEFAULT_CONFIG = {"enforce": False, "actor_type": "human", "tool": "git-cli"}


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


def hooks_template_dir() -> Path:
    return Path(__file__).resolve().parent / "hooks"


def load_config(root: Path | None = None) -> dict[str, Any]:
    path = matrixscroll_dir(root) / "config.json"
    if not path.is_file():
        return dict(DEFAULT_CONFIG)
    return json.loads(path.read_text(encoding="utf-8"))


def _git_date(timestamp: int | None = None) -> str:
    ts = int(timestamp if timestamp is not None else time.time())
    if time.daylight and time.localtime(ts).tm_isdst:
        offset_seconds = -time.altzone
    else:
        offset_seconds = -time.timezone
    sign = "+" if offset_seconds >= 0 else "-"
    offset_seconds = abs(offset_seconds)
    hours, remainder = divmod(offset_seconds, 3600)
    minutes = remainder // 60
    return f"{ts} {sign}{hours:02d}{minutes:02d}"


def _git_identity() -> dict[str, str]:
    return {
        "name": _run_git("config", "user.name"),
        "email": _run_git("config", "user.email"),
        "date": _git_date(),
    }


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
    return hashlib.sha1(header, usedforsecurity=False).hexdigest()


def parse_commit(sha: str, root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    fmt = "%H%x00%T%x00%P%x00%an%x00%ae%x00%at%x00%cn%x00%ce%x00%ct%x00%B"
    parts = _run_git("show", "-s", f"--format={fmt}", sha, cwd=root).split("\0")
    if len(parts) < 10:
        raise RuntimeError(f"unexpected git show output for {sha}")
    commit_sha, tree, parents_raw, an, ae, at, cn, ce, ct, body = parts[:10]
    parents = [p for p in parents_raw.split() if p]
    author = {"name": an, "email": ae, "date": _git_date(int(at))}
    committer = {"name": cn, "email": ce, "date": _git_date(int(ct))}
    actual_id = compute_commit_id(
        tree=tree,
        parents=parents,
        author=author,
        committer=committer,
        message=body,
    )
    if actual_id != commit_sha:
        raise RuntimeError(f"commit id mismatch for {sha}")
    return {
        "actual_id": commit_sha,
        "tree": tree,
        "parents": parents,
        "author": author,
        "committer": committer,
        "message": body,
    }


def build_commit_envelope(
    *,
    message: str | None = None,
    commit_sha: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build an unsigned commit envelope for staged state or an existing commit."""
    root = root or repo_root()
    if commit_sha:
        commit = parse_commit(commit_sha, root)
        commit_block = {
            "actual_id": commit["actual_id"],
            "tree": commit["tree"],
            "parents": commit["parents"],
            "author": commit["author"],
            "committer": commit["committer"],
            "message": commit["message"],
        }
    else:
        tree = _run_git("write-tree", cwd=root)
        parents: list[str] = []
        try:
            head = _run_git("rev-parse", "HEAD", cwd=root)
            if head:
                parents = [head]
        except RuntimeError:
            pass
        author = _git_identity()
        committer = dict(author)
        msg = message
        if msg is None:
            msg_file = root / ".git" / "COMMIT_EDITMSG"
            if msg_file.is_file():
                msg = msg_file.read_text(encoding="utf-8")
            else:
                msg = _run_git("log", "-1", "--pretty=%B", cwd=root) if parents else ""
        msg = msg or ""
        commit_block = {
            "expected_id": compute_commit_id(
                tree=tree,
                parents=parents,
                author=author,
                committer=committer,
                message=msg,
            ),
            "tree": tree,
            "parents": parents,
            "author": author,
            "committer": committer,
            "message": msg,
        }

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
        "commit": commit_block,
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
    commit = envelope["commit"]
    commit_id = commit.get("actual_id") or commit.get("expected_id")
    if not commit_id:
        raise ValueError("envelope missing commit id")
    path = envelope_path(commit_id, root)
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _commits_being_pushed(stdin_text: str) -> list[str]:
    commits: list[str] = []
    for line in stdin_text.splitlines():
        parts = line.strip().split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, _remote_ref, remote_sha = parts
        if local_sha == "0" * 40:
            continue
        if remote_sha == "0" * 40:
            cmd = ["git", "rev-list", local_sha]
        else:
            cmd = ["git", "rev-list", f"{remote_sha}..{local_sha}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            commits.extend([c for c in result.stdout.splitlines() if c])
    return commits


def install_hooks(root: Path | None = None, *, remove: bool = False) -> dict[str, Any]:
    root = root or repo_root()
    hooks = root / ".git" / "hooks"
    if not hooks.is_dir():
        raise RuntimeError(".git/hooks not found")
    names = ("post-commit", "pre-push")
    if remove:
        for name in names:
            dst = hooks / name
            if dst.is_file() and HOOK_MARKER in dst.read_text(encoding="utf-8"):
                backup = dst.with_suffix(dst.suffix + ".matrixscroll.bak")
                if backup.exists():
                    shutil.copy2(backup, dst)
                    backup.unlink()
                else:
                    dst.unlink()
        return {"ok": True, "removed": list(names)}

    for name in names:
        src = hooks_template_dir() / name
        dst = hooks / name
        content = src.read_text(encoding="utf-8")
        if dst.exists():
            existing = dst.read_text(encoding="utf-8")
            if HOOK_MARKER in existing:
                continue
            backup = dst.with_suffix(dst.suffix + ".matrixscroll.bak")
            shutil.copy2(dst, backup)
        dst.write_text(content, encoding="utf-8")
        try:
            os.chmod(dst, 0o755)
        except OSError:
            pass

    ms_dir = matrixscroll_dir(root)
    ms_dir.mkdir(parents=True, exist_ok=True)
    (ms_dir / "envelopes").mkdir(exist_ok=True)
    config_path = ms_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "installed": list(names), "root": str(root)}


def hook_status(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    hooks = root / ".git" / "hooks"
    installed = {}
    for name in ("post-commit", "pre-push"):
        path = hooks / name
        installed[name] = path.is_file() and HOOK_MARKER in path.read_text(encoding="utf-8")
    ms_dir = matrixscroll_dir(root)
    envelope_count = len(list((ms_dir / "envelopes").glob("*.json"))) if (ms_dir / "envelopes").is_dir() else 0
    config = load_config(root)
    return {
        "ok": True,
        "root": str(root),
        "hooks": installed,
        "envelope_count": envelope_count,
        "config": config,
    }


def hook_post_commit() -> int:
    try:
        root = repo_root()
        sha = _run_git("rev-parse", "HEAD", cwd=root)
        envelope = build_commit_envelope(commit_sha=sha, root=root)
        signed = sign_commit_envelope(envelope)
        path = save_envelope(signed, root)
        print(json.dumps({"ok": True, "envelope": str(path), "actual_id": sha}))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


def hook_pre_push(stdin_text: str = "") -> int:
    try:
        root = repo_root()
        commits = _commits_being_pushed(stdin_text)
        if not commits:
            print(json.dumps({"ok": True, "verified": 0, "note": "no commits to push"}))
            return 0
        failures: list[str] = []
        verified = 0
        for sha in commits:
            path = envelope_path(sha, root)
            if not path.is_file():
                failures.append(f"missing:{sha}")
                continue
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
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) >= 2 and args[0] == "hook":
        if args[1] == "post-commit":
            return hook_post_commit()
        if args[1] == "pre-push":
            stdin_text = sys.stdin.read()
            return hook_pre_push(stdin_text)
    print("usage: python -m matrixscroll.git hook <post-commit|pre-push>", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
