"""Provenance-only helpers for the Matrix Scroll MCP server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from .gate import (
    DEFAULT_NOTES_REF,
    export_envelope_bundle,
    publish_envelopes_to_notes,
    verify_commit_envelope_for_sha,
    verify_envelope_range,
)
from .git import (
    build_commit_envelope,
    envelope_path as envelope_file_path,
    hook_status,
    repo_root,
    save_envelope,
    sign_commit_envelope,
    _run_git,
)
from .guac_export import export_guac_jsonl
from .policy import VerifyPolicy


def _resolve_root(workspace: str | None) -> Path:
    if workspace:
        path = Path(workspace).expanduser().resolve()
        if path.is_dir():
            return path
        raise ValueError(f"workspace not found: {workspace}")
    return repo_root()


def _load_policy(
    *,
    require_mode: str | None = None,
    trusted_keys_file: str | None = None,
    require_actor_types: list[str] | None = None,
    deny_actor_types: list[str] | None = None,
) -> VerifyPolicy | None:
    policy = VerifyPolicy(
        require_mode=require_mode or None,
        require_actor_types=set(require_actor_types) if require_actor_types else None,
        deny_actor_types=set(deny_actor_types) if deny_actor_types else None,
    )
    if trusted_keys_file:
        file_policy = VerifyPolicy.from_json_file(trusted_keys_file)
        policy.trusted_public_keys = file_policy.trusted_public_keys
        if file_policy.require_mode and not policy.require_mode:
            policy.require_mode = file_policy.require_mode
    return None if policy.is_empty() else policy


def create_envelope(
    workspace: str = "",
    *,
    commit_sha: str = "",
    actor_type: str = "",
    tool: str = "",
    agent_scope: str = "",
    sign: bool = True,
    save: bool = True,
) -> dict[str, Any]:
    """Build (and optionally sign/save) a commit envelope for the active repo."""
    root = _resolve_root(workspace or None)
    resolved_sha = commit_sha
    if resolved_sha:
        resolved_sha = _run_git("rev-parse", resolved_sha, cwd=root)
    envelope = build_commit_envelope(
        commit_sha=resolved_sha or None,
        root=root,
    )
    if actor_type:
        envelope.setdefault("provenance", {})["actor_type"] = actor_type
    if tool:
        envelope.setdefault("provenance", {})["tool"] = tool
    if agent_scope:
        envelope.setdefault("provenance", {})["agent_scope"] = agent_scope

    if sign:
        envelope = sign_commit_envelope(envelope)

    path: str | None = None
    if save and sign:
        saved = save_envelope(envelope, root)
        path = str(saved)

    commit = envelope.get("commit") or {}
    commit_id = commit.get("actual_id") or commit.get("expected_id")
    return {
        "ok": True,
        "commit_id": commit_id,
        "signed": sign,
        "saved": bool(path),
        "path": path,
        "envelope": envelope,
    }


def verify_envelope(
    workspace: str = "",
    *,
    commit_sha: str = "",
    envelope_path: str = "",
    require_mode: str = "",
    trusted_keys_file: str = "",
    require_actor_types: list[str] | None = None,
    deny_actor_types: list[str] | None = None,
) -> dict[str, Any]:
    """Verify one signed commit envelope by SHA or explicit JSON path."""
    root = _resolve_root(workspace or None)
    policy = _load_policy(
        require_mode=require_mode or None,
        trusted_keys_file=trusted_keys_file or None,
        require_actor_types=require_actor_types,
        deny_actor_types=deny_actor_types,
    )

    if envelope_path:
        path = Path(envelope_path).expanduser()
        if not path.is_file():
            path = root / envelope_path
        if not path.is_file():
            return {"ok": False, "error": f"envelope file not found: {envelope_path}"}
        envelope = json.loads(path.read_text(encoding="utf-8-sig"))
        sha = commit_sha or (envelope.get("commit") or {}).get("actual_id") or ""
    else:
        if not commit_sha:
            return {"ok": False, "error": "commit_sha or envelope_path is required"}
        sha = _run_git("rev-parse", commit_sha, cwd=root)
        path = envelope_file_path(sha, root)
        if not path.is_file():
            return {"ok": False, "error": f"no envelope for {sha}", "sha": sha}
        envelope = json.loads(path.read_text(encoding="utf-8-sig"))

    result = verify_commit_envelope_for_sha(envelope, sha, policy, root=root)
    return {"ok": result.ok, "sha": sha, **result.to_dict()}


def verify_pr_range(
    workspace: str = "",
    *,
    base: str = "origin/main",
    head: str = "HEAD",
    source: Literal["local", "notes", "bundle"] = "notes",
    notes_ref: str = DEFAULT_NOTES_REF,
    bundle_dir: str = "",
    require_mode: str = "",
    trusted_keys_file: str = "",
    require_actor_types: list[str] | None = None,
    deny_actor_types: list[str] | None = None,
) -> dict[str, Any]:
    """Scroll Gate: verify every commit in base..head."""
    root = _resolve_root(workspace or None)
    policy = _load_policy(
        require_mode=require_mode or None,
        trusted_keys_file=trusted_keys_file or None,
        require_actor_types=require_actor_types,
        deny_actor_types=deny_actor_types,
    )
    bundle = Path(bundle_dir).expanduser().resolve() if bundle_dir else None
    return verify_envelope_range(
        base,
        head,
        source=source,
        root=root,
        notes_ref=notes_ref,
        bundle_dir=bundle,
        policy=policy,
    )


def publish_notes(
    workspace: str = "",
    *,
    base: str = "origin/main",
    head: str = "HEAD",
    notes_ref: str = DEFAULT_NOTES_REF,
) -> dict[str, Any]:
    """Publish local signed envelopes to refs/notes/matrixscroll."""
    root = _resolve_root(workspace or None)
    return publish_envelopes_to_notes(base, head, root=root, notes_ref=notes_ref)


def status(workspace: str = "") -> dict[str, Any]:
    """Return hook install state, envelope count, and repo config."""
    root = _resolve_root(workspace or None)
    return hook_status(root)


def audit_export(
    workspace: str = "",
    *,
    base: str = "origin/main",
    head: str = "HEAD",
    output_dir: str = ".matrixscroll/audit-export",
    include_guac: bool = True,
) -> dict[str, Any]:
    """Export envelope bundle (+ optional GUAC JSONL) for audit evidence packs."""
    root = _resolve_root(workspace or None)
    out = Path(output_dir).expanduser()
    if not out.is_absolute():
        out = root / out
    bundle = export_envelope_bundle(base, head, out, root=root)
    result: dict[str, Any] = {"bundle": bundle}
    if include_guac:
        guac_path = out / "guac-ingest.jsonl"
        guac = export_guac_jsonl(out, guac_path, root=root)
        result["guac"] = guac
    result["ok"] = bool(bundle.get("ok"))
    return result
