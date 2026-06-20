"""Rekor publish stub — dry-run artifacts and optional rekor-cli integration (Phase 3 MVP)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .canonical import canonical_bytes
from .gate import BUNDLE_INDEX, verify_commit_envelope_for_sha

REKOR_API = "rekor/v2"


def _artifact_digest(envelope: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(envelope)).hexdigest()


def build_rekor_entry(envelope: dict[str, Any], *, sha: str) -> dict[str, Any]:
    """Build a Rekor-shaped entry for local inspection (dry-run)."""
    block = envelope.get("signature") or {}
    provenance = envelope.get("provenance") or {}
    digest = _artifact_digest(envelope)
    return {
        "apiVersion": REKOR_API,
        "kind": "hashedrekord",
        "spec": {
            "data": {
                "hash": {"algorithm": "sha256", "value": digest},
                "content": envelope,
            },
            "signature": {
                "content": block.get("signature"),
                "publicKey": {"content": block.get("public_key")},
            },
            "annotations": {
                "commit_sha": sha,
                "device_id": block.get("device_id"),
                "actor_type": provenance.get("actor_type"),
                "tool": provenance.get("tool"),
                "matrixscroll_schema": envelope.get("schema"),
            },
        },
    }


def publish_rekor_dry_run(
    bundle_dir: Path,
    output_dir: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Write Rekor-shaped JSON artifacts locally without network upload."""
    root = root or repo_root()
    index_path = bundle_dir / BUNDLE_INDEX
    if not index_path.is_file():
        raise FileNotFoundError(f"bundle index missing: {index_path}")
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    commits = index.get("commits") or []

    output_dir.mkdir(parents=True, exist_ok=True)
    entries: list[str] = []
    skipped: list[dict[str, str]] = []

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
        entry = build_rekor_entry(envelope, sha=sha)
        out_path = output_dir / f"{sha}.rekor.json"
        out_path.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        entries.append(sha)

    manifest = {
        "schema": "matrixscroll.rekor_dry_run.v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": entries,
        "skipped": skipped,
        "output_dir": str(output_dir),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**manifest, "ok": len(skipped) == 0}


def publish_rekor_cli(
    bundle_dir: Path,
    *,
    rekor_url: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Upload verified envelopes via ``rekor-cli`` when installed and REKOR_URL is set."""
    if shutil.which("rekor-cli") is None:
        raise RuntimeError("rekor-cli not found on PATH")
    url = rekor_url or os.environ.get("REKOR_URL", "").strip()
    if not url:
        raise RuntimeError("REKOR_URL not set")

    dry = publish_rekor_dry_run(bundle_dir, bundle_dir / ".rekor-staging", root=root)
    uploaded: list[str] = []
    for sha in dry.get("entries") or []:
        artifact = bundle_dir / f"{sha}.json"
        cmd = [
            "rekor-cli",
            "upload",
            "--rekor_server",
            url,
            "--artifact",
            str(artifact),
            "--type",
            "hashedrekord",
            "--annotation",
            f"commit_sha={sha}",
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        uploaded.append(sha)

    return {"ok": True, "uploaded": uploaded, "rekor_url": url}
