from __future__ import annotations

# Path injection to allow relative imports in site-packages/install
import sys
from pathlib import Path
package_dir = Path(__file__).resolve().parent
if str(package_dir) not in sys.path:
    sys.path.append(str(package_dir))

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import git as _git
from . import gate as _gate
from ._core import status as _status

mcp = FastMCP("matrixscroll-mcp")


@mcp.tool()
def create_envelope(
    workspace: str,
    actor: str = "agent",
    tool: str = "matrixscroll-mcp",
    scope: str = "",
    message: str = "",
) -> dict[str, Any]:
    """Build, sign, and save a cryptographic commit envelope for staged changes or an existing commit in the workspace.

    This generates an Ed25519-signed commit envelope containing actor, tool, and optional scope details.

    Parameters:
        workspace (str): The absolute path to the local git repository workspace.
        actor (str, optional): The actor signing the commit. Defaults to "agent".
        tool (str, optional): The tool name creating the commit. Defaults to "matrixscroll-mcp".
        scope (str, optional): Optional context/scope identifier (e.g. prompt or issue key). Defaults to "".
        message (str, optional): Commit message override. Defaults to "".
    """
    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {workspace}")

    # Temporarily inject environment variables for the builder
    old_actor = os.environ.get("MATRIXSCROLL_ACTOR_TYPE")
    old_tool = os.environ.get("MATRIXSCROLL_TOOL")
    old_scope = os.environ.get("MATRIXSCROLL_AGENT_SCOPE")

    os.environ["MATRIXSCROLL_ACTOR_TYPE"] = actor
    os.environ["MATRIXSCROLL_TOOL"] = tool
    if scope:
        os.environ["MATRIXSCROLL_AGENT_SCOPE"] = scope
    elif "MATRIXSCROLL_AGENT_SCOPE" in os.environ:
        del os.environ["MATRIXSCROLL_AGENT_SCOPE"]

    try:
        envelope = _git.build_commit_envelope(message=message or None, root=root)
        signed = _git.sign_commit_envelope(envelope)
        saved_path = _git.save_envelope(signed, root)
        return {
            "ok": True,
            "path": str(saved_path),
            "envelope": signed,
        }
    finally:
        # Restore environment variables
        if old_actor is not None:
            os.environ["MATRIXSCROLL_ACTOR_TYPE"] = old_actor
        elif "MATRIXSCROLL_ACTOR_TYPE" in os.environ:
            del os.environ["MATRIXSCROLL_ACTOR_TYPE"]

        if old_tool is not None:
            os.environ["MATRIXSCROLL_TOOL"] = old_tool
        elif "MATRIXSCROLL_TOOL" in os.environ:
            del os.environ["MATRIXSCROLL_TOOL"]

        if old_scope is not None:
            os.environ["MATRIXSCROLL_AGENT_SCOPE"] = old_scope
        elif "MATRIXSCROLL_AGENT_SCOPE" in os.environ:
            del os.environ["MATRIXSCROLL_AGENT_SCOPE"]


@mcp.tool()
def verify_envelope(workspace: str, sha: str) -> dict[str, Any]:
    """Verify the cryptographic signature and integrity of a signed commit envelope for a specific commit SHA.

    Validates that the envelope is cryptographically sound and matches the commit hash in the git repository.

    Parameters:
        workspace (str): The absolute path to the local git repository workspace.
        sha (str): The 40-character commit hash to verify.
    """
    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {workspace}")

    envelope = _gate._load_envelope_for_sha(sha, source="local", root=root)
    if envelope is None:
        return {
            "ok": False,
            "sha": sha,
            "error": f"missing envelope for sha: {sha}",
        }

    res = _gate.verify_commit_envelope_for_sha(envelope, sha, root=root)
    return res.to_dict()


@mcp.tool()
def verify_pr_range(workspace: str, base: str, head: str, source: str = "local") -> dict[str, Any]:
    """Verify every commit envelope in a given PR or commit range (base..head).

    Ensures all commits in the range have valid envelopes matching policies.

    Parameters:
        workspace (str): The absolute path to the local git repository workspace.
        base (str): The base commit or ref (e.g. "main", "origin/main").
        head (str): The head commit or ref (e.g. "HEAD", branch name).
        source (str, optional): Envelope source. Must be "local" (default), "notes", or "bundle".
    """
    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {workspace}")

    if source not in ("local", "notes", "bundle"):
        raise ValueError(f"Invalid source: {source}. Must be local, notes, or bundle.")

    summary = _gate.verify_envelope_range(base, head, source=source, root=root)
    return summary


@mcp.tool()
def envelope_publish_notes(workspace: str, base: str, head: str) -> dict[str, Any]:
    """Publish local signed commit envelopes to git notes (refs/notes/matrixscroll) for a commit range.

    Makes local signed envelopes available for transport and range verification.

    Parameters:
        workspace (str): The absolute path to the local git repository workspace.
        base (str): The base commit or ref of the range.
        head (str): The head commit or ref of the range.
    """
    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {workspace}")

    return _gate.publish_envelopes_to_notes(base, head, root=root)


@mcp.tool()
def status(workspace: str = "") -> dict[str, Any]:
    """Retrieve the active cryptographic identity provider status, device ID, public key, and mode.

    Returns configuration and status details of the signing backend.

    Parameters:
        workspace (str, optional): The absolute path to the local git repository workspace. Defaults to "".
    """
    return _status()


@mcp.tool()
def audit_export(workspace: str, base: str, head: str, output: str) -> dict[str, Any]:
    """Export local commit envelopes for a given range in the workspace into a deterministic bundle directory.

    Collects and packages envelopes in the base..head range into a directory for audit verification.

    Parameters:
        workspace (str): The absolute path to the local git repository workspace.
        base (str): The base commit or ref of the range.
        head (str): The head commit or ref of the range.
        output (str): The absolute path to the output bundle directory.
    """
    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {workspace}")

    out_path = Path(output).expanduser().resolve()
    return _gate.export_envelope_bundle(base, head, out_path, root=root)


def main() -> None:
    """Run the Matrix Scroll MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
