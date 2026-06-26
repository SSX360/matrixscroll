"""PR provenance gate: export, transport, and range verification of commit envelopes."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .git import (
    COMMIT_ENVELOPE_SCHEMA,
    _repository_info,
    _run_git,
    envelope_path,
    repo_root,
)
from .manifest import verify_manifest
from .policy import (
    VerifyPolicy,
    verify_envelope_attribution_policy,
    verify_manifest_with_policy,
)

DEFAULT_NOTES_REF = "refs/notes/matrixscroll"
BUNDLE_INDEX = "index.json"


@dataclass
class EnvelopeVerifyResult:
    ok: bool
    sha: str
    device_id: str | None = None
    mode: str | None = None
    actor_type: str | None = None
    tool: str | None = None
    tool_version: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


def _resolve_manifest_path(uri: str, root: Path) -> Path:
    path = Path(uri)
    if path.is_file():
        return path
    candidate = root / uri
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"manifest not found: {uri}")


def _verify_linked_manifest(path: Path) -> tuple[bool, str | None]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return False, f"cannot read linked manifest: {exc}"
    if not verify_manifest(manifest):
        return False, "linked manifest failed cryptographic verification"
    return True, None


def _verify_delegation_block(
    envelope: dict[str, Any],
    root: Path,
) -> tuple[bool, str | None]:
    delegation = envelope.get("delegation")
    if not isinstance(delegation, dict):
        return True, None

    uri = delegation.get("delegation_manifest_uri")
    if uri:
        try:
            path = _resolve_manifest_path(uri, root)
        except FileNotFoundError as exc:
            return False, str(exc)
        ok, reason = _verify_linked_manifest(path)
        if not ok:
            return False, reason or "delegation manifest invalid"

        expected_hash = delegation.get("delegation_manifest_sha256")
        if expected_hash:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected_hash:
                return False, "delegation manifest sha256 mismatch"

    if not delegation.get("owner_id"):
        return False, "delegation block missing owner_id"

    return True, None


def verify_commit_envelope_for_sha(
    envelope: dict[str, Any],
    sha: str,
    policy: VerifyPolicy | None = None,
    *,
    root: Path | None = None,
) -> EnvelopeVerifyResult:
    """Verify a signed commit envelope is cryptographically valid and bound to *sha*."""
    root = root or repo_root()
    commit = envelope.get("commit") or {}
    actual_id = commit.get("actual_id")
    if actual_id != sha:
        return EnvelopeVerifyResult(
            ok=False,
            sha=sha,
            error=f"commit id mismatch: envelope has {actual_id!r}, expected {sha!r}",
        )

    ok, reason = verify_manifest_with_policy(envelope, policy)
    if not ok:
        return EnvelopeVerifyResult(ok=False, sha=sha, error=reason or "verification failed")

    ok, reason = verify_envelope_attribution_policy(envelope, policy)
    if not ok:
        return EnvelopeVerifyResult(ok=False, sha=sha, error=reason or "attribution policy failed")

    ok, reason = _verify_delegation_block(envelope, root)
    if not ok:
        return EnvelopeVerifyResult(ok=False, sha=sha, error=reason or "delegation invalid")

    provenance = envelope.get("provenance") or {}
    policy = policy or VerifyPolicy()
    if policy.verify_agent_scope or provenance.get("agent_scope"):
        scope_uri = provenance.get("agent_scope")
        if not scope_uri:
            if policy.verify_agent_scope:
                return EnvelopeVerifyResult(
                    ok=False, sha=sha, error="agent_scope verification required but missing"
                )
        else:
            try:
                path = _resolve_manifest_path(scope_uri, root)
            except FileNotFoundError as exc:
                return EnvelopeVerifyResult(ok=False, sha=sha, error=str(exc))
            ok, reason = _verify_linked_manifest(path)
            if not ok:
                return EnvelopeVerifyResult(
                    ok=False, sha=sha, error=reason or "agent_scope manifest invalid"
                )

    block = envelope.get("signature") or {}
    return EnvelopeVerifyResult(
        ok=True,
        sha=sha,
        device_id=block.get("device_id"),
        mode=block.get("mode"),
        actor_type=provenance.get("actor_type"),
        tool=provenance.get("tool"),
        tool_version=provenance.get("tool_version"),
    )


def commits_in_range(
    base: str,
    head: str,
    *,
    root: Path | None = None,
) -> list[str]:
    """Return commit SHAs in ``base..head`` in reverse chronological order."""
    root = root or repo_root()
    rev_range = f"{base}..{head}" if base else head
    out = _run_git("rev-list", rev_range, cwd=root)
    if not out:
        return []
    return out.splitlines()


def _load_envelope_from_path(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_envelope_for_sha(
    sha: str,
    *,
    source: Literal["local", "notes", "bundle"],
    root: Path | None = None,
    notes_ref: str = DEFAULT_NOTES_REF,
    bundle_dir: Path | None = None,
) -> dict[str, Any] | None:
    root = root or repo_root()
    if source == "local":
        path = envelope_path(sha, root)
        if not path.is_file():
            return None
        return _load_envelope_from_path(path)
    if source == "notes":
        try:
            raw = _run_git("notes", "--ref", notes_ref, "show", sha, cwd=root)
        except RuntimeError:
            return None
        if not raw:
            return None
        return json.loads(raw)
    if source == "bundle":
        if bundle_dir is None:
            raise ValueError("bundle_dir required when source is bundle")
        path = bundle_dir / f"{sha}.json"
        if not path.is_file():
            return None
        return _load_envelope_from_path(path)
    raise ValueError(f"unknown source: {source!r}")


def export_envelope_bundle(
    base: str,
    head: str,
    output: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Copy local envelopes for commits in ``base..head`` into a deterministic bundle."""
    root = root or repo_root()
    shas = commits_in_range(base, head, root=root)
    output.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    missing: list[str] = []
    for sha in shas:
        src = envelope_path(sha, root)
        if not src.is_file():
            missing.append(sha)
            continue
        dst = output / f"{sha}.json"
        shutil.copy2(src, dst)
        exported.append(sha)

    index = {
        "schema": "matrixscroll.envelope_bundle.v1",
        "repository": _repository_info(root),
        "base": base,
        "head": head,
        "commits": exported,
        "missing": missing,
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (output / BUNDLE_INDEX).write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "output": str(output),
        "exported": len(exported),
        "missing": missing,
        "index": str(output / BUNDLE_INDEX),
    }


def publish_envelopes_to_notes(
    base: str,
    head: str,
    *,
    root: Path | None = None,
    notes_ref: str = DEFAULT_NOTES_REF,
) -> dict[str, Any]:
    """Attach local signed envelopes to commits via git notes."""
    root = root or repo_root()
    shas = commits_in_range(base, head, root=root)
    published: list[str] = []
    missing: list[str] = []
    for sha in shas:
        src = envelope_path(sha, root)
        if not src.is_file():
            missing.append(sha)
            continue
        envelope_json = src.read_text(encoding="utf-8")
        _run_git(
            "notes",
            "--ref",
            notes_ref,
            "add",
            "-f",
            "-m",
            envelope_json,
            sha,
            cwd=root,
        )
        published.append(sha)

    return {
        "ok": True,
        "notes_ref": notes_ref,
        "published": len(published),
        "missing": missing,
        "commits": published,
    }


def publish_push_envelopes_to_notes(
    stdin_text: str,
    *,
    root: Path | None = None,
    notes_ref: str = DEFAULT_NOTES_REF,
) -> dict[str, Any]:
    """Publish envelopes for all commits in a pre-push stdin payload."""
    root = root or repo_root()
    published_total = 0
    missing: list[str] = []
    for line in stdin_text.splitlines():
        parts = line.strip().split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, _remote_ref, remote_sha = parts
        if local_sha == "0" * 40:
            continue
        base = "" if remote_sha == "0" * 40 else remote_sha
        result = publish_envelopes_to_notes(base, local_sha, root=root, notes_ref=notes_ref)
        published_total += result["published"]
        missing.extend(result["missing"])
    return {"ok": True, "published": published_total, "missing": missing}


def fetch_notes(
    remote: str = "origin",
    *,
    root: Path | None = None,
    notes_ref: str = DEFAULT_NOTES_REF,
) -> dict[str, Any]:
    """Fetch notes ref from a remote."""
    root = root or repo_root()
    _run_git("fetch", remote, f"{notes_ref}:{notes_ref}", cwd=root)
    return {"ok": True, "remote": remote, "notes_ref": notes_ref}


def format_range_summary(summary: dict[str, Any]) -> str:
    """Render a human-readable Markdown summary for CI step output."""
    status = "passed" if summary.get("ok") else "failed"
    lines = [
        "## Matrix Scroll provenance gate",
        "",
        f"**Status:** {status}",
        f"**Commits verified:** {summary.get('verified_count', 0)} / {summary.get('total', 0)}",
        f"**Agent commits:** {summary.get('agent_count', 0)}",
        f"**Human commits:** {summary.get('human_count', 0)}",
        f"**Modes:** {', '.join(summary.get('modes') or []) or 'none'}",
        "",
    ]
    failures = [r for r in summary.get("results", []) if not r.get("ok")]
    if failures:
        lines.append("### Failures")
        lines.append("")
        for row in failures[:20]:
            lines.append(f"- `{row.get('sha', '')[:8]}`: {row.get('error', 'unknown')}")
    return "\n".join(lines) + "\n"


def verify_envelope_range(
    base: str,
    head: str,
    *,
    source: Literal["local", "notes", "bundle"] = "local",
    root: Path | None = None,
    notes_ref: str = DEFAULT_NOTES_REF,
    bundle_dir: Path | None = None,
    policy: VerifyPolicy | None = None,
) -> dict[str, Any]:
    """Verify every commit in ``base..head`` has a valid envelope from *source*."""
    root = root or repo_root()
    shas = commits_in_range(base, head, root=root)
    if not shas:
        return {
            "ok": True,
            "base": base,
            "head": head,
            "source": source,
            "total": 0,
            "verified_count": 0,
            "agent_count": 0,
            "human_count": 0,
            "modes": [],
            "note": "no commits in range",
            "results": [],
        }

    results: list[EnvelopeVerifyResult] = []
    for sha in shas:
        envelope = _load_envelope_for_sha(
            sha,
            source=source,
            root=root,
            notes_ref=notes_ref,
            bundle_dir=bundle_dir,
        )
        if envelope is None:
            results.append(
                EnvelopeVerifyResult(ok=False, sha=sha, error="missing envelope")
            )
            continue
        if envelope.get("schema") != COMMIT_ENVELOPE_SCHEMA:
            results.append(
                EnvelopeVerifyResult(
                    ok=False,
                    sha=sha,
                    error=f"unexpected schema {envelope.get('schema')!r}",
                )
            )
            continue
        results.append(
            verify_commit_envelope_for_sha(envelope, sha, policy, root=root)
        )

    ok_count = sum(1 for r in results if r.ok)
    agent_count = sum(1 for r in results if r.ok and r.actor_type == "agent")
    human_count = sum(1 for r in results if r.ok and r.actor_type == "human")
    modes = sorted({r.mode for r in results if r.ok and r.mode})
    all_ok = ok_count == len(shas)

    return {
        "ok": all_ok,
        "base": base,
        "head": head,
        "source": source,
        "total": len(shas),
        "verified_count": ok_count,
        "agent_count": agent_count,
        "human_count": human_count,
        "modes": modes,
        "results": [r.to_dict() for r in results],
    }
