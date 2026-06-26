"""OSS ecosystem intelligence for Digital Rain recommendations.

The module is intentionally conservative: curated seed projects always work
offline, cached metrics avoid repeated API calls, and live network enrichment is
best-effort through OSSInsight first with GitHub REST as a fallback.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import requests

OSSINSIGHT_API_BASE = os.environ.get("OSSINSIGHT_API_BASE", "https://api.ossinsight.io/v1")
GITHUB_API_BASE = os.environ.get("GITHUB_API_BASE", "https://api.github.com")
DEFAULT_CACHE_TTL_SECONDS = int(os.environ.get("OSS_INSIGHT_CACHE_TTL", str(12 * 60 * 60)))
CACHE_DIR = Path(os.environ.get("DIGITAL_RAIN_CACHE_DIR", Path.home() / ".digital-rain" / "cache"))


@dataclass(frozen=True)
class EcosystemCandidate:
    repo: str
    name: str
    category: str
    description: str
    tags: tuple[str, ...]
    install_hint: str
    source_url: str
    tier: str = "integrate"
    api_docs: str = ""
    funding: str = ""
    pros: tuple[str, ...] = ()
    cons: tuple[str, ...] = ()


SEED_CANDIDATES: tuple[EcosystemCandidate, ...] = (
    EcosystemCandidate(
        "upstash/context7",
        "Context7",
        "mcp",
        "Up-to-date documentation context for coding agents and editors.",
        ("mcp", "docs", "context", "typescript", "javascript", "next", "react", "html", "css", "static-site", "protocol"),
        "Review the repo docs, then add its MCP server through your editor or agent host.",
        "https://github.com/upstash/context7",
    ),
    EcosystemCandidate(
        "modelcontextprotocol/servers",
        "MCP Servers",
        "mcp",
        "Reference and community MCP servers for common developer tools.",
        ("mcp", "servers", "integrations", "developer-tools"),
        "Use as the catalog starting point for MCP server selection.",
        "https://github.com/modelcontextprotocol/servers",
    ),
    EcosystemCandidate(
        "github/github-mcp-server",
        "GitHub MCP Server",
        "mcp",
        "Repository, issue, pull request, and GitHub workflow context for agents.",
        ("mcp", "github", "devops", "repo", "issues", "pull-requests", "ci", "github-action", "security"),
        "Use when the project workflow depends on GitHub issues, PRs, or Actions.",
        "https://github.com/github/github-mcp-server",
    ),
    EcosystemCandidate(
        "microsoft/playwright-mcp",
        "Playwright MCP",
        "mcp",
        "Browser automation and end-to-end verification for agent workflows.",
        ("mcp", "browser", "testing", "playwright", "frontend", "next", "react", "verification", "qa", "html", "css", "static-site", "vercel"),
        "Use for browser verification of local web apps and UI workflows.",
        "https://github.com/microsoft/playwright-mcp",
    ),
    EcosystemCandidate(
        "sigstore/sigstore-python",
        "Sigstore Python",
        "repos",
        "Python tooling for signing and verifying software provenance with Sigstore.",
        ("python", "security", "provenance", "verification", "sigstore", "supply-chain", "trust"),
        "Use when the project needs a concrete reference point for software signing and offline verification flows.",
        "https://github.com/sigstore/sigstore-python",
    ),
    EcosystemCandidate(
        "sigstore/cosign",
        "Cosign",
        "repos",
        "CLI and libraries for signing and verifying containers and software artifacts.",
        ("go", "security", "provenance", "verification", "sigstore", "attestation", "sbom", "supply-chain"),
        "Use as a reference for artifact signatures, attestations, and provenance UX.",
        "https://github.com/sigstore/cosign",
    ),
    EcosystemCandidate(
        "in-toto/in-toto",
        "in-toto",
        "repos",
        "Framework for protecting software supply-chain integrity with verifiable metadata.",
        ("python", "security", "provenance", "verification", "attestation", "in-toto", "supply-chain"),
        "Use when the product needs a reference model for step-level provenance and trust metadata.",
        "https://github.com/in-toto/in-toto",
    ),
    EcosystemCandidate(
        "slsa-framework/slsa-github-generator",
        "SLSA GitHub Generator",
        "repos",
        "GitHub Actions generator for SLSA provenance and build attestations.",
        ("github", "ci", "github-action", "security", "provenance", "attestation", "slsa", "supply-chain"),
        "Use when the project needs CI-backed provenance references instead of standalone signing only.",
        "https://github.com/slsa-framework/slsa-github-generator",
    ),
    EcosystemCandidate(
        "mrdoob/three.js",
        "Three.js",
        "repos",
        "WebGL/WebGPU 3D library for immersive sites, galleries, and spatial experiences.",
        ("threejs", "webgl", "javascript", "frontend", "vite", "3d", "immersive"),
        "Use for walkable 3D rooms, shader portals, post-processing, and metaverse-style web apps.",
        "https://github.com/mrdoob/three.js",
    ),
    EcosystemCandidate(
        "pmndrs/react-three-fiber",
        "React Three Fiber",
        "repos",
        "React renderer for Three.js — component model for interactive 3D UIs.",
        ("threejs", "webgl", "react", "frontend", "3d", "immersive"),
        "Use when the immersive experience is React-based instead of vanilla Vite + Three.js.",
        "https://github.com/pmndrs/react-three-fiber",
    ),
    EcosystemCandidate(
        "openai/codex",
        "OpenAI Codex",
        "skills",
        "Coding agent workflow for local codebase changes and verification.",
        ("agent", "coding", "openai", "python", "javascript", "typescript"),
        "Use as a reference for agentic local development workflows.",
        "https://github.com/openai/codex",
    ),
    EcosystemCandidate(
        "anthropics/claude-code",
        "Claude Code",
        "skills",
        "Terminal-native coding agent patterns and developer workflows.",
        ("agent", "coding", "terminal", "skills"),
        "Use as a benchmark for coding-agent UX and task execution patterns.",
        "https://github.com/anthropics/claude-code",
    ),
    EcosystemCandidate(
        "All-Hands-AI/OpenHands",
        "OpenHands",
        "skills",
        "Open-source autonomous software engineering agent.",
        ("agent", "coding", "automation", "python", "javascript"),
        "Use as a reference for autonomous issue-to-change workflows.",
        "https://github.com/All-Hands-AI/OpenHands",
    ),
    EcosystemCandidate(
        "anomalyco/opencode",
        "OpenCode",
        "skills",
        "Open coding agent interface and workflow patterns.",
        ("agent", "coding", "cli", "developer-tools"),
        "Use as a lightweight reference for agent UX and repository operations.",
        "https://github.com/anomalyco/opencode",
    ),
    EcosystemCandidate(
        "block/goose",
        "Goose",
        "skills",
        "Local AI agent for developer automation and tool use.",
        ("agent", "coding", "automation", "local"),
        "Use as a reference for local-first agent workflows.",
        "https://github.com/block/goose",
    ),
    EcosystemCandidate(
        "run-llama/llama_index",
        "LlamaIndex",
        "repos",
        "Data framework for RAG, knowledge agents, and retrieval pipelines.",
        ("rag", "retrieval", "python", "llm", "context"),
        "Use when the project needs structured retrieval over documents or code.",
        "https://github.com/run-llama/llama_index",
    ),
    EcosystemCandidate(
        "infiniflow/ragflow",
        "RAGFlow",
        "repos",
        "RAG engine focused on document understanding and retrieval workflows.",
        ("rag", "documents", "retrieval", "llm"),
        "Use as a reference for full RAG product architecture.",
        "https://github.com/infiniflow/ragflow",
    ),
    EcosystemCandidate(
        "qdrant/qdrant",
        "Qdrant",
        "repos",
        "Vector database for semantic search and memory layers.",
        ("vector-db", "retrieval", "rust", "python", "rag"),
        "Use when the project needs durable semantic retrieval at scale.",
        "https://github.com/qdrant/qdrant",
    ),
    EcosystemCandidate(
        "chroma-core/chroma",
        "Chroma",
        "repos",
        "Embeddings database for local-first AI apps and RAG prototypes.",
        ("vector-db", "retrieval", "python", "rag", "local"),
        "Use when prototyping local semantic memory or document retrieval.",
        "https://github.com/chroma-core/chroma",
    ),
    EcosystemCandidate(
        "steel-dev/awesome-web-agents",
        "Awesome Web Agents",
        "repos",
        "Curated map of tools, frameworks, and resources for AI agents that browse and interact with the web.",
        ("web-agent", "browser", "automation", "scraping", "agent", "llm-infrastructure"),
        "Use as the discovery spine for AI web-agent infrastructure choices.",
        "https://github.com/steel-dev/awesome-web-agents",
    ),
    EcosystemCandidate(
        "steel-dev/steel-browser",
        "Steel Browser",
        "repos",
        "Open-source browser API for AI apps and agents that need managed web interaction infrastructure.",
        ("web-agent", "browser", "automation", "scraping", "agent", "python"),
        "Use when the use case needs browser sessions, web interaction, or scraping infrastructure.",
        "https://github.com/steel-dev/steel-browser",
        api_docs="https://docs.steel.dev",
        pros=(
            "Open-source core you can self-host with no per-session vendor lock-in.",
            "Session APIs, proxies, and CAPTCHA handling purpose-built for agents.",
        ),
        cons=(
            "Self-hosting browser fleets adds ops burden versus a managed tier.",
            "Younger project, so APIs and integrations are still evolving.",
        ),
    ),
    EcosystemCandidate(
        "firecrawl/firecrawl",
        "Firecrawl",
        "repos",
        "Web context API that turns sites into clean Markdown, structured JSON, screenshots, and agent-ready data.",
        ("scraping", "markdown", "web-agent", "agent", "rag", "data-extraction"),
        "Use when the project needs reliable web-to-context ingestion.",
        "https://github.com/firecrawl/firecrawl",
        api_docs="https://docs.firecrawl.dev",
        pros=(
            "Turns arbitrary sites into clean, agent-ready Markdown and JSON.",
            "Open-source with a hosted tier, so prototyping-to-scale path is short.",
        ),
        cons=(
            "Crawl-heavy workloads can get costly on the hosted plan.",
            "Extraction quality varies on heavily dynamic or anti-bot sites.",
        ),
    ),
    EcosystemCandidate(
        "browserbase/stagehand",
        "Stagehand",
        "repos",
        "Browser automation framework for controlling web browsers with natural language and code.",
        ("browser", "automation", "web-agent", "playwright", "typescript", "agent"),
        "Use when the workflow needs reliable browser actions mixed with code-level control.",
        "https://github.com/browserbase/stagehand",
        api_docs="https://docs.stagehand.dev",
        pros=(
            "Blends natural-language actions with deterministic Playwright code.",
            "Backed by Browserbase, so it pairs cleanly with managed browser infra.",
        ),
        cons=(
            "Natural-language steps can be non-deterministic without guardrails.",
            "Best leverage assumes a hosted browser backend underneath.",
        ),
    ),
    EcosystemCandidate(
        "browser-use/browser-use",
        "Browser Use",
        "repos",
        "Open-source framework for connecting AI agents to browser interaction workflows.",
        ("browser", "automation", "web-agent", "python", "agent"),
        "Use as a reference for browser-agent loops and task execution patterns.",
        "https://github.com/browser-use/browser-use",
    ),
    EcosystemCandidate(
        "Skyvern-AI/skyvern",
        "Skyvern",
        "repos",
        "AI browser automation for multi-step workflows, form filling, and structured extraction.",
        ("browser", "automation", "web-agent", "playwright", "rpa", "agent"),
        "Use when the use case resembles resilient workflow automation across real websites.",
        "https://github.com/Skyvern-AI/skyvern",
    ),
    EcosystemCandidate(
        "parallel-web/parallel",
        "Parallel",
        "infrastructure",
        "Hosted web research API that runs deep, multi-source web tasks and returns structured, agent-ready answers.",
        ("web-agent", "research", "search", "automation", "agent", "llm-infrastructure", "hosted"),
        "Adopt as a managed research backend instead of building your own crawl-and-synthesize loop.",
        "https://parallel.ai",
        tier="foundation",
        api_docs="https://docs.parallel.ai",
        funding="Well-funded commercial web research API with active investor backing.",
        pros=(
            "Offloads deep multi-source web research to a managed, scalable API.",
            "Returns structured, citation-backed results ready for agent reasoning.",
        ),
        cons=(
            "Closed, usage-priced service — a recurring cost and external dependency.",
            "Less control over crawl behavior than a self-hosted stack.",
        ),
    ),
    EcosystemCandidate(
        "steel-dev/steel-browser",
        "Steel.dev Cloud",
        "infrastructure",
        "Managed cloud browser sessions for AI agents — proxies, CAPTCHA handling, and session APIs without running a fleet.",
        ("web-agent", "browser", "automation", "scraping", "agent", "hosted", "llm-infrastructure"),
        "Adopt as the managed browser layer when self-hosting Steel Browser is not worth the ops cost.",
        "https://steel.dev",
        tier="foundation",
        api_docs="https://docs.steel.dev",
        funding="Venture-backed (Y Combinator) with an open-source core and hosted tier.",
        pros=(
            "Managed browser sessions remove fleet ops, proxies, and anti-bot upkeep.",
            "Open-source core means a self-host exit path if you outgrow the hosted tier.",
        ),
        cons=(
            "Hosted usage is metered and adds an external runtime dependency.",
            "Heavy parallel browsing can become a notable line item.",
        ),
    ),
    EcosystemCandidate(
        "browserbase/stagehand",
        "Browserbase",
        "infrastructure",
        "Headless browser infrastructure for AI agents — scalable sessions, stealth, and observability as a managed service.",
        ("web-agent", "browser", "automation", "scraping", "agent", "hosted", "llm-infrastructure"),
        "Adopt as the managed browser runtime that pairs with Stagehand for code-plus-NL control.",
        "https://browserbase.com",
        tier="foundation",
        api_docs="https://docs.browserbase.com",
        funding="Well-funded browser-infrastructure company with strong venture backing.",
        pros=(
            "Scalable managed browser sessions with stealth and live observability.",
            "First-class Stagehand integration for mixed natural-language and code control.",
        ),
        cons=(
            "Proprietary, usage-priced platform with vendor lock-in risk.",
            "Overkill for projects that only need occasional local browser automation.",
        ),
    ),
)


def _cache_path(repo: str) -> Path:
    safe = repo.replace("/", "__")
    return CACHE_DIR / f"repo__{safe}.json"


def _read_cache(repo: str, ttl_seconds: int) -> dict[str, Any] | None:
    path = _cache_path(repo)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() - float(data.get("cached_at", 0)) > ttl_seconds:
        return None
    return data.get("metrics") if isinstance(data.get("metrics"), dict) else None


def _write_cache(repo: str, metrics: dict[str, Any]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(repo).write_text(
            json.dumps({"cached_at": time.time(), "metrics": metrics}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": "Digital-Rain"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_ossinsight_metrics(repo: str, timeout: float = 4.0) -> dict[str, Any]:
    """Best-effort OSSInsight lookup.

    OSSInsight's public API is beta and endpoint shapes have changed over time,
    so this function accepts several common metric field names and otherwise
    returns an empty payload.
    """
    owner, name = repo.split("/", 1)
    urls = (
        f"{OSSINSIGHT_API_BASE}/repos/{owner}/{name}",
        f"{OSSINSIGHT_API_BASE}/repo/{owner}/{name}",
    )
    for url in urls:
        try:
            resp = requests.get(url, headers={"Accept": "application/json"}, timeout=timeout)
            if not resp.ok:
                continue
            raw = resp.json()
            data = raw.get("data", raw) if isinstance(raw, dict) else {}
            if not isinstance(data, dict):
                continue
            return {
                "stars": _num(data, "stars", "stargazers_count", "star_count"),
                "forks": _num(data, "forks", "forks_count", "fork_count"),
                "open_issues": _num(data, "open_issues", "open_issues_count", "issues"),
                "contributors": _num(data, "contributors", "contributors_count"),
                "recent_growth": _num(data, "stars_growth", "star_growth", "growth"),
                "source": "ossinsight",
            }
        except (requests.RequestException, ValueError):
            continue
    return {}


def fetch_github_metrics(repo: str, timeout: float = 4.0) -> dict[str, Any]:
    url = f"{GITHUB_API_BASE}/repos/{repo}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout)
        if not resp.ok:
            return {}
        data = resp.json()
    except (requests.RequestException, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        "stars": int(data.get("stargazers_count") or 0),
        "forks": int(data.get("forks_count") or 0),
        "open_issues": int(data.get("open_issues_count") or 0),
        "contributors": 0,
        "recent_growth": 0,
        "pushed_at": data.get("pushed_at") or "",
        "source": "github",
    }


def _num(data: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = data.get(key)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def metrics_for_repo(repo: str, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> dict[str, Any]:
    cached = _read_cache(repo, ttl_seconds)
    if cached is not None:
        return {**cached, "cached": True}

    metrics = fetch_ossinsight_metrics(repo)
    if not metrics:
        metrics = fetch_github_metrics(repo)
    if not metrics:
        metrics = {
            "stars": 0,
            "forks": 0,
            "open_issues": 0,
            "contributors": 0,
            "recent_growth": 0,
            "source": "seed",
        }
    _write_cache(repo, metrics)
    return {**metrics, "cached": False}


_LANGUAGE_TAGS = {
    "python", "javascript", "typescript", "go", "rust", "ruby",
    "java", "php", "c", "cpp", "csharp", "kotlin", "swift",
}


def _ecosystem_aligned(candidate: EcosystemCandidate, profile: dict[str, Any]) -> bool:
    """Drop language-specific repos that don't match the detected stack.

    MCP servers, packaged skills, and hosted infrastructure are
    language-agnostic and always eligible. A ``repos`` candidate that
    advertises one or more programming-language tags is only relevant when at
    least one of those languages is actually present in the project — this is
    what stops a Rust or Go repo from being handed Python-only libraries.
    Candidates with no language tag (generic tooling) are left untouched.
    """
    if candidate.category != "repos":
        return True
    lang_tags = {t.lower() for t in candidate.tags} & _LANGUAGE_TAGS
    if not lang_tags:
        return True
    detected = {str(v).lower() for v in profile.get("languages", [])}
    return bool(lang_tags & detected)


def _fit_score(candidate: EcosystemCandidate, profile: dict[str, Any], goal: str) -> tuple[int, list[str]]:
    terms = set()
    for key in ("languages", "frameworks", "notable_sdks", "package_managers", "signals"):
        terms.update(str(v).lower() for v in profile.get(key, []) if v)
    terms.update(t for t in goal.lower().replace("/", " ").replace("-", " ").split() if len(t) > 2)
    tags = {t.lower() for t in candidate.tags}
    matched = sorted(terms & tags)
    score = min(35, len(matched) * 9)
    reasons = [f"matches project signal: {m}" for m in matched[:3]]

    summary = " ".join(sorted(terms))
    provenance_terms = {"security", "provenance", "verification", "attestation", "sigstore", "cosign", "in-toto", "slsa", "supply-chain", "trust"}
    trust_heavy = bool(provenance_terms & set(summary.split()))
    public_proof_surface = any(t in summary for t in ("docs-site", "static-site", "protocol", "mcp", "html", "css", "vercel"))
    if candidate.category == "mcp" and any(t in summary for t in ("github", "playwright", "next", "react", "typescript", "javascript")):
        score += 8
        reasons.append("fits agent/tooling integration needs")
    if candidate.category == "mcp" and any(t in summary for t in ("docs", "static-site", "vercel", "html", "css", "protocol", "mcp", "verification")):
        score += 8
        reasons.append("fits docs, protocol, or verification-site work")
    if candidate.category == "mcp" and trust_heavy and {"security", "github-action", "github"} & tags:
        score += 8
        reasons.append("fits trust-heavy rollout and proof operations")
    if candidate.category == "repos" and any(t in summary for t in ("python", "rag", "openai", "anthropic", "llm")):
        score += 8
        reasons.append("fits retrieval or AI context work")
    if candidate.category == "repos" and provenance_terms & set(summary.split()) and provenance_terms & tags:
        score += 12
        reasons.append("fits security, provenance, or trust-heavy product work")
    if candidate.category == "repos" and public_proof_surface and {"security", "provenance", "verification", "sigstore", "slsa", "in-toto"} & tags:
        score += 8
        reasons.append("fits public proof, comparison, or verifier storytelling")
    if candidate.category == "repos" and any(t in summary for t in ("browser", "scraping", "web", "agent", "automation", "playwright")):
        score += 10
        reasons.append("fits AI web-agent infrastructure work")
    if candidate.category == "skills" and any(t in summary for t in ("python", "typescript", "javascript")):
        score += 6
        reasons.append("fits coding-agent workflow patterns")
    if candidate.category == "infrastructure":
        score += 2
        reasons.append("hosted foundation layer you can build on instead of operate")
        if any(t in summary for t in ("browser", "scraping", "web", "agent", "automation", "research", "crawl", "search")):
            score += 8
            reasons.append("fits a web-agent or research workload")
    if trust_heavy and public_proof_surface and {"browser", "playwright", "scraping", "automation", "web-agent"} & tags:
        score -= 6
        reasons.append("de-prioritized because trust/provenance work is more central than browser infrastructure here")
    return min(score, 45), reasons


def _ecosystem_score(metrics: dict[str, Any]) -> tuple[int, list[str]]:
    stars = int(metrics.get("stars") or 0)
    forks = int(metrics.get("forks") or 0)
    issues = int(metrics.get("open_issues") or 0)
    contributors = int(metrics.get("contributors") or 0)
    growth = int(metrics.get("recent_growth") or 0)

    score = 0
    reasons: list[str] = []
    if stars:
        score += min(25, int(math.log10(stars + 1) * 8))
        reasons.append(f"{stars:,} GitHub stars")
    if forks:
        score += min(10, int(math.log10(forks + 1) * 4))
    if contributors:
        score += min(8, int(math.log10(contributors + 1) * 4))
        reasons.append(f"{contributors:,} contributors")
    if growth:
        score += min(10, int(math.log10(growth + 1) * 5))
        reasons.append(f"recent star growth: {growth:,}")
    if issues and stars and issues / max(stars, 1) > 0.08:
        score -= 5
        reasons.append("higher issue pressure")
    source = metrics.get("source", "seed")
    reasons.append(f"metrics source: {source}")
    return max(0, score), reasons


def _pros_cons(candidate: EcosystemCandidate, metrics: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Use curated pros/cons when present, otherwise derive sensible defaults."""
    pros = list(candidate.pros)
    cons = list(candidate.cons)
    if not pros:
        pros.append(candidate.description)
        stars = int(metrics.get("stars") or 0)
        if stars:
            pros.append(f"Validated by community traction ({stars:,} GitHub stars).")
        if candidate.tier == "foundation":
            pros.append("Managed hosted layer — no fleet or ops to run yourself.")
    if not cons:
        if candidate.tier == "foundation":
            cons.append("External, usage-priced dependency with vendor lock-in risk.")
        elif candidate.category == "repos":
            cons.append("Self-integrated component you own, deploy, and maintain.")
        else:
            cons.append("Requires wiring into your editor or agent host before it adds value.")
    return pros[:4], cons[:4]


def recommend(
    profile: dict[str, Any],
    goal: str = "",
    categories: list[str] | tuple[str, ...] | None = None,
    limit: int = 9,
    live: bool = True,
) -> dict[str, Any]:
    wanted = set(categories or ("mcp", "skills", "repos", "infrastructure"))
    rows: list[dict[str, Any]] = []
    for candidate in SEED_CANDIDATES:
        if candidate.category not in wanted:
            continue
        if not _ecosystem_aligned(candidate, profile):
            continue
        metrics = metrics_for_repo(candidate.repo) if live else {
            "stars": 0,
            "forks": 0,
            "open_issues": 0,
            "contributors": 0,
            "recent_growth": 0,
            "source": "seed",
            "cached": False,
        }
        fit, fit_reasons = _fit_score(candidate, profile, goal)
        ecosystem, ecosystem_reasons = _ecosystem_score(metrics)
        install_penalty = 4 if candidate.category == "repos" else 0
        base = 18 if candidate.tier == "foundation" else 20
        score = max(0, min(100, base + fit + ecosystem - install_penalty))
        reasons = fit_reasons + ecosystem_reasons
        if not fit_reasons:
            reasons.insert(0, "useful general ecosystem candidate")
        pros, cons = _pros_cons(candidate, metrics)
        rows.append({
            **asdict(candidate),
            "tags": list(candidate.tags),
            "pros": pros,
            "cons": cons,
            "metrics": metrics,
            "score": score,
            "reasons": reasons[:5],
            "why_now": _why_now(candidate, metrics, reasons),
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    selected = rows[:limit]
    selected_names = {r["name"] for r in selected}
    foundation_extra = [
        r for r in rows
        if r.get("tier") == "foundation" and r["name"] not in selected_names
    ]
    selected.extend(foundation_extra)
    return {
        "recommendations": selected,
        "sources": [
            "https://ossinsight.io/docs/api",
            "https://ossinsight.io/trending/ai",
            "https://ossinsight.io/blog/skills-layer-takes-over-2026",
            "https://ossinsight.io/blog/agent-memory-race-2026",
        ],
        "live": live,
        "cache_ttl_seconds": DEFAULT_CACHE_TTL_SECONDS,
    }


def _why_now(candidate: EcosystemCandidate, metrics: dict[str, Any], reasons: list[str]) -> str:
    source = metrics.get("source", "seed")
    if candidate.category == "infrastructure":
        theme = "well-funded hosted infrastructure is becoming the foundation layer teams build on instead of operate"
    elif candidate.category == "mcp":
        theme = "MCP and agent tool-use projects are active in the OSSInsight AI landscape"
    elif candidate.category == "skills":
        theme = "packaged coding skills and reusable agent workflows are becoming the practical layer above models"
    else:
        if any(tag in candidate.tags for tag in ("security", "provenance", "verification", "attestation", "sigstore", "supply-chain", "in-toto", "slsa")):
            theme = "software supply-chain verification and provenance tooling remain core reference points for trust-heavy products"
        elif any(tag in candidate.tags for tag in ("web-agent", "browser", "scraping", "automation")):
            theme = "AI web-agent infrastructure is a high-leverage layer for agents that need live web context"
        else:
            theme = "context, memory, and retrieval infrastructure remain core to useful project intelligence"
    evidence = reasons[0] if reasons else f"tracked from {source}"
    return f"{theme}; {evidence}."
