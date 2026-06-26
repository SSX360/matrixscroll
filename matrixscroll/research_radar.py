"""Academic and model-release radar for Digital Rain."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import requests

CACHE_DIR = Path(os.environ.get("DIGITAL_RAIN_CACHE_DIR", Path.home() / ".digital-rain" / "cache"))
DEFAULT_CACHE_TTL_SECONDS = int(os.environ.get("RESEARCH_RADAR_CACHE_TTL", str(6 * 60 * 60)))
ARXIV_API_BASE = os.environ.get("ARXIV_API_BASE", "https://export.arxiv.org/api/query")
HF_API_BASE = os.environ.get("HF_API_BASE", "https://huggingface.co/api")
RADAR_CACHE_VERSION = "v2"

SOURCES = [
    "https://info.arxiv.org/help/api/user-manual.html",
    "https://huggingface.co/docs/huggingface_hub/en/guides/search",
    "https://huggingface.co/docs/hub/en/models-the-hub",
]

TOPIC_HINTS = {
    "python": ["agent memory", "retrieval augmented generation", "code agents"],
    "flask": ["local ai assistant", "software engineering agents", "tool use"],
    "anthropic": ["constitutional ai", "agent evaluation", "tool use"],
    "openai": ["reasoning models", "code generation", "agentic coding"],
    "pandas": ["dataframe agents", "data analysis agents"],
    "pytorch": ["efficient fine tuning", "small language models"],
    "notebook": ["notebook agents", "reproducible computational notebooks"],
    "verification": ["software supply chain security", "artifact verification", "signed provenance"],
    "provenance": ["software provenance", "signed provenance", "attestation"],
    "security": ["software supply chain security", "artifact verification", "slsa"],
    "attestation": ["software attestations", "artifact verification", "slsa"],
    "supply-chain": ["software supply chain security", "signed provenance", "slsa"],
    "sigstore": ["sigstore", "software signing", "artifact verification"],
    "mcp": ["developer tool integration", "human-ai tool use"],
}

SEED_PAPERS = [
    {
        "title": "Attention Is All You Need",
        "source": "seed",
        "url": "https://arxiv.org/abs/1706.03762",
        "published": "2017-06-12",
        "summary": "Transformer architecture foundation; useful as a baseline for model and context reasoning.",
    },
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "source": "seed",
        "url": "https://arxiv.org/abs/2005.11401",
        "published": "2020-05-22",
        "summary": "Core RAG pattern for grounding model outputs in external context.",
    },
]

SECURITY_SEED_PAPERS = [
    {
        "title": "A Defense-Oriented Evaluation of Software Supply Chain Security",
        "source": "seed",
        "url": "https://arxiv.org/abs/2405.14993",
        "published": "2024-05-23",
        "summary": "Recent academic framing for software supply-chain attacks, defenses, and practical posture gaps.",
    },
    {
        "title": "A Usability Case Study of Sigstore",
        "source": "seed",
        "url": "https://arxiv.org/abs/2503.00271",
        "published": "2025-03-01",
        "summary": "Explores how software signing and provenance verification behave in real maintainer workflows.",
    },
    {
        "title": "Sigstore: Software Signing for Everybody",
        "source": "seed",
        "url": "https://dl.acm.org/doi/10.1145/3548606.3560596",
        "published": "2022-11-07",
        "summary": "Describes a practical public-good signing system designed to make artifact signing and verification easier to adopt.",
    },
]

SEED_MODELS = [
    {
        "modelId": "sentence-transformers/all-MiniLM-L6-v2",
        "source": "seed",
        "url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
        "downloads": 0,
        "likes": 0,
        "pipeline_tag": "sentence-similarity",
        "summary": "Lightweight embedding model for local retrieval prototypes.",
    },
    {
        "modelId": "BAAI/bge-small-en-v1.5",
        "source": "seed",
        "url": "https://huggingface.co/BAAI/bge-small-en-v1.5",
        "downloads": 0,
        "likes": 0,
        "pipeline_tag": "sentence-similarity",
        "summary": "Compact embedding model often used for RAG baselines.",
    },
]


def topics_for_profile(profile: dict[str, Any], goal: str = "") -> list[str]:
    terms: list[str] = []
    if profile.get("notebooks"):
        terms.append("notebook")
    for key in ("frameworks", "languages", "notable_sdks", "signals"):
        terms.extend(str(v).lower() for v in profile.get(key, []) if v)
    goal_terms = [t for t in goal.lower().replace("-", " ").split() if len(t) > 3]
    topics: list[str] = []
    for term in terms:
        for topic in TOPIC_HINTS.get(term, []):
            if topic not in topics:
                topics.append(topic)
    for term in goal_terms:
        if term not in topics:
            topics.append(term)
    return topics[:8] or ["software engineering agents", "retrieval augmented generation"]


def _security_topics(topics: list[str]) -> bool:
    joined = " ".join(topics)
    return any(term in joined for term in (
        "verification", "provenance", "security", "attestation",
        "supply chain", "sigstore", "software signing", "artifact"
    ))


def _cache_path(kind: str, query: str) -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in query.lower())[:80]
    return CACHE_DIR / f"research__{RADAR_CACHE_VERSION}__{kind}__{safe}.json"


def _read_cache(kind: str, query: str, ttl_seconds: int) -> list[dict[str, Any]] | None:
    path = _cache_path(kind, query)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() - float(data.get("cached_at", 0)) > ttl_seconds:
        return None
    rows = data.get("items")
    return rows if isinstance(rows, list) else None


def _write_cache(kind: str, query: str, items: list[dict[str, Any]]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(kind, query).write_text(
            json.dumps({"cached_at": time.time(), "items": items}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def search_arxiv(query: str, limit: int = 4, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> list[dict[str, Any]]:
    cached = _read_cache("arxiv", query, ttl_seconds)
    if cached is not None:
        return [{**item, "cached": True} for item in cached[:limit]]
    parts = [part.strip() for part in query.split(" OR ") if part.strip()]
    search_query = " OR ".join(f'all:"{part[:80]}"' for part in parts) if parts else f'all:"{query[:80]}"'
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": limit,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API_BASE}?{urllib.parse.urlencode(params)}"
    try:
        resp = requests.get(url, timeout=6, headers={"User-Agent": "Digital-Rain"})
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items: list[dict[str, Any]] = []
        for entry in root.findall("atom:entry", ns):
            title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
            summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
            published = (entry.findtext("atom:published", default="", namespaces=ns) or "")[:10]
            link = ""
            for link_el in entry.findall("atom:link", ns):
                if link_el.attrib.get("rel") == "alternate":
                    link = link_el.attrib.get("href", "")
                    break
            if title:
                items.append({
                    "title": title,
                    "summary": summary[:260],
                    "published": published,
                    "url": link,
                    "source": "arxiv",
                    "cached": False,
                })
        _write_cache("arxiv", query, items)
        return items[:limit]
    except (requests.RequestException, ET.ParseError):
        return [{**item, "cached": False} for item in SEED_PAPERS[:limit]]


def search_huggingface(query: str, limit: int = 4, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> list[dict[str, Any]]:
    cached = _read_cache("hf", query, ttl_seconds)
    if cached is not None:
        return [{**item, "cached": True} for item in cached[:limit]]
    params = {
        "search": query,
        "sort": "downloads",
        "direction": -1,
        "limit": limit,
    }
    url = f"{HF_API_BASE}/models?{urllib.parse.urlencode(params)}"
    try:
        resp = requests.get(url, timeout=6, headers={"User-Agent": "Digital-Rain"})
        resp.raise_for_status()
        raw = resp.json()
        items: list[dict[str, Any]] = []
        for row in raw if isinstance(raw, list) else []:
            model_id = row.get("modelId") or row.get("id")
            if not model_id:
                continue
            items.append({
                "modelId": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "downloads": int(row.get("downloads") or 0),
                "likes": int(row.get("likes") or 0),
                "pipeline_tag": row.get("pipeline_tag") or "",
                "summary": "Public Hugging Face model candidate ranked by downloads for this radar query.",
                "source": "huggingface",
                "cached": False,
            })
        _write_cache("hf", query, items)
        return items[:limit]
    except (requests.RequestException, ValueError, TypeError):
        return [{**item, "cached": False} for item in SEED_MODELS[:limit]]


def research_radar(profile: dict[str, Any], goal: str = "", limit: int = 4, live: bool = True) -> dict[str, Any]:
    topics = topics_for_profile(profile, goal)
    query = " OR ".join(topics[:3])
    if live:
        papers = search_arxiv(query, limit=limit)
        models = search_huggingface(" ".join(topics[:2]), limit=limit)
    else:
        seed_papers = SECURITY_SEED_PAPERS if _security_topics(topics) else SEED_PAPERS
        papers = [{**item, "cached": False} for item in seed_papers[:limit]]
        models = [] if _security_topics(topics) else [{**item, "cached": False} for item in SEED_MODELS[:limit]]
    return {
        "topics": topics,
        "papers": papers,
        "models": models,
        "sources": SOURCES,
        "live": live,
        "cache_ttl_seconds": DEFAULT_CACHE_TTL_SECONDS,
        "acknowledgement": "Thank you to arXiv for use of its open access interoperability.",
    }
