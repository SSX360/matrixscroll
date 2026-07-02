"""Tests for canonical encoding."""

from __future__ import annotations

from matrixscroll.canonical import canonical_bytes


def test_canonical_excludes_signature_block():
    payload = {"b": 2, "a": 1, "signature": {"value": "ignored"}}
    assert canonical_bytes(payload) == b'{"a":1,"b":2}'


def test_canonical_excludes_pqc_signatures_block():
    payload = {
        "b": 2,
        "a": 1,
        "pqc_signatures": [{"algorithm": "ml-dsa-65"}],
    }
    assert canonical_bytes(payload) == b'{"a":1,"b":2}'
