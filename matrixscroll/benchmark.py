"""Product benchmark signals for Digital Rain."""

from __future__ import annotations

from typing import Any


OPENHUMAN_SOURCES = [
    "https://github.com/tinyhumansai/openhuman",
    "https://tinyhumans.gitbook.io",
]


def openhuman_benchmark(profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a concise competitive benchmark against OpenHuman.

    This is intentionally product-facing rather than adversarial. It turns a
    broad personal-AI benchmark into concrete Digital Rain build priorities.
    """
    profile = profile or {}
    stack = ", ".join((profile.get("frameworks") or []) + (profile.get("languages") or [])) or "project"
    notebooks = profile.get("notebooks") or []
    notebook_risk = any(nb.get("execution_health") == "out_of_order" for nb in notebooks)
    readiness = (profile.get("launch_readiness") or {}).get("status", "unknown")

    advantages = [
        {
            "title": "Project-first intelligence",
            "status": "shipping",
            "detail": f"Digital Rain starts with concrete repo signals for {stack}, command safety, notebooks, and local trust posture.",
        },
        {
            "title": "No managed integration dependency",
            "status": "shipping",
            "detail": "Core scans, brainstorm, vault search, diagnostics, and ecosystem ranking work locally or from public repo metrics.",
        },
        {
            "title": "Verifiable release evidence",
            "status": "shipping",
            "detail": "The Matrix Scroll identity layer signs release manifests, giving Digital Rain a provenance angle personal assistants usually lack.",
        },
        {
            "title": "OSS ecosystem radar",
            "status": "shipping",
            "detail": "Recommendations combine local stack fit with OSSInsight/GitHub-style ecosystem signals for MCPs, skills, and repos.",
        },
    ]

    gaps = [
        {
            "title": "Connector auto-fetch",
            "status": "next",
            "detail": "OpenHuman positions around 118+ integrations and scheduled sync. Digital Rain should add opt-in local connector snapshots before adding any managed bridge.",
        },
        {
            "title": "Durable memory tree",
            "status": "next",
            "detail": "Digital Rain has vault search today. The next step is a project memory tree that summarizes scans, decisions, release evidence, and notes into editable Markdown.",
        },
        {
            "title": "Token compression",
            "status": "next",
            "detail": "Add deterministic context packs that dedupe scanner output, docs, vault notes, and ecosystem evidence before LLM calls.",
        },
        {
            "title": "Ambient companion workflow",
            "status": "later",
            "detail": "The companion should surface project alerts, benchmark gaps, and release-readiness events without pretending to be a general personal assistant.",
        },
    ]

    next_moves = [
        "Build a local project memory tree under the configured vault.",
        "Add connector snapshots for GitHub issues/PRs, local git history, and calendar-free project milestones before broad OAuth.",
        "Create a context-pack compressor with visible token savings and source retention.",
        "Turn release evidence into a first-class dashboard timeline.",
    ]
    if notebook_risk:
        next_moves.insert(0, "Resolve out-of-order notebook state before using notebook findings as durable memory.")
    if readiness != "ready":
        next_moves.insert(0, "Clear launch readiness blockers before expanding integration surface.")

    return {
        "benchmark": "OpenHuman",
        "positioning": "Digital Rain should beat broad personal-AI tools by being the deeper, local-first project intelligence and provenance system.",
        "sources": OPENHUMAN_SOURCES,
        "advantages": advantages,
        "gaps": gaps,
        "next_moves": next_moves[:5],
    }
