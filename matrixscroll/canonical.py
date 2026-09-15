"""Deterministic canonical JSON encoding for Matrix Scroll manifests."""

from __future__ import annotations

import json
from typing import Any

# Signature blocks and post-hoc informational fields are excluded from the
# Ed25519 / PQC signing input so overlays (timestamp, receipt, pqc) can attach
# without invalidating an existing signature.
_SIGNATURE_KEYS = frozenset({"signature", "pqc_signatures"})
_INFORMATIONAL_KEYS = frozenset({"timestamp", "receipt"})
_EXCLUDE_FROM_SIGNING = _SIGNATURE_KEYS | _INFORMATIONAL_KEYS


def _canonical_body(payload: dict[str, Any], *, exclude_pqc: bool) -> dict[str, Any]:
    if exclude_pqc:
        return {k: v for k, v in payload.items() if k not in _EXCLUDE_FROM_SIGNING}
    return {k: v for k, v in payload.items() if k != "signature"}


def _encode(body: dict[str, Any]) -> bytes:
    return json.dumps(
        body,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    """Return deterministic signing bytes per SPEC.md section 4 (Ed25519 v1).

    Excludes ``signature``, optional ``pqc_signatures``, and informational
    ``timestamp`` / ``receipt`` fields so post-hoc overlays stay compatible.
    """
    return _encode(_canonical_body(payload, exclude_pqc=True))


def canonical_bytes_pqc(payload: dict[str, Any]) -> bytes:
    """Return signing bytes for PQC overlay (§11) — excludes signature and pqc_signatures."""
    return _encode(_canonical_body(payload, exclude_pqc=True))
