"""Tests for OCSF / OTel envelope export helpers."""

from __future__ import annotations

from matrixscroll.export_ocsf import OCSF_CLASS_UID_PLACEHOLDER, envelope_to_ocsf
from matrixscroll.export_otel import envelope_to_otel_log_record


def _sample_envelope():
    return {
        "schema": "matrixscroll.action_envelope.v1",
        "action_type": "api_call",
        "provenance": {"actor_type": "agent", "tool": "cursor"},
        "signature": {
            "schema": "matrixscroll.signature.v1",
            "algorithm": "ed25519",
            "device_id": "dev1",
            "public_key": "abc",
            "mode": "emulated",
            "signed_at": "2026-09-15T12:00:00Z",
            "value": "sig",
        },
    }


def test_envelope_to_ocsf_shape():
    event = envelope_to_ocsf(_sample_envelope())
    assert event["class_uid"] == OCSF_CLASS_UID_PLACEHOLDER
    assert event["activity_name"] == "api_call"
    assert event["actor"]["user"]["type"] == "agent"
    assert event["time"] == "2026-09-15T12:00:00Z"


def test_envelope_to_otel_log_record_shape():
    record = envelope_to_otel_log_record(_sample_envelope())
    assert record["severityText"] == "INFO"
    assert record["body"]["stringValue"].startswith("matrixscroll envelope")
    keys = {item["key"] for item in record["attributes"]}
    assert "matrixscroll.schema" in keys
    assert "matrixscroll.action_type" in keys
    assert isinstance(record["timeUnixNano"], int)
