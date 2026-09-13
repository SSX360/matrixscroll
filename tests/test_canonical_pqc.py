"""Canonical encoding tests including PQC overlay rules."""

from __future__ import annotations

from matrixscroll.canonical import canonical_bytes, canonical_bytes_pqc


def test_pqc_canonical_ignores_pqc_signatures_key() -> None:
    payload = {
        "schema": "matrixscroll.test.v0",
        "payload": "x",
        "pqc_signatures": [{"schema": "matrixscroll.pqc_signature.v1", "algorithm": "ml-dsa-65"}],
    }
    body_only = canonical_bytes_pqc(payload)
    assert b"pqc_signatures" not in body_only
    assert b"payload" in body_only
