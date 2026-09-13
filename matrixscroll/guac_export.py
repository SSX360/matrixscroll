"""Export verified commit envelopes to GUAC-compatible JSONL (Phase 3 MVP)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .gate import BUNDLE_INDEX, verify_commit_envelope_for_sha
from .git import _repository_info, repo_root

PREDICATE_TYPE = "https://matrixscroll.com/attestation/commit-envelope/v1"


def _load_bundle_index(bundle_dir: Path) -> dict[str, Any]:
    index_path = bundle_dir / BUNDLE_INDEX
    if not index_path.is_file():
        raise FileNotFoundError(f"bundle index missing: {index_path}")
    return json.loads(index_path.read_text(encoding="utf-8-sig"))


def envelope_to_guac_statement(
    envelope: dict[str, Any],
    *,
    sha: str,
    repo_name: str,
) -> dict[str, Any]:
    """Build one in-toto / GUAC-adjacent attestation object."""
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": PREDICATE_TYPE,
        "subject": [{"name": f"{repo_name}@{sha}", "digest": {"sha1": sha}}],
        "predicate": envelope,
    }


def export_guac_jsonl(
    bundle_dir: Path,
    output: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Verify each envelope in a bundle and write GUAC-ingestible JSONL."""
    root = root or repo_root()
    index = _load_bundle_index(bundle_dir)
    repo_info = index.get("repository") or _repository_info(root)
    repo_name = str(repo_info.get("remote_url") or repo_info.get("root") or "unknown")

    commits = index.get("commits") or []
    exported: list[str] = []
    skipped: list[dict[str, str]] = []

    lines: list[str] = []
    for sha in commits:
        path = bundle_dir / f"{sha}.json"
        if not path.is_file():
            skipped.append({"sha": sha, "error": "envelope file missing"})
            continue
        envelope = json.loads(path.read_text(encoding="utf-8-sig"))
        result = verify_commit_envelope_for_sha(envelope, sha, root=root)
        if not result.ok:
            skipped.append({"sha": sha, "error": result.error or "verification failed"})
            continue
        statement = envelope_to_guac_statement(envelope, sha=sha, repo_name=repo_name)
        lines.append(json.dumps(statement, sort_keys=True, separators=(",", ":")))
        exported.append(sha)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    return {
        "ok": len(skipped) == 0,
        "schema": "matrixscroll.guac_export.v1",
        "output": str(output),
        "exported": len(exported),
        "skipped": skipped,
        "commits": exported,
    }
