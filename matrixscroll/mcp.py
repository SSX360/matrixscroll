from __future__ import annotations

# Path injection to allow relative imports in site-packages/install
import sys
from pathlib import Path
package_dir = Path(__file__).resolve().parent
if str(package_dir) not in sys.path:
    sys.path.append(str(package_dir))

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


from typing import Any

from mcp.server.fastmcp import FastMCP

from . import mcp_core as core

mcp = FastMCP("matrixscroll-mcp")


@mcp.tool()
def analyze_workspace(workspace: str) -> dict[str, Any]:
    """Scan a local workspace directory and return its project profile.

    This tool is read-only and performs an offline scan of the target directory to detect
    programming languages, active frameworks, dependencies, and project structure signals.
    It does not modify any files.

    Parameters:
        workspace (str): The absolute path to the local directory to be analyzed.

    Returns:
        dict[str, Any]: A dictionary containing detected languages, frameworks, notable SDKs,
        package managers, manifest files, and a high-level summary string of the project profile.
    """
    return core.analyze_workspace(workspace)


@mcp.tool()
def brainstorm_workspace(workspace: str, goal: str = "", limit: int = 6) -> dict[str, Any]:
    """Generate local, file-grounded next-action brainstorm recommendations for a workspace.

    This tool is read-only and uses local project files, rules, and notes to suggest developer
    next steps. It is designed to be run offline.

    Parameters:
        workspace (str): The absolute path to the local project workspace.
        goal (str, optional): A specific engineering or product goal to align recommendations with. Defaults to "".
        limit (int, optional): The maximum number of recommendations to return. Defaults to 6.

    Returns:
        dict[str, Any]: A dictionary containing project summary, suggestions (each with title,
        prompt, category, and tag), and execution status flags.
    """
    return core.brainstorm_workspace(workspace, goal=goal, limit=limit)


@mcp.tool()
def recommend_ecosystem(
    workspace: str, goal: str = "", limit: int = 9, live: bool = False
) -> dict[str, Any]:
    """Recommend compatible MCP servers, skills, repositories, and APIs for a project.

    This tool recommends external ecosystem integrations matching the project profile.
    It has no side effects.

    Parameters:
        workspace (str): The absolute path to the local project workspace.
        goal (str, optional): The target engineering goal or capability needed. Defaults to "".
        limit (int, optional): The maximum number of recommendations to return. Defaults to 9.
        live (bool, optional): If True, query public ecosystem indexes for real-time recommendations.
                               If False (default), uses pre-cached local resources to run entirely offline.

    Returns:
        dict[str, Any]: A dictionary containing recommended repositories, MCP servers, and hosted API integrations.
    """
    return core.recommend_ecosystem(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def build_usecase_blueprint(
    workspace: str, goal: str = "", limit: int = 8, live: bool = False
) -> dict[str, Any]:
    """Synthesize a 3-layer architecture blueprint (BUILD/INTEGRATE/FOUNDATION) for a goal.

    This tool is read-only and structures ecosystem findings into an actionable design plan
    specifying what should be custom-built vs. integrated.

    Parameters:
        workspace (str): The absolute path to the local project workspace.
        goal (str, optional): The target development or architectural goal. Defaults to "".
        limit (int, optional): The maximum number of items to rank and recommend. Defaults to 8.
        live (bool, optional): If True, performs live network lookups for ecosystem tools.
                               If False (default), runs completely offline.

    Returns:
        dict[str, Any]: A dictionary detailing the 3-layer architectural canvas, confidence scores,
        patterns to borrow, and next steps.
    """
    return core.build_usecase_blueprint(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def scan_research_radar(
    workspace: str, goal: str = "", limit: int = 4, live: bool = False
) -> dict[str, Any]:
    """Surface academic papers, models, and AI releases relevant to the workspace.

    This tool is read-only and assists with literature mapping and model selection for agent tasks.

    Parameters:
        workspace (str): The absolute path to the local project workspace.
        goal (str, optional): The research topic or machine learning goal. Defaults to "".
        limit (int, optional): The maximum number of papers or models to return. Defaults to 4.
        live (bool, optional): If True, queries arXiv and Hugging Face API live.
                               If False (default), uses local cached results.

    Returns:
        dict[str, Any]: A dictionary listing relevant papers, machine learning models, and source metadata.
    """
    return core.scan_research_radar(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def scan_market_radar(
    workspace: str, goal: str = "", limit: int = 8, live: bool = False
) -> dict[str, Any]:
    """Surface launch directories and developer discussions matching a project goal.

    This tool is read-only and helps identify user objections, maker positioning, and market feedback.

    Parameters:
        workspace (str): The absolute path to the local project workspace.
        goal (str, optional): The product, feature category, or topic to search. Defaults to "".
        limit (int, optional): The maximum number of market signals to return. Defaults to 8.
        live (bool, optional): If True, queries Hacker News, DevHunt, and Uneed APIs live.
                               If False (default), runs completely offline.

    Returns:
        dict[str, Any]: A dictionary listing developer attention items, categories, and tags.
    """
    return core.scan_market_radar(workspace, goal=goal, limit=limit, live=live)


@mcp.tool()
def benchmark_openhuman(workspace: str) -> dict[str, Any]:
    """Compare the project's posture and tools against the OpenHuman framework.

    This tool is read-only and returns a product-level comparison to help define local features.

    Parameters:
        workspace (str): The absolute path to the local project workspace.

    Returns:
        dict[str, Any]: A dictionary detailing integration metrics, architectural alignments,
        and next-step suggestions.
    """
    return core.benchmark_openhuman(workspace)


@mcp.tool()
def audit_trust_surface(workspace: str, target: str = "auto") -> dict[str, Any]:
    """Audit the project for missing proof links, legacy names, and trust gaps.

    This tool is read-only and analyzes public-facing metadata and documentation files
    (such as README, docs, verify, index.html) to locate credentials and references.

    Parameters:
        workspace (str): The absolute path to the local project workspace to audit.
        target (str, optional): The target trust profile. Must be one of:
                                - "public-site": A public webpage surface.
                                - "mcp-server": An MCP server code surface.
                                - "trust-repo": A public repository layout.
                                - "repo": A standard repository layout.
                                - "auto" (default): Auto-detects target based on available files.

    Returns:
        dict[str, Any]: A dictionary containing a summary of detected proof links, stale naming issues,
        gaps in trust coverage, and recommended fixes.
    """
    return core.audit_trust_surface(workspace, target=target)


@mcp.tool()
def scaffold_editor_integration(
    workspace: str,
    editor: str,
    write: bool = False,
) -> dict[str, Any]:
    """Preview or write editor configurations to integrate the Matrix Scroll MCP server.

    This tool is write-capable. By default, it runs in preview-only mode returning a unified diff.
    It will only write the configuration to disk if the `write` parameter is explicitly set to True.

    Parameters:
        workspace (str): The absolute path to the local project workspace.
        editor (str): The target editor/host name. Supported values: "cursor", "vscode", "claude".
        write (bool, optional): If True, writes the updated configuration directly to the project's
                                editor settings directory. If False (default), returns a diff preview only.

    Returns:
        dict[str, Any]: A dictionary containing the target configuration path, config payload,
        unified diff preview, and write success status.
    """
    return core.scaffold_editor_integration(workspace, editor=editor, write=write)


@mcp.tool()
def plan_matrixscroll_rollout(
    workspace: str,
    audience: str,
    goal: str = "",
) -> dict[str, Any]:
    """Generate a structured, target-ready rollout plan for the Matrix Scroll protocol.

    This tool is read-only and outputs a target-specific playbook, objection-handling map,
    and compare hooks to make the security story clear to stakeholders.

    Parameters:
        workspace (str): The absolute path to the local project workspace.
        audience (str): The target stakeholder persona. Must be one of:
                        - "founder": Product-focused value and fast-proof setups.
                        - "security": Trust limits, sandboxing, and policy enforcement.
                        - "devrel": Copyable config blocks and developer rollout assets.
                        - "team": Rollout phases, workspace onboarding, and team config review.
        goal (str, optional): The specific engineering or adoption goal. Defaults to "".

    Returns:
        dict[str, Any]: A dictionary containing target-specific one-liners, steps, proof assets,
        common objections with responses, and comparison hooks.
    """
    return core.plan_matrixscroll_rollout(workspace, audience=audience, goal=goal)


def main() -> None:
    """Run the Matrix Scroll MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
