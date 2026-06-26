"""Context-aware brainstorm suggestions for the active workspace."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

import scanner
import vault
import workspace_config as wc
import llm

_JOB_TTL_SECONDS = 600
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


@dataclass
class BrainstormItem:
    title: str
    prompt: str
    tag: str
    category: str
    source: str = "offline"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _scan_workspace(workspace: Path, config: dict[str, Any]) -> dict:
    nb_cfg = config.get("notebooks", {})
    if not nb_cfg.get("enabled", True):
        return scanner.scan_project(str(workspace), max_notebooks=0)
    return scanner.scan_project(
        str(workspace),
        max_notebooks=int(nb_cfg.get("max_notebooks", 10)),
        exclude_dirs=list(nb_cfg.get("exclude_dirs") or []),
    )


def gather_context(
    workspace: Path | None = None,
    goal: str = "",
    config: dict[str, Any] | None = None,
    list_rules: Callable[[str], list[dict]] | None = None,
    catalog_search: Callable[[str, int], list[dict]] | None = None,
) -> dict[str, Any]:
    resolved_ws, resolved_configured = wc.resolve_workspace()
    ws = workspace if workspace is not None else resolved_ws
    cfg = config or wc.load_config(ws)
    profile = _scan_workspace(ws, cfg)

    rules: list[dict] = []
    if list_rules:
        rules = list_rules(str(ws))

    mcp_hits: list[dict] = []
    if catalog_search:
        query_parts = [
            scanner.profile_summary(profile),
            *profile.get("frameworks", []),
            *profile.get("notable_sdks", []),
        ]
        goal = " ".join(p for p in query_parts if p)
        if goal.strip():
            mcp_hits = catalog_search(goal, 3)

    vault_snippets: list[str] = []
    if cfg.get("brainstorm", {}).get("include_vault_context", True):
        vault_path = wc.resolve_vault_path(ws, cfg)
        if vault_path and vault_path.is_dir():
            query = " ".join(profile.get("frameworks", []) + profile.get("languages", []))
            if query.strip():
                try:
                    hits = vault.search_vault(query, str(vault_path), k=2)
                    vault_snippets = [h.get("text", "")[:200] for h in hits]
                except Exception:
                    pass

    return {
        "workspace": str(ws),
        "configured": True if workspace is not None else resolved_configured,
        "goal": goal,
        "profile": profile,
        "rules": rules,
        "mcp_hits": mcp_hits,
        "vault_snippets": vault_snippets,
        "config": cfg,
    }


def context_summary(context: dict[str, Any]) -> str:
    profile = context.get("profile", {})
    parts = []
    if profile.get("languages"):
        parts.append(", ".join(profile["languages"][:3]))
    if profile.get("frameworks"):
        parts.append(", ".join(profile["frameworks"][:2]))
    notebooks = profile.get("notebooks") or []
    if notebooks:
        parts.append(f"{len(notebooks)} notebook(s)")
    return " · ".join(parts) if parts else "project"


def suggest_offline(context: dict[str, Any], limit: int = 6) -> list[BrainstormItem]:
    items: list[BrainstormItem] = []
    profile = context.get("profile", {})
    rules = context.get("rules") or []
    configured = context.get("configured", False)
    goal_low = str(context.get("goal") or "").lower()
    frameworks = profile.get("frameworks") or []
    langs = profile.get("languages") or []
    sdks = profile.get("notable_sdks") or []
    signals = {str(v).lower() for v in profile.get("signals") or []}

    if not configured:
        items.append(BrainstormItem(
            title="Point Digital Rain at your active codebase",
            prompt="Help me configure the active workspace for Digital Rain so scans target my real project.",
            tag="Setup",
            category="workspace",
        ))

    site_or_docs_context = (
        "static-site" in frameworks
        or "docs-site" in signals
        or any(term in goal_low for term in ("homepage", "pricing", "docs", "copy", "cta", "funnel", "conversion"))
    )
    trust_context = (
        bool({"mcp", "verification", "provenance", "protocol", "security", "attestation", "trust"} & signals)
        or any(term in goal_low for term in (
            "mcp", "verification", "verifier", "proof", "provenance",
            "sigstore", "attestation", "trust", "offline verify",
        ))
    )

    if site_or_docs_context:
        items.append(BrainstormItem(
            title="Tighten the live proof path",
            prompt=(
                "Review the homepage, pricing, and verifier flow and identify the fastest path "
                "for a skeptical buyer to see a real proof without reading long docs first."
            ),
            tag="Funnel",
            category="product",
        ))
    if trust_context:
        items.append(BrainstormItem(
            title="Audit the MCP and verifier story",
            prompt=(
                "Audit the MCP setup story, verifier demo, and protocol explanation in this repo. "
                "Flag stale naming, unclear install steps, and missing trust evidence before a new user can trust it."
            ),
            tag="Trust",
            category="docs",
        ))

    vault_path = wc.resolve_vault_path(Path(context["workspace"]), context.get("config"))
    vault_mode = context.get("config", {}).get("vault", {}).get("mode", "project")
    if vault_mode == "project" and vault_path and not vault_path.exists():
        items.append(BrainstormItem(
            title="Create a project notes vault",
            prompt="Scaffold a docs/vault folder for this project and suggest what notes I should capture.",
            tag="Vault",
            category="vault",
        ))
    elif vault_mode == "existing" and not vault_path:
        items.append(BrainstormItem(
            title="Link your Obsidian vault path",
            prompt="Walk me through linking an existing Obsidian vault to this project in Digital Rain config.",
            tag="Vault",
            category="vault",
        ))

    for nb in profile.get("notebooks") or []:
        if nb.get("execution_health") == "out_of_order":
            name = nb.get("filename", "notebook")
            items.append(BrainstormItem(
                title=f"Fix out-of-order cells in {name}",
                prompt=(
                    f"My notebook {name} has out-of-order execution. "
                    "Explain the risks and a safe order to re-run cells."
                ),
                tag="Notebook health",
                category="notebook",
            ))
            break

    if "threejs" in sdks or ("vite" in frameworks and "javascript" in langs):
        items.append(BrainstormItem(
            title="Apply immersive WebGL realism checklist",
            prompt=(
                "Review this Vite/Three.js project against the Digital Rain immersive WebGL playbook: "
                "void environment, shader uTime animation loop, portal path with god-rays, "
                "UnrealBloomPass tuning, and browser QA. Suggest the highest-impact next improvements."
            ),
            tag="Immersive web",
            category="frontend",
        ))

    if not rules:
        scope = frameworks[0] if frameworks else (langs[0] if langs else "this project")
        items.append(BrainstormItem(
            title=f"Create a Cursor rule for {scope}",
            prompt=(
                f"Generate a .cursor/rules file for {scope} conventions in this codebase "
                "based on what you detect in the project scan."
            ),
            tag="Rules",
            category="rules",
        ))

    if frameworks:
        fw = frameworks[0]
        items.append(BrainstormItem(
            title=f"Rank ecosystem options for {fw}",
            prompt=(
                f"Scan my project and rank MCP servers, skills, and repositories that fit a {fw} stack. "
                "Explain the top matches without installing anything."
            ),
            tag="Ecosystem",
            category="ecosystem",
        ))
    elif sdks:
        sdk = sdks[0]
        items.append(BrainstormItem(
            title=f"Improve the {sdk} workflow",
            prompt=f"Suggest MCP servers, skills, repositories, and project rules that would improve my {sdk} workflow in this repo.",
            tag="Ecosystem",
            category="ecosystem",
        ))

    for hit in context.get("mcp_hits") or []:
        name = hit.get("name") or hit.get("title") or "MCP server"
        items.append(BrainstormItem(
            title=f"Evaluate {name} for this stack",
            prompt=f"Evaluate whether {name} fits this project, what it would help with, and what tradeoffs I should consider.",
            tag="Catalog match",
            category="ecosystem",
        ))

    if "python" in langs and not any(i.category == "notebook" for i in items):
        items.append(BrainstormItem(
            title="Scan Jupyter notebooks in this repo",
            prompt="Scan my project's notebooks and report execution health, imports, and variables.",
            tag="Notebook scan",
            category="notebook",
        ))

    if not items:
        items.append(BrainstormItem(
            title="Scan my project stack",
            prompt="Scan my project and summarize languages, frameworks, SDKs, and notable config signals.",
            tag="Project scan",
            category="workspace",
        ))

    seen: set[str] = set()
    unique: list[BrainstormItem] = []
    for item in items:
        key = item.prompt
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= limit:
            break
    return unique


def _llm_enhancement_allowed() -> bool:
    """Sync LLM brainstorm enhancement is for cloud backends only (Ollama is too slow)."""
    return llm.active_backend() in ("gemini", "anthropic")


def _prune_jobs() -> None:
    cutoff = time.monotonic() - _JOB_TTL_SECONDS
    with _jobs_lock:
        stale = [job_id for job_id, job in _jobs.items() if job.get("created", 0) < cutoff]
        for job_id in stale:
            _jobs.pop(job_id, None)


def get_enhancement_job(job_id: str) -> dict[str, Any] | None:
    _prune_jobs()
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def _run_enhancement_job(
    job_id: str,
    context: dict[str, Any],
    limit: int,
    generate: Callable[[str, list[dict]], str],
) -> None:
    try:
        items = _suggest_with_llm_raw(context, limit=limit, generate=generate)
        payload = {
            "status": "complete",
            "suggestions": [s.to_dict() for s in (items or [])],
            "llm_enhanced": bool(items),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        payload = {"status": "error", "suggestions": [], "llm_enhanced": False, "error": str(exc)}
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(payload)


def start_enhancement_job(
    context: dict[str, Any],
    limit: int,
    generate: Callable[[str, list[dict]], str],
) -> str:
    _prune_jobs()
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running",
            "suggestions": [],
            "llm_enhanced": False,
            "error": None,
            "created": time.monotonic(),
        }
    threading.Thread(
        target=_run_enhancement_job,
        args=(job_id, context, limit, generate),
        daemon=True,
    ).start()
    return job_id


def _suggest_with_llm_raw(
    context: dict[str, Any],
    limit: int,
    generate: Callable[[str, list[dict]], str],
) -> list[BrainstormItem] | None:
    profile = context.get("profile", {})
    summary = scanner.profile_summary(profile)
    notebooks = profile.get("notebooks") or []
    nb_text = ", ".join(
        f"{n.get('filename')}:{n.get('execution_health')}" for n in notebooks[:5]
    ) or "none"
    rules_count = len(context.get("rules") or [])

    sys_prompt = (
        "You suggest concise next-step ideas for a developer using Cursor. "
        "Return exactly one idea per line in the format: TITLE | PROMPT | TAG. "
        "Keep titles under 60 chars. Prompts must be actionable and reference the stack provided."
    )
    user = (
        f"Stack: {summary}\nNotebooks: {nb_text}\nRules count: {rules_count}\n"
        f"Generate {limit} tailored brainstorm ideas."
    )

    def _gen(system: str, messages: list[dict]) -> str:
        return generate(system, messages, ollama_num_predict=llm.OLLAMA_BRAINSTORM_NUM_PREDICT)

    raw = _gen(sys_prompt, [{"role": "user", "content": user}])

    items: list[BrainstormItem] = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|", 2)]
        if len(parts) < 2:
            continue
        title, prompt = parts[0], parts[1]
        tag = parts[2] if len(parts) > 2 else "Brainstorm"
        if title and prompt:
            items.append(BrainstormItem(title, prompt, tag, "llm", source="llm"))
        if len(items) >= limit:
            break
    return items or None


def suggest_with_llm(
    context: dict[str, Any],
    limit: int = 6,
    generate: Callable[..., str] | None = None,
) -> list[BrainstormItem] | None:
    if not generate:
        return None
    if not _llm_enhancement_allowed():
        return None
    if not context.get("config", {}).get("brainstorm", {}).get("prefer_llm_enhancement", True):
        return None
    try:
        return _suggest_with_llm_raw(context, limit=limit, generate=generate)
    except Exception:
        return None


def brainstorm(
    limit: int = 6,
    list_rules: Callable[[str], list[dict]] | None = None,
    catalog_search: Callable[[str, int], list[dict]] | None = None,
    llm_generate: Callable[..., str] | None = None,
    async_enhance: bool = False,
) -> dict[str, Any]:
    context = gather_context(list_rules=list_rules, catalog_search=catalog_search)
    if not context.get("config", {}).get("brainstorm", {}).get("enabled", True):
        return {
            "workspace": context["workspace"],
            "configured": context["configured"],
            "context_summary": context_summary(context),
            "suggestions": [],
            "llm_enhanced": False,
            "disabled": True,
        }
    cfg_limit = int(context.get("config", {}).get("brainstorm", {}).get("max_suggestions", limit))
    limit = min(limit, cfg_limit)
    cfg = context.get("config", {}).get("brainstorm", {})

    offline = suggest_offline(context, limit=limit)
    enhancement_job_id = None
    llm_items = None

    if (
        async_enhance
        and llm_generate
        and cfg.get("prefer_llm_enhancement", True)
        and llm.active_backend() == "ollama"
    ):
        enhancement_job_id = start_enhancement_job(context, limit=limit, generate=llm_generate)
    else:
        llm_items = suggest_with_llm(context, limit=limit, generate=llm_generate)

    suggestions = llm_items if llm_items else offline

    result = {
        "workspace": context["workspace"],
        "configured": context["configured"],
        "context_summary": context_summary(context),
        "suggestions": [s.to_dict() for s in suggestions],
        "llm_enhanced": bool(llm_items),
    }
    if enhancement_job_id:
        result["enhancement_job_id"] = enhancement_job_id
        result["enhancement_status"] = "running"
    return result
