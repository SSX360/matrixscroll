"""Tests for signed agent trace envelopes."""

from __future__ import annotations

import json
from pathlib import Path

from matrixscroll.agent_trace import (
    sign_agent_trace,
    summarize_agent_trace,
    verify_agent_trace,
)


def test_sign_and_verify_agent_trace(tmp_path: Path) -> None:
    trace = tmp_path / "run-abc.jsonl"
    trace.write_text(
        "\n".join(
            [
                json.dumps({"ts": 1, "runId": "run-abc", "step": 0, "note": "start"}),
                json.dumps({"ts": 2, "runId": "run-abc", "step": 1, "note": "click"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    summary = summarize_agent_trace(trace)
    assert summary["run_id"] == "run-abc"
    assert summary["step_count"] == 2
    assert summary["trace_sha256"].startswith("sha256:")

    signed = sign_agent_trace(trace)
    assert signed["ok"] is True
    envelope_path = Path(signed["path"])
    assert envelope_path.is_file()

    ok = verify_agent_trace(envelope_path, trace_path=trace)
    assert ok["ok"] is True
    assert ok["run_id"] == "run-abc"
    assert ok["step_count"] == 2


def test_verify_detects_trace_drift(tmp_path: Path) -> None:
    trace = tmp_path / "run-drift.jsonl"
    trace.write_text(json.dumps({"ts": 1, "runId": "run-drift", "step": 0}) + "\n", encoding="utf-8")
    signed = sign_agent_trace(trace)
    envelope_path = Path(signed["path"])

    trace.write_text(
        json.dumps({"ts": 1, "runId": "run-drift", "step": 0, "note": "mutated"}) + "\n",
        encoding="utf-8",
    )
    result = verify_agent_trace(envelope_path, trace_path=trace)
    assert result["ok"] is False
    assert result["error"] == "trace_drift"
