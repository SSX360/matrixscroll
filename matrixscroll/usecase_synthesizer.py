"""Use-case blueprint synthesis for Digital Rain."""

from __future__ import annotations

from typing import Any

import scanner
import immersive_web


def _top(items: list[dict[str, Any]], n: int = 3) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: int(item.get("score") or 0), reverse=True)[:n]


def _name(row: dict[str, Any]) -> str:
    return str(row.get("name") or row.get("title") or row.get("modelId") or "candidate")


def _source_url(row: dict[str, Any]) -> str:
    return str(row.get("source_url") or row.get("url") or "")


def _stack_terms(profile: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for key in ("frameworks", "languages", "notable_sdks", "package_managers", "signals"):
        terms.extend(str(v) for v in profile.get(key, []) if v)
    return terms[:8]


def _profile_density(profile: dict[str, Any]) -> int:
    """Weight how richly the local scan describes the project.

    Confidence should track how grounded the blueprint is in real on-disk
    signals, not merely whether the offline radars returned seed data. Each
    detected language, framework, SDK, package manager, and manifest adds a
    capped contribution, so a single-signal repo scores well below a rich
    polyglot one instead of every project saturating at the ceiling.
    """
    languages = len(profile.get("languages") or [])
    frameworks = len(profile.get("frameworks") or [])
    sdks = len(profile.get("notable_sdks") or [])
    managers = len(profile.get("package_managers") or [])
    manifests = len(profile.get("manifests") or [])
    density = (
        min(12, languages * 4)
        + min(9, frameworks * 3)
        + min(6, sdks * 3)
        + min(4, managers * 2)
        + min(3, manifests)
    )
    return min(34, density)


def _confidence(
    profile: dict[str, Any],
    ecosystem: dict[str, Any],
    research: dict[str, Any],
    market: dict[str, Any],
) -> int:
    score = 30 + _profile_density(profile)
    if ecosystem.get("recommendations"):
        score += 12
    if research.get("papers") or research.get("models"):
        score += 12
    if market.get("items"):
        score += 12
    source_status = market.get("source_status") or {}
    ok_count = sum(1 for row in source_status.values() if row.get("ok"))
    score += min(8, ok_count * 2)
    return min(96, score)


def _landscape_tool(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _name(row),
        "tier": row.get("tier") or "integrate",
        "category": row.get("category"),
        "why": row.get("why_now") or "; ".join(row.get("reasons", [])[:2]),
        "pros": list(row.get("pros") or [])[:4],
        "cons": list(row.get("cons") or [])[:4],
        "api_docs": row.get("api_docs") or "",
        "funding": row.get("funding") or "",
        "source_url": _source_url(row),
        "score": int(row.get("score") or 0),
    }


def _tool_landscape(recs: list[dict[str, Any]], stack: list[str], summary: str) -> list[dict[str, Any]]:
    """Group recommendations into a 3-layer canvas: BUILD / INTEGRATE / FOUNDATION."""
    foundation = [r for r in recs if (r.get("tier") or "integrate") == "foundation"]
    integrate = [r for r in recs if (r.get("tier") or "integrate") not in ("foundation", "build")]
    build_owned = {
        "name": "Local project context spine",
        "tier": "build",
        "category": "build",
        "why": "The differentiated layer you own: product-specific UX, trust model, workflow, and domain logic.",
        "pros": ["Keeps the core value proposition in your control.", "No vendor lock-in around the product-defining layer.", "Can be tailored tightly to this repo's structure and audience."],
        "cons": ["You maintain and evolve it yourself."],
        "api_docs": "",
        "funding": "",
        "source_url": "",
        "score": 88,
    }
    return [
        {
            "layer": "BUILD",
            "intent": "Own the differentiated orchestration layer that wraps everything else.",
            "tools": [build_owned] + [_landscape_tool(r) for r in recs if (r.get("tier") or "") == "build"],
        },
        {
            "layer": "INTEGRATE",
            "intent": "Adopt mature OSS libraries, MCP servers, and skills instead of rebuilding commodity capabilities.",
            "tools": [_landscape_tool(r) for r in sorted(integrate, key=lambda r: int(r.get("score") or 0), reverse=True)[:6]],
        },
        {
            "layer": "FOUNDATION",
            "intent": "Lean on well-funded hosted infrastructure (top-invested APIs) you build on rather than operate.",
            "tools": [_landscape_tool(r) for r in sorted(foundation, key=lambda r: int(r.get("score") or 0), reverse=True)],
        },
    ]


def build_blueprint(
    profile: dict[str, Any],
    ecosystem: dict[str, Any],
    research: dict[str, Any],
    market: dict[str, Any],
    goal: str = "",
) -> dict[str, Any]:
    """Combine local, OSS, research, and market signals into a read-only plan."""
    goal = goal.strip() or "improve this project"
    stack = _stack_terms(profile)
    summary = scanner.profile_summary(profile)
    recs = list(ecosystem.get("recommendations") or [])
    market_items = list(market.get("items") or [])
    papers = list(research.get("papers") or [])
    models = list(research.get("models") or [])

    top_recs = _top(recs, 4)
    top_market = _top(market_items, 4)
    top_model = models[0] if models else {}
    top_paper = papers[0] if papers else {}
    goal_low = goal.lower()
    web_agent_goal = any(term in goal_low for term in (
        "web agent", "scrap", "crawl", "captcha", "proxy", "stagehand",
        "steel", "firecrawl", "skyvern", "browser-use", "parallel"
    ))
    web_agent_recs = [
        row for row in _top(recs, 6)
        if any(tag in row.get("tags", []) for tag in ("web-agent", "scraping", "automation", "llm-infrastructure"))
        and int(row.get("score") or 0) >= 65
    ]
    trust_context = any(term in goal_low for term in (
        "verification", "verifier", "provenance", "attestation", "sigstore",
        "security", "trust", "mcp", "protocol", "supply chain"
    )) or any(term in stack for term in (
        "verification", "provenance", "attestation", "sigstore",
        "security", "trust", "mcp", "protocol", "supply-chain"
    ))
    site_context = "static-site" in stack or "docs-site" in stack
    immersive_context = immersive_web.is_immersive_web_context(profile, goal)
    immersive_recs = [
        row for row in recs
        if any(tag in row.get("tags", []) for tag in ("threejs", "webgl", "frontend", "docs", "testing"))
    ]

    power_stack = [
        {
            "name": "Local project context spine",
            "type": "build",
            "score": 88,
            "why": "Own the product-specific UX, trust model, domain logic, and workflow layer that differentiate this project.",
            "components": stack or ["workspace scanner", "vault", "diagnostics"],
            "evidence": [summary],
        },
        {
            "name": "OSS-backed integration radar",
            "type": "integrate",
            "score": int(top_recs[0].get("score") or 72) if top_recs else 72,
            "why": "Use mature repositories and MCP/skill projects as patterns before building bespoke connectors.",
            "components": [_name(row) for row in top_recs[:3]] or ["Context7", "Playwright MCP", "GitHub MCP Server"],
            "evidence": [reason for row in top_recs[:2] for reason in row.get("reasons", [])[:2]],
        },
        {
            "name": "Research and model radar",
            "type": "monitor",
            "score": 76 if (top_paper or top_model) else 60,
            "why": "Keep the use case tied to current papers and available model artifacts instead of stale assumptions.",
            "components": [v for v in [top_paper.get("title"), top_model.get("modelId")] if v] or ["arXiv", "Hugging Face"],
            "evidence": [v for v in [top_paper.get("summary"), top_model.get("summary")] if v][:2],
        },
        {
            "name": "Launch-market feedback loop",
            "type": "validate",
            "score": int(top_market[0].get("score") or 70) if top_market else 70,
            "why": "Compare current launches and developer discussion before deciding what to re-engineer, combine, or avoid.",
            "components": [_name(row) for row in top_market[:3]],
            "evidence": [row.get("evidence") or row.get("description") for row in top_market[:3]],
        },
    ]
    if web_agent_goal or web_agent_recs:
        power_stack.insert(2, {
            "name": "AI web-agent infrastructure layer",
            "type": "integrate",
            "score": int(web_agent_recs[0].get("score") or 82) if web_agent_recs else 82,
            "why": "For live-web use cases, prefer proven browser/session/scraping infrastructure before building anti-bot, proxy, or extraction plumbing.",
            "components": [_name(row) for row in web_agent_recs[:4]] or ["Steel Browser", "Firecrawl", "Stagehand", "Skyvern"],
            "evidence": [row.get("why_now") or "; ".join(row.get("reasons", [])[:2]) for row in web_agent_recs[:3]],
        })
    if immersive_context:
        playbook = immersive_web.build_realism_playbook(profile, goal)
        power_stack.insert(2 if not (web_agent_goal or web_agent_recs) else 3, {
            "name": "Immersive WebGL realism layer",
            "type": "build",
            "score": int(immersive_recs[0].get("score") or 86) if immersive_recs else 86,
            "why": "Spatial/metaverse galleries need shader motion, PBR textures, portal paths, and tuned bloom — not static white rooms.",
            "components": [layer["layer"] for layer in playbook["layers"]],
            "evidence": [step for layer in playbook["layers"][:3] for step in layer["build"][:2]],
        })

    patterns = []
    for row in top_market[:4]:
        patterns.append({
            "pattern": _name(row),
            "source": row.get("source_name") or row.get("source"),
            "why_borrow": row.get("description") or row.get("evidence"),
            "url": _source_url(row),
        })
    for row in top_recs[:2]:
        patterns.append({
            "pattern": _name(row),
            "source": row.get("category", "ecosystem"),
            "why_borrow": row.get("why_now") or "; ".join(row.get("reasons", [])[:2]),
            "url": _source_url(row),
        })

    build_vs_integrate = [
        {
            "decision": "Build the project-specific orchestration layer",
            "rationale": "Own the domain-specific UX, trust model, workflow, and product logic that make this project distinct.",
            "confidence": "high",
        },
        {
            "decision": "Integrate mature retrieval, browser, GitHub, and model components where they fit",
            "rationale": "OSS metrics and ecosystem ranking reduce the risk of rebuilding commodity infrastructure.",
            "confidence": "medium",
        },
        {
            "decision": "Do not copy launch products; extract packaging, positioning, and workflow patterns",
            "rationale": "Market sources are evidence for what resonates, not source material to replicate directly.",
            "confidence": "high",
        },
    ]
    if trust_context:
        build_vs_integrate.insert(1, {
            "decision": "Use proven provenance and verification references before inventing adjacent trust claims",
            "rationale": "Reference mature supply-chain and attestation tooling so the product story stays anchored in real verification patterns, while keeping the differentiated trust envelope product-specific.",
            "confidence": "high",
        })
    if web_agent_goal or web_agent_recs:
        build_vs_integrate.insert(1, {
            "decision": "Integrate web-agent infrastructure before building browser plumbing",
            "rationale": "Browser sessions, scraping, CAPTCHA handling, proxies, and selector resilience are specialized infrastructure with active OSS and commercial ecosystems.",
            "confidence": "high",
        })
    if immersive_context:
        build_vs_integrate.insert(1, {
            "decision": "Build shader-driven motion and portal architecture locally; integrate Three.js + doc MCPs",
            "rationale": "Immersive realism comes from custom GLSL, procedural textures, post-processing, and QA iteration — use Context7 and Playwright MCP for docs and smoke tests, not generic UI templates.",
            "confidence": "high",
        })

    research_edge = []
    for paper in papers[:3]:
        research_edge.append({
            "title": paper.get("title"),
            "kind": "paper",
            "why_now": paper.get("summary"),
            "url": paper.get("url"),
        })
    for model in models[:3]:
        research_edge.append({
            "title": model.get("modelId"),
            "kind": "model",
            "why_now": f"{model.get('pipeline_tag') or 'model'} · {int(model.get('downloads') or 0):,} downloads",
            "url": model.get("url"),
        })

    market_proof = [
        {
            "title": row.get("title"),
            "source": row.get("source_name"),
            "signal": row.get("evidence") or row.get("description"),
            "score": row.get("score"),
            "url": row.get("url"),
        }
        for row in top_market[:5]
    ]

    next_steps = [
        "Define the exact user job and success metric for the goal.",
        "Select one power-stack composition and map it to the active repo's existing files.",
        "Prototype only the local orchestration layer; integrate mature OSS components for commodity capabilities.",
        "Validate positioning against launch-directory patterns and HN objections before expanding scope.",
        "Add tests around the chosen workflow before adding any write/install actions.",
    ]
    if site_context:
        next_steps.insert(1, "Trace the shortest path from homepage to proof so a new visitor can see a real verification outcome before reading deep docs.")
    if trust_context:
        next_steps.insert(2, "Audit the verifier, MCP setup story, and comparison claims against Sigstore, in-toto, and attestation-adjacent expectations.")
    if web_agent_goal or web_agent_recs:
        next_steps.insert(2, "Evaluate Steel Browser, Firecrawl, Stagehand, Browser Use, and Skyvern against the target web workflow before writing custom browser infrastructure.")
    if immersive_context:
        next_steps.insert(1, "Apply the immersive WebGL playbook: void environment, shader uTime loop, portal path, UnrealBloomPass with high threshold, then browser QA.")
        next_steps.insert(2, "Modularize into src/shaders, src/scene, and src/effects; verify stars, river, and portals animate every frame.")

    evidence = {
        "local": {"summary": summary, "stack": stack, "path": profile.get("path")},
        "ecosystem": [
            {"name": _name(row), "score": row.get("score"), "url": _source_url(row), "reasons": row.get("reasons", [])[:3]}
            for row in top_recs
        ],
        "research": research_edge[:4],
        "market": market_proof,
    }

    sources = []
    for collection in (ecosystem.get("sources") or [], research.get("sources") or [], market.get("sources") or []):
        if collection not in sources:
            sources.append(collection)

    result = {
        "goal": goal,
        "profile_summary": summary,
        "confidence": _confidence(profile, ecosystem, research, market),
        "power_stack": power_stack,
        "tool_landscape": _tool_landscape(recs, stack, summary),
        "patterns_to_borrow": patterns[:6],
        "build_vs_integrate": build_vs_integrate,
        "research_edge": research_edge[:6],
        "market_proof": market_proof,
        "next_steps": next_steps,
        "evidence": evidence,
        "source_status": {
            "market": market.get("source_status", {}),
            "ecosystem_live": ecosystem.get("live"),
            "research_live": research.get("live"),
        },
        "sources": sources,
    }
    if immersive_context:
        result["immersive_web_playbook"] = immersive_web.build_realism_playbook(profile, goal)
    return result
