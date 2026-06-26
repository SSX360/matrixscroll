# Path injection to allow relative imports in site-packages/install
import sys
from pathlib import Path
package_dir = Path(__file__).resolve().parent
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))

"""Optional Matrix Scroll MCP server powered by Digital Rain.

Exposes the local intelligence engine (``digital_rain_core``) as Model Context
Protocol tools over stdio so agents and editors such as Cursor and Claude
Desktop can call it directly. The default posture is read-only: tools scan,
rank, explain, audit, and preview without mutating the repo. The only
write-capable surface is explicit editor-config scaffolding, and it only writes
when ``write=True`` is passed. Network enrichment stays opt-in per call
(``live`` defaults to ``False``) to preserve the offline-first guarantee.

Install the optional dependency with ``pip install .[mcp]`` and run with
``python mcp_server.py`` or point your editor's MCP config at that command.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import mcp_core as core

mcp = FastMCP("matrixscroll-mcp")


@mcp.tool()
def analyze_workspace(workspace: str) -> dict[str, Any]:
    """Scan a local workspace directory and return its project profile."""
    return core.analyze_workspace(workspace)


@mcp.tool()
def brainstorm_workspace(workspace: str, goal: str = "", limit: int = 6) -> dict[str, Any]:
    """Generate local, file-grounded next-move ideas for a workspace."""
    return core.brainstorm_workspace(workspace, goal=goal, limit=limit)


@mcp.tool()
def recommend_ecosystem(
    workspace: str, goal: str = "", limit: int = 9, live: bool = False
) -> dict[str, Any]:
    """Recommend MCP servers, skills, repos, and hosted foundation APIs."""
    return core.recommend_ecosystem(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def build_usecase_blueprint(
    workspace: str, goal: str = "", limit: int = 8, live: bool = False
) -> dict[str, Any]:
    """Synthesize a BUILD / INTEGRATE / FOUNDATION blueprint for a goal."""
    return core.build_usecase_blueprint(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def scan_research_radar(
    workspace: str, goal: str = "", limit: int = 4, live: bool = False
) -> dict[str, Any]:
    """Surface relevant papers and models for the workspace and goal."""
    return core.scan_research_radar(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def scan_market_radar(
    workspace: str, goal: str = "", limit: int = 8, live: bool = False
) -> dict[str, Any]:
    """Surface launch and developer-discussion signals for a goal."""
    return core.scan_market_radar(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def benchmark_openhuman(workspace: str) -> dict[str, Any]:
    """Compare the workspace's project-first posture against OpenHuman."""
    return core.benchmark_openhuman(workspace)


@mcp.tool()
def audit_trust_surface(workspace: str, target: str = "auto") -> dict[str, Any]:
    """Audit stale names, trust gaps, and proof links for a repo or public site."""
    return core.audit_trust_surface(workspace, target=target)


@mcp.tool()
def scaffold_editor_integration(
    workspace: str,
    editor: str,
    write: bool = False,
) -> dict[str, Any]:
    """Preview or explicitly write a narrow editor config for Matrix Scroll MCP."""
    return core.scaffold_editor_integration(workspace, editor=editor, write=write)


@mcp.tool()
def plan_matrixscroll_rollout(
    workspace: str,
    audience: str,
    goal: str = "",
) -> dict[str, Any]:
    """Generate a concise rollout pack for the Matrix Scroll MCP story."""
    return core.plan_matrixscroll_rollout(workspace, audience=audience, goal=goal)


def main() -> None:
    """Run the Matrix Scroll MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
