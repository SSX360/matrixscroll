"""Market and launch-platform radar for Digital Rain.

This module treats product directories and communities as public market-signal
sources. It does not submit, install, clone, or upload local project contents.
"""

from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any

import requests

CACHE_DIR = Path(os.environ.get("DIGITAL_RAIN_CACHE_DIR", Path.home() / ".digital-rain" / "cache"))
DEFAULT_CACHE_TTL_SECONDS = int(os.environ.get("MARKET_RADAR_CACHE_TTL", str(6 * 60 * 60)))
HN_API_BASE = os.environ.get("HN_API_BASE", "https://hacker-news.firebaseio.com/v0")

SOURCE_DEFS: dict[str, dict[str, str]] = {
    "uneed": {
        "name": "Uneed",
        "url": "https://www.uneed.best/",
        "note": "Launchpad categories, alternatives, tags, and maker-market positioning.",
    },
    "microlaunch": {
        "name": "MicroLaunch",
        "url": "https://microlaunch.net/",
        "note": "Startup launches, leaderboards, deals, ratings, and launch copy.",
    },
    "devhunt": {
        "name": "DevHunt",
        "url": "https://devhunt.org/",
        "note": "Developer-tool launches and dev-focused product positioning.",
    },
    "hackernews": {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/",
        "note": "Developer attention, Show HN/Launch HN examples, comments, and objections.",
    },
    "awesome_web_agents": {
        "name": "Awesome Web Agents",
        "url": "https://github.com/steel-dev/awesome-web-agents",
        "fetch_url": "https://raw.githubusercontent.com/steel-dev/awesome-web-agents/main/README.md",
        "note": "Curated GitHub list for AI web-agent tools, browser automation, and LLM infrastructure.",
    },
}

DEFAULT_SOURCES = tuple(SOURCE_DEFS.keys())

SEED_ITEMS: dict[str, list[dict[str, Any]]] = {
    "uneed": [
        {
            "title": "AI products and productivity launch categories",
            "description": "Use product tags, alternatives, and category framing to test whether the use case is already crowded.",
            "url": "https://www.uneed.best/",
            "category": "launch-positioning",
            "tags": ["ai", "productivity", "alternatives", "seo"],
            "score": 56,
        }
    ],
    "microlaunch": [
        {
            "title": "Founder launch leaderboard patterns",
            "description": "Compare launch copy, score, product type, and deal mechanics against current indie startup launches.",
            "url": "https://microlaunch.net/",
            "category": "startup-launch",
            "tags": ["launch", "startup", "leaderboard", "deals"],
            "score": 58,
        }
    ],
    "devhunt": [
        {
            "title": "Developer-tool launch positioning",
            "description": "Use dev-tool launches to find packaging, open-source, and technical validation patterns.",
            "url": "https://devhunt.org/",
            "category": "developer-tools",
            "tags": ["devtools", "open-source", "launch"],
            "score": 60,
        }
    ],
    "hackernews": [
        {
            "title": "Show HN and Launch HN objection mining",
            "description": "Mine discussion patterns for what developers praise, doubt, and ask for before committing to a build.",
            "url": "https://news.ycombinator.com/show",
            "category": "developer-attention",
            "tags": ["show-hn", "launch-hn", "feedback", "sentiment"],
            "score": 62,
        }
    ],
    "awesome_web_agents": [
        {
            "title": "AI web-agent infrastructure map",
            "description": "Curated tools, frameworks, and resources for agents that browse and interact with the web.",
            "url": "https://github.com/steel-dev/awesome-web-agents",
            "category": "web-agent-infrastructure",
            "tags": ["web-agent", "browser", "automation", "scraping", "llm-infrastructure"],
            "score": 68,
        }
    ],
}


def _cache_path(source: str, goal: str) -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in goal.lower())[:80] or "general"
    return CACHE_DIR / f"market__{source}__{safe}.json"


def _read_cache(source: str, goal: str, ttl_seconds: int) -> dict[str, Any] | None:
    path = _cache_path(source, goal)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    age = time.time() - float(data.get("cached_at", 0))
    if age > ttl_seconds:
        return None
    if not isinstance(data.get("items"), list):
        return None
    return {
        "items": data["items"],
        "cached_at": data.get("cached_at"),
        "cache_age_seconds": int(age),
    }


def _write_cache(source: str, goal: str, items: list[dict[str, Any]]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(source, goal).write_text(
            json.dumps({"cached_at": time.time(), "items": items}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _headers() -> dict[str, str]:
    return {
        "Accept": "text/html,application/json",
        "User-Agent": "Digital-Rain/1.0 market-radar",
    }


def _terms(goal: str) -> list[str]:
    terms = re.findall(r"[a-z0-9][a-z0-9+\-.]{2,}", goal.lower())
    stop = {"with", "from", "that", "this", "into", "build", "tool", "tools", "using", "make"}
    return [t for t in terms if t not in stop][:10]


def _text_lines(markup: str) -> list[str]:
    markup = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", markup)
    markup = re.sub(r"(?i)<br\s*/?>", "\n", markup)
    markup = re.sub(r"(?i)</(p|div|li|h[1-6]|a|td|tr)>", "\n", markup)
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup))
    return [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if len(line.strip()) > 2]


def _anchors(markup: str, base_url: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for href, body in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', markup):
        title = " ".join(_text_lines(body))[:140]
        if not title:
            continue
        url = urllib.parse.urljoin(base_url, html.unescape(href))
        if url.startswith("mailto:") or url.startswith("#"):
            continue
        out.append((title, url))
    return out


def _line_score(title: str, desc: str, goal: str, source: str) -> int:
    haystack = f"{title} {desc}".lower()
    matched = sum(1 for term in _terms(goal) if term in haystack)
    score = 38 + matched * 11
    if any(word in haystack for word in ("ai", "agent", "developer", "dev", "launch", "open-source", "github")):
        score += 8
    if source == "hackernews" and any(prefix in haystack for prefix in ("show hn", "launch hn", "ask hn")):
        score += 12
    return min(100, score)


def _normalize_item(source: str, item: dict[str, Any], goal: str, cached: bool = False) -> dict[str, Any]:
    source_def = SOURCE_DEFS[source]
    title = str(item.get("title") or source_def["name"]).strip()
    desc = str(item.get("description") or item.get("text") or source_def["note"]).strip()
    score = int(item.get("score") or _line_score(title, desc, goal, source))
    return {
        "source": source,
        "source_name": source_def["name"],
        "title": title[:180],
        "description": desc[:280],
        "url": item.get("url") or source_def["url"],
        "category": item.get("category") or source_def["note"].split(",", 1)[0].lower(),
        "tags": list(item.get("tags") or []),
        "score": max(0, min(100, score)),
        "metrics": dict(item.get("metrics") or {}),
        "evidence": item.get("evidence") or desc[:160],
        "cached": cached,
    }


def _fetch_directory_source(source: str, goal: str, limit: int) -> list[dict[str, Any]]:
    source_def = SOURCE_DEFS[source]
    url = source_def["url"]
    fetch_url = source_def.get("fetch_url", url)
    resp = requests.get(fetch_url, timeout=7, headers=_headers())
    resp.raise_for_status()
    markup = resp.text
    lines = _markdown_lines(markup) if fetch_url.endswith(".md") else _text_lines(markup)
    anchors = _markdown_links(markup, url) if fetch_url.endswith(".md") else _anchors(markup, url)
    terms = _terms(goal)
    candidates: list[dict[str, Any]] = []

    for title, href in anchors[:80]:
        low = title.lower()
        if terms and not any(term in low for term in terms):
            if not any(marker in low for marker in ("ai", "agent", "developer", "startup", "tool", "launch")):
                continue
        candidates.append({
            "title": title,
            "description": source_def["note"],
            "url": href,
            "category": "product-signal",
            "tags": [t for t in terms if t in low][:4],
        })

    for idx, line in enumerate(lines[:260]):
        low = line.lower()
        if terms and not any(term in low for term in terms):
            if not any(marker in low for marker in ("ai", "agent", "developer", "startup", "tool", "launch", "alternative")):
                continue
        desc = " ".join(lines[idx + 1:idx + 3])[:240] or source_def["note"]
        candidates.append({
            "title": line[:140],
            "description": desc,
            "url": url,
            "category": "market-copy",
            "tags": [t for t in terms if t in low][:4],
        })

    if not candidates:
        candidates = SEED_ITEMS[source]
    normalized = [_normalize_item(source, item, goal) for item in candidates]
    normalized.sort(key=lambda item: item["score"], reverse=True)
    return normalized[:limit]


def _markdown_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip().lstrip("#-*0123456789. ").strip()
        if not line or line.startswith("<!--"):
            continue
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) > 2:
            lines.append(line)
    return lines


def _markdown_links(markdown: str, base_url: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for title, href in re.findall(r"\[([^\]]{2,120})\]\((https?://[^)]+)\)", markdown):
        if "img.shields.io" in href or "github.com/sponsors" in href:
            continue
        out.append((html.unescape(title.strip()), urllib.parse.urljoin(base_url, href.strip())))
    return out


def _fetch_hackernews(goal: str, limit: int) -> list[dict[str, Any]]:
    story_lists = ("topstories", "showstories", "newstories")
    ids: list[int] = []
    for list_name in story_lists:
        resp = requests.get(f"{HN_API_BASE}/{list_name}.json", timeout=6, headers={"User-Agent": "Digital-Rain"})
        resp.raise_for_status()
        raw = resp.json()
        if isinstance(raw, list):
            ids.extend(int(v) for v in raw[:35] if isinstance(v, int))

    seen: set[int] = set()
    rows: list[dict[str, Any]] = []
    terms = _terms(goal)
    for item_id in ids:
        if item_id in seen:
            continue
        seen.add(item_id)
        resp = requests.get(f"{HN_API_BASE}/item/{item_id}.json", timeout=5, headers={"User-Agent": "Digital-Rain"})
        if not resp.ok:
            continue
        item = resp.json()
        if not isinstance(item, dict) or item.get("type") != "story":
            continue
        title = html.unescape(str(item.get("title") or "HN story"))
        text = html.unescape(re.sub(r"<[^>]+>", " ", str(item.get("text") or "")))
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        haystack = f"{title} {text} {url}".lower()
        if terms and not any(term in haystack for term in terms):
            if not (
                any(marker in haystack for marker in ("show hn", "launch hn", "ask hn"))
                and any(signal in haystack for signal in ("agent", "ai", "developer", "github", "browser", "scrap", "automation"))
            ):
                continue
        score = min(100, 36 + int(item.get("score") or 0) // 12 + int(item.get("descendants") or 0) // 20)
        rows.append(_normalize_item("hackernews", {
            "title": title,
            "description": text[:220] or "HN story/comment thread can expose developer sentiment and objections.",
            "url": url,
            "category": "developer-discussion",
            "tags": [t for t in terms if t in haystack][:4],
            "score": score,
            "metrics": {
                "hn_score": int(item.get("score") or 0),
                "comments": int(item.get("descendants") or 0),
                "item_id": item_id,
            },
            "evidence": f"{item.get('score', 0)} points · {item.get('descendants', 0)} comments",
        }, goal))
        if len(rows) >= limit:
            break
    return rows or [_normalize_item("hackernews", item, goal) for item in SEED_ITEMS["hackernews"][:limit]]


def _fetch_source(source: str, goal: str, limit: int) -> list[dict[str, Any]]:
    if source == "hackernews":
        return _fetch_hackernews(goal, limit)
    return _fetch_directory_source(source, goal, limit)


def scan_market(
    goal: str = "",
    sources: list[str] | tuple[str, ...] | None = None,
    limit: int = 8,
    live: bool = True,
    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
) -> dict[str, Any]:
    selected = [s for s in (sources or DEFAULT_SOURCES) if s in SOURCE_DEFS]
    goal = goal.strip() or "AI developer tool launch"
    items: list[dict[str, Any]] = []
    status: dict[str, dict[str, Any]] = {}

    for source in selected:
        cached = _read_cache(source, goal, ttl_seconds) if live else None
        if cached is not None:
            source_items = [_normalize_item(source, item, goal, cached=True) for item in cached["items"][:limit]]
            status[source] = {
                "ok": True,
                "source": SOURCE_DEFS[source]["url"],
                "cached": True,
                "cache_age_seconds": cached["cache_age_seconds"],
                "item_count": len(source_items),
            }
            items.extend(source_items)
            continue

        if not live:
            source_items = [_normalize_item(source, item, goal) for item in SEED_ITEMS[source][:limit]]
            status[source] = {"ok": True, "source": SOURCE_DEFS[source]["url"], "cached": False, "seed": True, "item_count": len(source_items)}
            items.extend(source_items)
            continue

        try:
            source_items = _fetch_source(source, goal, limit)
            _write_cache(source, goal, source_items)
            status[source] = {"ok": True, "source": SOURCE_DEFS[source]["url"], "cached": False, "item_count": len(source_items)}
            items.extend(source_items)
        except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError) as exc:
            source_items = [_normalize_item(source, item, goal) for item in SEED_ITEMS[source][:limit]]
            status[source] = {
                "ok": False,
                "source": SOURCE_DEFS[source]["url"],
                "cached": False,
                "fallback": "seed",
                "error": str(exc)[:180],
                "item_count": len(source_items),
            }
            items.extend(source_items)

    items.sort(key=lambda item: item["score"], reverse=True)
    return {
        "goal": goal,
        "items": items[:limit],
        "source_status": status,
        "sources": [SOURCE_DEFS[s]["url"] for s in selected],
        "live": live,
        "cache_ttl_seconds": ttl_seconds,
    }
