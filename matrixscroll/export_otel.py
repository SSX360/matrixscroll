"""Export a Matrix Scroll envelope as an OpenTelemetry log-record-shaped dict.

Field names follow the OTel Logs data model at a high level. This is a bridge
helper for observability pipelines, not a claim of OTel SDK conformance.
"""

from __future__ import annotations

from typing import Any


def envelope_to_otel_log_record(envelope: dict[str, Any]) -> dict[str, Any]:
    """Convert an envelope into an OTel log-record-shaped dictionary."""
    block = envelope.get("signature") or {}
    provenance = envelope.get("provenance") or {}
    signed_at = block.get("signed_at") or ""
    body_schema = envelope.get("schema") or "matrixscroll.envelope"

    attributes: dict[str, Any] = {
        "matrixscroll.schema": body_schema,
        "matrixscroll.algorithm": block.get("algorithm"),
        "matrixscroll.mode": block.get("mode"),
        "matrixscroll.device_id": block.get("device_id"),
        "matrixscroll.actor_type": provenance.get("actor_type"),
        "matrixscroll.tool": provenance.get("tool"),
    }
    if envelope.get("action_type"):
        attributes["matrixscroll.action_type"] = envelope["action_type"]
    commit = envelope.get("commit") or {}
    if commit.get("actual_id"):
        attributes["matrixscroll.commit_sha"] = commit["actual_id"]

    return {
        "timeUnixNano": _rfc3339_to_unix_nano(signed_at) if signed_at else None,
        "observedTimeUnixNano": None,
        "severityNumber": 9,  # INFO
        "severityText": "INFO",
        "body": {
            "stringValue": f"matrixscroll envelope {body_schema}",
        },
        "attributes": [
            {"key": key, "value": {"stringValue": str(value)}}
            for key, value in attributes.items()
            if value is not None
        ],
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": "matrixscroll"}},
            ]
        },
    }


def _rfc3339_to_unix_nano(value: str) -> int | None:
    from datetime import datetime

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return int(dt.timestamp() * 1_000_000_000)
