"""Deterministic canonical JSON encoding for Matrix Scroll manifests."""

from __future__ import annotations

import json
from typing import Any

_SIGNATURE_KEYS = frozenset({"signature", "pqc_signatures"})


def _canonical_body(payload: dict[str, Any], *, exclude_pqc: bool) -> dict[str, Any]:
    if exclude_pqc:
        return {k: v for k, v in payload.items() if k not in _SIGNATURE_KEYS}
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

    Excludes ``signature`` and optional ``pqc_signatures`` so Ed25519 verification
    stays valid after a v1.1 PQC overlay is attached.
    """
    return _encode(_canonical_body(payload, exclude_pqc=True))


def canonical_bytes_pqc(payload: dict[str, Any]) -> bytes:
    """Return signing bytes for PQC overlay (§11) — excludes signature and pqc_signatures."""
    return _encode(_canonical_body(payload, exclude_pqc=True))
