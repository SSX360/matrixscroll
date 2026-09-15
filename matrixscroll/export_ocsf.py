"""Export a Matrix Scroll envelope as an OCSF-ish event dict.

This is a field mapping helper for SIEM ingestion experiments. It is not an
OCSF certification claim and does not assign a registry-approved ``class_uid``.
"""

from __future__ import annotations

from typing import Any

# Placeholder until an organisation maps Matrix Scroll events into a registered
# OCSF class. Keep the value stable for golden tests.
OCSF_CLASS_UID_PLACEHOLDER = 6001999


def envelope_to_ocsf(envelope: dict[str, Any]) -> dict[str, Any]:
    """Convert a commit or action envelope into an OCSF-shaped dict."""
    block = envelope.get("signature") or {}
    provenance = envelope.get("provenance") or {}
    actor_type = provenance.get("actor_type") or "unknown"
    tool = provenance.get("tool") or "unknown"
    signed_at = block.get("signed_at")
    activity = envelope.get("action_type") or envelope.get("schema") or "sign"

    return {
        "class_uid": OCSF_CLASS_UID_PLACEHOLDER,
        "class_name": "Matrix Scroll Envelope",
        "activity_name": str(activity),
        "activity_id": 1,
        "severity": 1,
        "status": "Success" if block.get("value") else "Unknown",
        "time": signed_at,
        "actor": {
            "user": {
                "type": actor_type,
                "name": tool,
            },
            "app_name": tool,
        },
        "metadata": {
            "product": {
                "name": "matrixscroll",
                "vendor_name": "SSX360",
            },
            "version": "1.0.0",
            "uid": block.get("device_id"),
        },
        "unmapped": {
            "schema": envelope.get("schema"),
            "algorithm": block.get("algorithm"),
            "mode": block.get("mode"),
            "public_key": block.get("public_key"),
        },
    }
