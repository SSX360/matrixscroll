from __future__ import annotations

"""Matrix Scroll MCP server — provenance verbs only.

Install: ``pip install "matrixscroll[mcp]"``
Run: ``python -m matrixscroll.mcp``

Tools cover commit envelope production, Scroll Gate verification, notes
transport, and audit export. All verification is offline and read-only except
where noted (``create_envelope``, ``publish_notes``, ``audit_export`` write
local files or git notes).
"""

from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from . import mcp_core as core
from .cloud.client import CloudAuthError, audit_export as cloud_audit_export
from .cloud.client import list_envelopes as cloud_list_envelopes
from .cloud.client import verify_range as cloud_verify_range

SIGNUP_URL = "https://ssx360.com/signup"
DOCS_URL = "https://ssx360.com/docs"


def _require_api_key(feature: str) -> dict[str, Any] | None:
    """Return structured auth error payload when SSX360_API_KEY is unset."""
    import os

    if os.environ.get("SSX360_API_KEY", "").strip():
        return None
    return {
        "ok": False,
        "error": "api_key_required",
        "message": (
            f"{feature} requires SSX360_API_KEY. "
            "Community tier includes 100 CI verifications/day. "
            f"Get a key at {SIGNUP_URL}"
        ),
        "signup_url": SIGNUP_URL,
        "docs_url": DOCS_URL,
    }


def _cloud_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, CloudAuthError):
        return {"ok": False, **exc.payload}
    return {"ok": False, "error": "cloud_error", "message": str(exc)}

mcp = FastMCP(
    "matrixscroll-mcp",
    instructions=(
        "Matrix Scroll MCP exposes provenance verbs only: create and verify "
        "Ed25519 commit envelopes, run Scroll Gate over PR ranges, publish git "
        "notes, and export audit bundles. Prefer ``status`` first in a new repo. "
        "Verification tools are read-only; ``create_envelope``, ``publish_notes``, "
        "and ``audit_export`` write local artifacts."
    ),
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "commit-envelope.v1.json"
_SPEC_PATH = _REPO_ROOT / "SPEC.md"


@mcp.resource("matrixscroll://schema/commit-envelope.v1")
def commit_envelope_schema() -> str:
    """Public JSON Schema for Matrix Scroll commit envelopes (v1)."""
    if _SCHEMA_PATH.is_file():
        return _SCHEMA_PATH.read_text(encoding="utf-8")
    return '{"error":"commit-envelope.v1.json not found in install root"}'


@mcp.resource("matrixscroll://spec")
def specification() -> str:
    """Matrix Scroll byte contract and verification rules (SPEC.md)."""
    if _SPEC_PATH.is_file():
        return _SPEC_PATH.read_text(encoding="utf-8")
    return "SPEC.md not found in install root."


@mcp.prompt()
def provenance_report(repo_path: str = ".") -> str:
    """Guide an agent to produce a provenance audit report for a Git repository."""
    return (
        f"Using Matrix Scroll MCP tools, inspect the repository at {repo_path!r}:\n"
        "1. Call ``status`` to confirm hooks and local envelope count.\n"
        "2. Call ``verify_pr_range`` with source=notes (or local if notes are missing).\n"
        "3. Call ``audit_export`` to write an evidence bundle under "
        "``.matrixscroll/audit-export``.\n"
        "4. Summarize signed vs unsigned commits, actor types, and any policy failures.\n"
        "Do not modify source code unless the user explicitly asks."
    )


@mcp.tool()
def create_envelope(
    workspace: Annotated[
        str,
        Field(
            description="Absolute or relative path to the Git repository root. "
            "Leave empty to auto-detect from the current working directory.",
        ),
    ] = "",
    commit_sha: Annotated[
        str,
        Field(
            description="Existing commit to envelope (full or short SHA). "
            "Empty uses the staged commit or HEAD depending on hook context.",
        ),
    ] = "",
    actor_type: Annotated[
        str,
        Field(
            description="Provenance actor label recorded in the envelope, e.g. agent, human, or ci.",
        ),
    ] = "",
    tool: Annotated[
        str,
        Field(
            description="Producing tool name recorded in provenance, e.g. cursor or claude-code.",
        ),
    ] = "",
    agent_scope: Annotated[
        str,
        Field(
            description="Optional path or glob limiting what an agent commit claims to touch.",
        ),
    ] = "",
    sign: Annotated[
        bool,
        Field(
            description="When true (default), Ed25519-sign the envelope with the active key store.",
        ),
    ] = True,
    save: Annotated[
        bool,
        Field(
            description="When true (default), persist the envelope under .matrixscroll/envelopes/.",
        ),
    ] = True,
) -> dict[str, Any]:
    """Create a signed commit envelope for the current or specified commit.

    Side effects: may write ``.matrixscroll/envelopes/<sha>.json`` when ``save`` is true.
    Returns envelope metadata including ``ok``, ``sha``, and envelope fields on success.
    """
    return core.create_envelope(
        workspace,
        commit_sha=commit_sha,
        actor_type=actor_type,
        tool=tool,
        agent_scope=agent_scope,
        sign=sign,
        save=save,
    )


@mcp.tool()
def verify_envelope(
    workspace: Annotated[
        str,
        Field(
            description="Git repository root. Empty auto-detects from the working directory.",
        ),
    ] = "",
    commit_sha: Annotated[
        str,
        Field(
            description="Commit SHA whose local envelope file should be verified offline.",
        ),
    ] = "",
    envelope_path: Annotated[
        str,
        Field(
            description="Optional explicit path to an envelope JSON file instead of the default "
            "``.matrixscroll/envelopes/<sha>.json`` location.",
        ),
    ] = "",
    require_mode: Annotated[
        str,
        Field(
            description="Policy filter on signature mode, e.g. emulated or hardware. "
            "Empty skips mode enforcement.",
        ),
    ] = "",
    trusted_keys_file: Annotated[
        str,
        Field(
            description="Path to a JSON policy file listing trusted Ed25519 public keys.",
        ),
    ] = "",
    require_actor_types: Annotated[
        list[str] | None,
        Field(
            description="If set, fail verification unless provenance.actor_type is in this list.",
        ),
    ] = None,
    deny_actor_types: Annotated[
        list[str] | None,
        Field(
            description="If set, fail verification when provenance.actor_type matches any denied value.",
        ),
    ] = None,
) -> dict[str, Any]:
    """Verify one signed commit envelope offline (read-only).

    Usage: provide ``commit_sha`` for the default on-disk envelope, or ``envelope_path``
    for an explicit JSON file. Apply ``require_mode`` and actor policy lists to enforce
    team trust rules.

    Returns ``{ok: bool, sha: str, ...}`` with verification details; ``ok`` false on
    signature, policy, or missing-envelope errors. No files are written.
    """
    return core.verify_envelope(
        workspace,
        commit_sha=commit_sha,
        envelope_path=envelope_path,
        require_mode=require_mode,
        trusted_keys_file=trusted_keys_file,
        require_actor_types=require_actor_types,
        deny_actor_types=deny_actor_types,
    )


@mcp.tool()
def verify_pr_range(
    workspace: Annotated[
        str,
        Field(description="Git repository root. Empty auto-detects from the working directory."),
    ] = "",
    base: Annotated[
        str,
        Field(description="Range start Git ref (exclusive), typically origin/main."),
    ] = "origin/main",
    head: Annotated[
        str,
        Field(description="Range end Git ref (inclusive), e.g. HEAD or a PR head SHA."),
    ] = "HEAD",
    source: Annotated[
        Literal["hosted", "local", "notes", "bundle"],
        Field(
            description="Envelope transport: hosted Scroll Gate (default, requires SSX360_API_KEY), "
            "local files, git notes, or bundle dir for offline verification.",
        ),
    ] = "hosted",
    notes_ref: Annotated[
        str,
        Field(description="Git notes ref when source=notes, default refs/notes/matrixscroll."),
    ] = "refs/notes/matrixscroll",
    bundle_dir: Annotated[
        str,
        Field(description="Directory containing exported envelope bundles when source=bundle."),
    ] = "",
    require_mode: Annotated[
        str,
        Field(description="Optional policy require_mode filter applied to every commit in the range."),
    ] = "",
    trusted_keys_file: Annotated[
        str,
        Field(description="Optional JSON file of trusted public keys for the range check."),
    ] = "",
    require_actor_types: Annotated[
        list[str] | None,
        Field(description="Optional allow-list of provenance.actor_type values."),
    ] = None,
    deny_actor_types: Annotated[
        list[str] | None,
        Field(description="Optional deny-list of provenance.actor_type values."),
    ] = None,
) -> dict[str, Any]:
    """Scroll Gate: verify signed/unsigned commits across a PR commit range.

    Hosted mode (default): calls ssx360.com with SSX360_API_KEY.
    Set source=local|notes|bundle to verify offline without an API key.
    """
    if source in ("local", "notes", "bundle"):
        return core.verify_pr_range(
            workspace,
            base=base,
            head=head,
            source=source,
            notes_ref=notes_ref,
            bundle_dir=bundle_dir,
            require_mode=require_mode,
            trusted_keys_file=trusted_keys_file,
            require_actor_types=require_actor_types,
            deny_actor_types=deny_actor_types,
        )

    auth_err = _require_api_key("verify_pr_range (hosted Scroll Gate)")
    if auth_err:
        return auth_err
    try:
        return cloud_verify_range(base=base, head=head)
    except Exception as exc:
        return _cloud_error(exc)


@mcp.tool()
def publish_notes(
    workspace: Annotated[
        str,
        Field(description="Git repository root. Empty auto-detects from the working directory."),
    ] = "",
    base: Annotated[
        str,
        Field(description="Range start ref (exclusive) for envelopes to publish."),
    ] = "origin/main",
    head: Annotated[
        str,
        Field(description="Range end ref (inclusive) for envelopes to publish."),
    ] = "HEAD",
    notes_ref: Annotated[
        str,
        Field(description="Git notes ref to write, default refs/notes/matrixscroll."),
    ] = "refs/notes/matrixscroll",
) -> dict[str, Any]:
    """Publish local signed envelopes to git notes for CI Scroll Gate verification.

    Side effects: updates the local git notes ref; push ``refs/notes/matrixscroll`` to remote separately.
    """
    return core.publish_notes(workspace, base=base, head=head, notes_ref=notes_ref)


@mcp.tool()
def status(workspace: Annotated[
    str,
    Field(description="Git repository root. Empty auto-detects from the working directory."),
] = "") -> dict[str, Any]:
    """Report hook install state, local envelope count, and Matrix Scroll config (read-only)."""
    return core.status(workspace)


@mcp.tool()
def audit_export(
    workspace: Annotated[
        str,
        Field(
            description="Git repository root. Empty auto-detects from the working directory.",
        ),
    ] = "",
    base: Annotated[
        str,
        Field(
            description="Range start Git ref (exclusive) for commits included in the export bundle.",
        ),
    ] = "origin/main",
    head: Annotated[
        str,
        Field(
            description="Range end Git ref (inclusive) for commits included in the export bundle.",
        ),
    ] = "HEAD",
    output_dir: Annotated[
        str,
        Field(
            description="Directory for exported JSON envelopes and optional GUAC JSONL. "
            "Relative paths resolve under the repository root.",
        ),
    ] = ".matrixscroll/audit-export",
    include_guac: Annotated[
        bool,
        Field(
            description="When true (default), also write guac-ingest.jsonl for supply-chain tooling.",
        ),
    ] = True,
) -> dict[str, Any]:
    """Export an audit evidence bundle for procurement or compliance review.

    Team+ hosted export uses SSX360_API_KEY and ssx360.com/api/v1/audit/export.
    Without a key, falls back to local envelope export under ``output_dir``.
    """
    auth_err = _require_api_key("audit_export (hosted)")
    if auth_err is None:
        try:
            return cloud_audit_export(format="json")
        except Exception as exc:
            return _cloud_error(exc)
    if auth_err.get("error") != "api_key_required":
        return auth_err
    return core.audit_export(
        workspace,
        base=base,
        head=head,
        output_dir=output_dir,
        include_guac=include_guac,
    )


def main() -> None:
    """Run the Matrix Scroll MCP server over stdio."""
    mcp.run(transport="stdio")


@mcp.tool()
def list_envelopes(
    limit: Annotated[
        int,
        Field(description="Maximum envelopes to return from the hosted platform (default 50)."),
    ] = 50,
) -> dict[str, Any]:
    """List commit envelopes stored on ssx360.com for the authenticated organization."""
    auth_err = _require_api_key("list_envelopes")
    if auth_err:
        return auth_err
    try:
        return cloud_list_envelopes(limit=limit)
    except Exception as exc:
        return _cloud_error(exc)


if __name__ == "__main__":
    main()
