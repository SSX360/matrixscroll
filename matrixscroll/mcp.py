from __future__ import annotations

"""Matrix Scroll MCP server — provenance verbs only.

Install: ``pip install "matrixscroll[mcp]"``
Run: ``python -m matrixscroll.mcp``

Tools cover commit envelope production, Scroll Gate verification, notes
transport, and audit export. Workspace intelligence (analyze, brainstorm,
radar) lives in Digital Rain — not here.
"""

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from . import mcp_core as core

mcp = FastMCP("matrixscroll-mcp")


@mcp.tool()
def create_envelope(
    workspace: str = "",
    commit_sha: str = "",
    actor_type: str = "",
    tool: str = "",
    agent_scope: str = "",
    sign: bool = True,
    save: bool = True,
) -> dict[str, Any]:
    """Create a Matrix Scroll commit envelope for the current or specified commit.

    Parameters:
        workspace: Git repo root (defaults to detected repo).
        commit_sha: Existing commit to envelope (defaults to staged/next commit).
        actor_type: Provenance actor, e.g. agent, human, ci.
        tool: Producing tool name, e.g. cursor, claude-code.
        agent_scope: Optional bounded scope path/glob for agent commits.
        sign: Ed25519-sign the envelope (default True).
        save: Persist under .matrixscroll/envelopes (default True).
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
    workspace: str = "",
    commit_sha: str = "",
    envelope_path: str = "",
    require_mode: str = "",
    trusted_keys_file: str = "",
    require_actor_types: list[str] | None = None,
    deny_actor_types: list[str] | None = None,
) -> dict[str, Any]:
    """Verify one signed commit envelope offline.

    Parameters:
        workspace: Git repo root (defaults to detected repo).
        commit_sha: Commit SHA to verify (uses local envelope file).
        envelope_path: Optional explicit path to envelope JSON.
        require_mode: Policy require_mode, e.g. hardware or emulated.
        trusted_keys_file: JSON file with trusted_public_keys policy.
        require_actor_types: Allowed actor_type values.
        deny_actor_types: Denied actor_type values.
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
    workspace: str = "",
    base: str = "origin/main",
    head: str = "HEAD",
    source: Literal["local", "notes", "bundle"] = "notes",
    notes_ref: str = "refs/notes/matrixscroll",
    bundle_dir: str = "",
    require_mode: str = "",
    trusted_keys_file: str = "",
    require_actor_types: list[str] | None = None,
    deny_actor_types: list[str] | None = None,
) -> dict[str, Any]:
    """Scroll Gate: verify signed/unsigned commits across a PR commit range.

    Parameters:
        workspace: Git repo root (defaults to detected repo).
        base: Range start ref (exclusive), e.g. origin/main.
        head: Range end ref (inclusive), e.g. HEAD or PR head SHA.
        source: Envelope transport — local, notes, or bundle.
        notes_ref: Git notes ref when source=notes.
        bundle_dir: Bundle directory when source=bundle.
        require_mode: Policy require_mode filter.
        trusted_keys_file: Trusted keys JSON for signed/untrusted actor checks.
        require_actor_types: Require specific actor types.
        deny_actor_types: Fail on denied actor types.
    """
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


@mcp.tool()
def publish_notes(
    workspace: str = "",
    base: str = "origin/main",
    head: str = "HEAD",
    notes_ref: str = "refs/notes/matrixscroll",
) -> dict[str, Any]:
    """Publish local signed envelopes to git notes for CI Scroll Gate verification."""
    return core.publish_notes(workspace, base=base, head=head, notes_ref=notes_ref)


@mcp.tool()
def status(workspace: str = "") -> dict[str, Any]:
    """Report hook install state, local envelope count, and Matrix Scroll config."""
    return core.status(workspace)


@mcp.tool()
def audit_export(
    workspace: str = "",
    base: str = "origin/main",
    head: str = "HEAD",
    output_dir: str = ".matrixscroll/audit-export",
    include_guac: bool = True,
) -> dict[str, Any]:
    """Export audit evidence bundle (JSON envelopes + optional GUAC JSONL)."""
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


if __name__ == "__main__":
    main()
