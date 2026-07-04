"""Signed agent run traces (JSONL) for WEB_WIZARD and browser agents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .manifest import sign_manifest, verify_manifest

AGENT_TRACE_SCHEMA = "matrixscroll.agent_trace.v1"


def _read_trace_lines(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    entries: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            entries.append(obj)
    return entries


def summarize_agent_trace(trace_path: Path | str) -> dict[str, Any]:
    """Build an unsigned agent-trace envelope body from a `.jsonl` run log."""
    path = Path(trace_path).expanduser().resolve()
    raw = path.read_bytes()
    entries = _read_trace_lines(path)
    run_id = ""
    if entries:
        run_id = str(entries[0].get("runId") or entries[0].get("run_id") or "")
    timestamps = [e.get("ts") for e in entries if isinstance(e.get("ts"), (int, float))]
    return {
        "schema": AGENT_TRACE_SCHEMA,
        "run_id": run_id,
        "trace_file": path.name,
        "step_count": len(entries),
        "trace_sha256": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "first_ts": min(timestamps) if timestamps else None,
        "last_ts": max(timestamps) if timestamps else None,
    }


def sign_agent_trace(
    trace_path: Path | str,
    *,
    envelope_path: Path | str | None = None,
) -> dict[str, Any]:
    """Sign a JSONL agent trace; optionally write `<trace>.envelope.json`."""
    body = summarize_agent_trace(trace_path)
    signed = sign_manifest(body)
    if envelope_path is not None:
        out = Path(envelope_path).expanduser()
    else:
        out = Path(trace_path).expanduser().with_suffix(".envelope.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(signed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "signed": signed, "path": str(out)}


def verify_agent_trace(
    envelope: dict[str, Any] | Path | str,
    *,
    trace_path: Path | str | None = None,
) -> dict[str, Any]:
    """Verify envelope signature; optionally confirm trace file matches recorded hash."""
    if not isinstance(envelope, dict):
        path = Path(envelope).expanduser()
        envelope = json.loads(path.read_text(encoding="utf-8-sig"))
    if envelope.get("schema") != AGENT_TRACE_SCHEMA:
        return {"ok": False, "error": "invalid_schema", "message": "expected matrixscroll.agent_trace.v1"}
    if not verify_manifest(envelope):
        return {"ok": False, "error": "invalid_signature", "message": "Ed25519 verification failed"}
    if trace_path is not None:
        summary = summarize_agent_trace(trace_path)
        expected = envelope.get("trace_sha256")
        actual = summary.get("trace_sha256")
        if expected != actual:
            return {
                "ok": False,
                "error": "trace_drift",
                "message": "trace file bytes do not match signed envelope",
                "expected": expected,
                "actual": actual,
            }
    return {"ok": True, "run_id": envelope.get("run_id"), "step_count": envelope.get("step_count")}
