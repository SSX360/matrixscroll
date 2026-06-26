"""Directory-first standalone core for Matrix Scroll MCP."""

from __future__ import annotations

import difflib
import json
import os
from pathlib import Path
import sys
from typing import Any

from . import brainstorm as bs
from . import benchmark
from . import market_radar
from . import oss_insight
from . import research_radar
from . import scanner
from . import usecase_synthesizer
from . import workspace_config as wc

LEGACY_MCP_LABELS: dict[str, str] = {
    "cursor-copilot": "Legacy editor config label still appears.",
    "digital-rain": "Legacy public MCP identity still appears.",
    "digital rain mcp": "Legacy public MCP identity still appears.",
}

PROOF_SURFACE_HINTS: tuple[tuple[str, str], ...] = (
    ("Browser verifier", "/verify/"),
    ("Compare page", "/compare/"),
    ("PyPI provenance", "pypi.org/project/matrixscroll"),
    ("Conformance vectors", "/vectors"),
    ("GitHub Action", "matrixscroll-verify-action"),
    ("Security docs", "AGENTIC_AI_SECURITY"),
    ("Whitepaper", "WHITEPAPER"),
    ("Spec", "SPEC.md"),
)


def _config_for(workspace: Path) -> dict[str, Any]:
    return wc.load_config(workspace)


def analyze_workspace(path: str | Path) -> dict[str, Any]:
    """Scan a concrete workspace directory and return its project profile."""
    workspace = Path(path).expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"Not a directory: {workspace}")
    cfg = _config_for(workspace)
    nb_cfg = cfg.get("notebooks", {})
    if not nb_cfg.get("enabled", True):
        return scanner.scan_project(str(workspace), max_notebooks=0)
    return scanner.scan_project(
        str(workspace),
        max_notebooks=int(nb_cfg.get("max_notebooks", 10)),
        exclude_dirs=list(nb_cfg.get("exclude_dirs") or []),
    )


def _profile_for(path: str | Path, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    return profile if profile is not None else analyze_workspace(path)


def _detect_trust_target(workspace: Path, profile: dict[str, Any], target: str) -> str:
    if target != "auto":
        return target
    signals = {str(value).lower() for value in profile.get("signals", [])}
    frameworks = {str(value).lower() for value in profile.get("frameworks", [])}
    if (workspace / "mcp_server.py").exists():
        return "mcp-server"
    if "docs-site" in signals or "static-site" in frameworks or (workspace / "index.html").exists():
        return "public-site"
    if "provenance" in signals or "verification" in signals or (workspace / "README.md").exists():
        return "trust-repo"
    return "repo"


def _audit_surface_files(workspace: Path, target: str) -> list[Path]:
    candidates = [
        workspace / "README.md",
        workspace / "INTEGRATIONS.md",
        workspace / ".cursor" / "mcp.json.example",
        workspace / "mcp_server.py",
        workspace / "index.html",
        workspace / "docs" / "index.html",
        workspace / "compare" / "index.html",
        workspace / "ecosystem" / "index.html",
        workspace / "pricing" / "index.html",
        workspace / "mcp" / "index.html",
    ]
    if target == "public-site":
        candidates = [path for path in candidates if path.suffix == ".html" or path.name == "README.md"]
    elif target == "mcp-server":
        candidates = [
            workspace / "README.md",
            workspace / "INTEGRATIONS.md",
            workspace / ".cursor" / "mcp.json.example",
            workspace / "mcp_server.py",
        ]
    out: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path.exists() and path.is_file() and path not in seen:
            out.append(path)
            seen.add(path)
    return out


def _scan_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _audit_stale_names(files: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for needle, note in LEGACY_MCP_LABELS.items():
        matched_files: list[str] = []
        for path in files:
            text = _scan_text(path).lower()
            index = text.find(needle)
            if index >= 0:
                context = text[max(0, index - 120): index + len(needle) + 120]
                if any(marker in context for marker in ("compatibility", "deprecated", "legacy", "transition")):
                    continue
                matched_files.append(path.as_posix())
        if matched_files:
            findings.append(
                {
                    "label": needle,
                    "note": note,
                    "files": matched_files,
                }
            )
    return findings


def _audit_proof_links(files: list[Path]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for label, needle in PROOF_SURFACE_HINTS:
        for path in files:
            text = _scan_text(path)
            if needle.lower() in text.lower():
                links.append(
                    {
                        "label": label,
                        "match": needle,
                        "source": path.as_posix(),
                    }
                )
                break
    return links


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _audit_payload(
    workspace: Path,
    profile: dict[str, Any],
    target: str,
) -> dict[str, Any]:
    resolved_target = _detect_trust_target(workspace, profile, target)
    files = _audit_surface_files(workspace, resolved_target)
    stale_names = _audit_stale_names(files)
    proof_links = _audit_proof_links(files)
    proof_labels = {item["label"] for item in proof_links}
    trust_gaps: list[str] = []
    if resolved_target == "public-site" and not (workspace / "mcp" / "index.html").exists():
        trust_gaps.append("No dedicated /mcp/ route is present yet.")
    if "Browser verifier" not in proof_labels:
        trust_gaps.append("The trust surface does not link the browser verifier yet.")
    if "Compare page" not in proof_labels:
        trust_gaps.append("The trust surface does not answer the Sigstore/SLSA comparison in-place.")
    if "GitHub Action" not in proof_labels:
        trust_gaps.append("No CI proof link is visible yet.")
    if "Security docs" not in proof_labels:
        trust_gaps.append("No public security or policy proof link is visible yet.")
    if not any(item["label"] == "PyPI provenance" for item in proof_links):
        trust_gaps.append("No public package or release provenance link is visible yet.")
    if stale_names:
        trust_gaps.append("Legacy MCP naming still appears in public-facing or setup surfaces.")

    recommended_fixes: list[str] = []
    if resolved_target == "public-site" and not (workspace / "mcp" / "index.html").exists():
        recommended_fixes.append(
            "Add a dedicated /mcp/ page with a real audit sample, safety strip, and editor setup blocks."
        )
    if stale_names:
        recommended_fixes.append(
            "Switch setup examples to the canonical `matrixscroll-mcp` label and document legacy labels as compatibility-only guidance."
        )
    if "Browser verifier" not in proof_labels:
        recommended_fixes.append("Expose the browser verifier alongside the MCP story so proof stays one click away.")
    if "Compare page" not in proof_labels:
        recommended_fixes.append("Add a one-line compare hook that explains commit-time proof versus artifact attestations.")
    if "GitHub Action" not in proof_labels or "Security docs" not in proof_labels:
        recommended_fixes.append("Surface public proof links to CI verification and security docs near the primary MCP promise.")
    if not recommended_fixes and not trust_gaps:
        recommended_fixes.append("Keep the trust surface tight: refresh proof links, screenshots, and config examples as each release ships.")

    salient_signals = [str(value) for value in profile.get("signals", [])[:6]]
    summary_bits = [
        f"Detected {resolved_target.replace('-', ' ')} trust surface.",
        f"{len(proof_links)} proof link(s) surfaced.",
    ]
    if stale_names:
        summary_bits.append(f"{len(stale_names)} legacy naming issue(s) remain.")
    else:
        summary_bits.append("No legacy naming found in the audited surface.")
    if salient_signals:
        summary_bits.append("Signals: " + ", ".join(salient_signals) + ".")

    return {
        "workspace": str(workspace),
        "target": resolved_target,
        "summary": " ".join(summary_bits),
        "stale_names": stale_names,
        "proof_links": proof_links,
        "trust_gaps": trust_gaps,
        "recommended_fixes": _dedupe_strings(recommended_fixes),
    }


def _server_root() -> Path:
    return Path(__file__).resolve().parent


def _mcp_python_command(server_root: Path) -> str:
    if os.name == "nt":
        venv_python = server_root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = server_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _claude_config_path() -> Path:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def _editor_target_path(workspace: Path, editor: str) -> Path:
    if editor == "cursor":
        return workspace / ".cursor" / "mcp.json"
    if editor == "vscode":
        return workspace / ".vscode" / "mcp.json"
    if editor == "claude":
        return _claude_config_path()
    raise ValueError(f"Unsupported editor: {editor}")


def _editor_env(workspace: Path, editor: str) -> dict[str, str]:
    workspace_value = "${workspaceFolder}" if editor in {"cursor", "vscode"} else str(workspace)
    return {
        "COPILOT_WORKSPACE": workspace_value,
        "ANTHROPIC_API_KEY": "${env:ANTHROPIC_API_KEY}",
        "GEMINI_API_KEY": "${env:GEMINI_API_KEY}",
        "LLM_BACKEND": "ollama",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "OLLAMA_MODEL": "gemma4:e4b",
        "OLLAMA_CHAT_MODEL": "gemma3:4b",
    }


def _editor_config_payload(workspace: Path, editor: str) -> dict[str, Any]:
    server_root = _server_root()
    server_entry = {
        "type": "stdio",
        "command": _mcp_python_command(server_root),
        "args": [str(server_root / "mcp.py")],
        "env": _editor_env(workspace, editor),
    }
    return {
        "mcpServers": {
            "matrixscroll-mcp": server_entry,
        }
    }


def _load_json_text(path: Path) -> tuple[str, dict[str, Any]]:
    text = ""
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return text, {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Existing config is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Existing config must be a JSON object: {path}")
    return text, data


def _merge_mcp_config(existing: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    servers = dict(existing.get("mcpServers") or {})
    servers.update(update.get("mcpServers") or {})
    merged["mcpServers"] = servers
    return merged


def _diff_preview(before: str, after: str, target_path: Path) -> str:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"{target_path}.before",
        tofile=str(target_path),
        lineterm="",
    )
    return "\n".join(diff) or f"No changes required for {target_path}"


def list_project_rules(project_path: str | Path) -> list[dict[str, Any]]:
    """Read local project rule metadata without importing Flask app code."""
    rules_dir = Path(project_path).expanduser().resolve() / ".cursor" / "rules"
    if not rules_dir.exists() or not rules_dir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for f in rules_dir.glob("*.mdc"):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        description = ""
        globs = ""
        always_apply = False
        body = content
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
            for line in parts[1].splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == "description":
                    description = value
                elif key == "globs":
                    globs = value
                elif key == "alwaysApply":
                    always_apply = value.lower() == "true"
        out.append({
            "filename": f.name,
            "description": description or f.stem,
            "globs": globs,
            "always_apply": always_apply,
            "body": body,
        })
    return out


def brainstorm_workspace(
    path: str | Path,
    goal: str = "",
    limit: int = 6,
) -> dict[str, Any]:
    """Generate local brainstorm ideas for a concrete workspace directory."""
    workspace = Path(path).expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"Not a directory: {workspace}")
    cfg = _config_for(workspace)
    context = bs.gather_context(
        workspace=workspace,
        goal=goal,
        config=cfg,
        list_rules=lambda p: list_project_rules(p),
        catalog_search=None,
    )
    if not context.get("config", {}).get("brainstorm", {}).get("enabled", True):
        return {
            "workspace": str(workspace),
            "configured": True,
            "context_summary": bs.context_summary(context),
            "suggestions": [],
            "llm_enhanced": False,
            "disabled": True,
        }
    items = bs.suggest_offline(context, limit=limit)
    payload = {
        "workspace": str(workspace),
        "configured": True,
        "context_summary": bs.context_summary(context),
        "suggestions": [item.to_dict() for item in items],
        "llm_enhanced": False,
    }
    if goal:
        payload["goal"] = goal
    return payload


def recommend_ecosystem(
    path: str | Path,
    goal: str = "",
    categories: list[str] | tuple[str, ...] | None = None,
    limit: int = 9,
    live: bool = True,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Recommend MCPs, skills, and repos using local scan + OSS signals."""
    profile = _profile_for(path, profile)
    result = oss_insight.recommend(
        profile,
        goal=goal,
        categories=categories,
        limit=limit,
        live=live,
    )
    result["workspace"] = str(Path(path).expanduser().resolve())
    result["profile_summary"] = scanner.profile_summary(profile)
    return result


def benchmark_openhuman(path: str | Path, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = _profile_for(path, profile)
    result = benchmark.openhuman_benchmark(profile)
    result["workspace"] = str(Path(path).expanduser().resolve())
    result["profile_summary"] = scanner.profile_summary(profile)
    return result


def audit_trust_surface(
    path: str | Path,
    target: str = "auto",
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit proof links, stale names, and trust gaps for a workspace."""
    workspace = Path(path).expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"Not a directory: {workspace}")
    profile = _profile_for(workspace, profile)
    return _audit_payload(workspace, profile, target)


def scaffold_editor_integration(
    path: str | Path,
    editor: str,
    write: bool = False,
) -> dict[str, Any]:
    """Preview or write a narrowly scoped editor MCP config for Matrix Scroll MCP."""
    workspace = Path(path).expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"Not a directory: {workspace}")
    editor_name = editor.lower().strip()
    if editor_name not in {"cursor", "vscode", "claude"}:
        raise ValueError("editor must be one of: cursor, vscode, claude")

    target_path = _editor_target_path(workspace, editor_name)
    config = _editor_config_payload(workspace, editor_name)
    before_text, existing = _load_json_text(target_path)
    merged = _merge_mcp_config(existing, config)
    rendered = json.dumps(merged, indent=2) + "\n"
    preview = _diff_preview(before_text, rendered, target_path)

    wrote = False
    if write:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(rendered, encoding="utf-8")
        wrote = True

    return {
        "workspace": str(workspace),
        "editor": editor_name,
        "config": merged,
        "target_path": str(target_path),
        "diff_preview": preview,
        "wrote": wrote,
    }


def plan_matrixscroll_rollout(
    path: str | Path,
    audience: str,
    goal: str = "",
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a concise Matrix Scroll MCP rollout pack for a concrete workspace."""
    workspace = Path(path).expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"Not a directory: {workspace}")
    audience_name = audience.lower().strip()
    if audience_name not in {"founder", "security", "devrel", "team"}:
        raise ValueError("audience must be one of: founder, security, devrel, team")

    profile = _profile_for(workspace, profile)
    audit = _audit_payload(workspace, profile, "auto")
    target = audit["target"]
    target_phrase = {
        "public-site": "public trust surface",
        "mcp-server": "repo-backed MCP server",
        "trust-repo": "trust-heavy repo",
        "repo": "local repo",
    }.get(target, "local repo")
    goal_text = goal.strip() or "ship a proof-first Matrix Scroll MCP rollout"

    one_liners = {
        "founder": f"Turn this {target_phrase} into a trust audit, rollout plan, and setup-ready Matrix Scroll MCP story without losing the read-only safety posture.",
        "security": f"Use Matrix Scroll MCP to audit proof surfaces, flag stale trust claims, and preview tightly scoped editor setup before any write is allowed.",
        "devrel": f"Package this {target_phrase} into a proof-first Matrix Scroll MCP launch path with copyable setup, screenshots, and a clean compare hook.",
        "team": f"Roll Matrix Scroll MCP into one repo at a time: audit trust, preview config, then enable opt-in scaffolding only where the team approves it.",
    }

    rollout_steps = {
        "founder": [
            "Lead with the outcome: trust audit, rollout plan, and safe MCP setup in minutes.",
            "Show a real `audit_trust_surface` output next to a config preview so the value feels concrete immediately.",
            "Thread one MCP CTA through the homepage, docs, compare, and ecosystem instead of scattering disconnected mentions.",
            "Ship release proof with screenshots, verifier links, and a Steel smoke report before announcing broadly.",
        ],
        "security": [
            "Run `audit_trust_surface` against the repo and clean every stale public label before rollout.",
            "Keep the safety contract explicit: read-only by default, opt-in writes only for editor config scaffolding.",
            "Pair config previews with proof links to the verifier, GitHub Action, vectors, and security docs.",
            "Use Steel QA to capture page evidence and fail the release if proof links or verifier surfaces regress.",
        ],
        "devrel": [
            "Open with a one-screen promise and a real MCP output sample from the repo being discussed.",
            "Publish copyable Cursor, VS Code, and Claude Desktop config blocks under the canonical `matrixscroll-mcp` label.",
            "Use the compare hook to explain that Matrix Scroll MCP is the operator layer around commit-time proof, not a generic assistant.",
            "Package screenshots of repo input, trust audit, config preview, and verifier proof as launch assets.",
        ],
        "team": [
            "Start in one workspace, preview config changes, and keep writes disabled until the owner opts in.",
            "Use the trust audit to spot missing proof links, stale names, and weak rollout surfaces before onboarding more repos.",
            "Anchor rollout around one repeatable path: audit, preview config, verify proof, then document the approved setup.",
            "Reuse the same MCP story across docs and internal rollout notes so adoption does not drift.",
        ],
    }

    proof_assets = [
        "Screenshot of the homepage or /mcp/ promise with the safety strip visible.",
        "Real `audit_trust_surface` output captured from the target repo.",
        "A `scaffold_editor_integration(..., write=false)` diff preview for one editor.",
        "Verifier or compare proof link showing commit-time proof versus artifact attestations.",
    ]
    if target == "public-site":
        proof_assets.append("A Steel QA pass/fail report with one screenshot per public route.")

    objections = {
        "Is this just another coding assistant?": "No. Matrix Scroll MCP is the trust and rollout layer around provenance, config scaffolding, and public proof QA.",
        "Will it mutate my repo silently?": "No. The MCP stays read-only by default and only writes editor config when `write=true` is explicitly requested.",
        "Why not just use Sigstore or SLSA?": "Those systems secure artifacts and CI. Matrix Scroll MCP helps operators package commit-time proof, trust surfaces, and rollout guidance around them.",
    }
    if audience_name == "security":
        objections["Can we review the exact config change first?"] = "Yes. `scaffold_editor_integration` returns a diff preview by default and only writes after explicit opt-in."
    if audience_name == "devrel":
        objections["Is there anything shareable beyond docs?"] = "Yes. The launch path is repo input, trust audit output, config preview, and verifier proof with screenshots ready for launch posts."

    compare_hooks = [
        "Matrix Scroll proves who or what made the commit before merge; Sigstore and SLSA prove what CI built later.",
        "Matrix Scroll MCP is the operator layer around that proof: audit the trust surface, scaffold safe setup, and package the rollout story.",
        "Steel Browser stays internal QA, not a required customer dependency, so the public promise stays local-first and trust-first.",
    ]

    return {
        "workspace": str(workspace),
        "audience": audience_name,
        "goal": goal_text,
        "one_liner": one_liners[audience_name],
        "rollout_steps": rollout_steps[audience_name],
        "proof_assets": proof_assets,
        "objections": objections,
        "compare_hooks": compare_hooks,
        "trust_summary": audit["summary"],
    }


def scan_research_radar(
    path: str | Path,
    goal: str = "",
    limit: int = 4,
    live: bool = True,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = _profile_for(path, profile)
    result = research_radar.research_radar(profile, goal=goal, limit=limit, live=live)
    result["workspace"] = str(Path(path).expanduser().resolve())
    result["profile_summary"] = scanner.profile_summary(profile)
    return result


def scan_market_radar(
    path: str | Path,
    goal: str = "",
    sources: list[str] | tuple[str, ...] | None = None,
    limit: int = 8,
    live: bool = True,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = _profile_for(path, profile)
    default_goal = goal or scanner.profile_summary(profile)
    result = market_radar.scan_market(
        goal=default_goal,
        sources=sources,
        limit=limit,
        live=live,
    )
    result["workspace"] = str(Path(path).expanduser().resolve())
    result["profile_summary"] = scanner.profile_summary(profile)
    return result


def build_usecase_blueprint(
    path: str | Path,
    goal: str = "",
    sources: list[str] | tuple[str, ...] | None = None,
    limit: int = 8,
    live: bool = True,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workspace = Path(path).expanduser().resolve()
    profile = _profile_for(workspace, profile)
    default_goal = goal or scanner.profile_summary(profile)
    ecosystem = oss_insight.recommend(profile, goal=default_goal, limit=limit, live=live)
    research = research_radar.research_radar(profile, goal=default_goal, limit=min(4, limit), live=live)
    market = market_radar.scan_market(goal=default_goal, sources=sources, limit=limit, live=live)
    blueprint = usecase_synthesizer.build_blueprint(
        profile=profile,
        ecosystem=ecosystem,
        research=research,
        market=market,
        goal=default_goal,
    )
    blueprint["workspace"] = str(workspace)
    blueprint["live"] = live
    return blueprint
