"""Tests for RFC 3161-shaped timestamp helpers."""

from __future__ import annotations

import pytest

from matrixscroll.timestamp import (
    TimestampToken,
    attach_timestamp,
    build_timestamp_request,
    make_dev_token,
    verify_timestamp_structure,
    verify_timestamp_with_root,
)
from matrixscroll.verdict import Verdict


DIGEST = "ab" * 32


def test_build_timestamp_request():
    req = build_timestamp_request(DIGEST)
    assert req["version"] == 1
    assert req["messageImprint"]["hashedMessage"] == DIGEST
    assert req["messageImprint"]["hashAlgorithm"] == "sha256"


def test_build_timestamp_request_rejects_bad_digest():
    with pytest.raises(ValueError):
        build_timestamp_request("deadbeef")


def test_attach_timestamp_copies_envelope():
    env = {"schema": "matrixscroll.commit_envelope.v1", "commit": {"actual_id": "a" * 40}}
    token = make_dev_token(DIGEST)
    out = attach_timestamp(env, token)
    assert "timestamp" in out
    assert "timestamp" not in env
    assert out["timestamp"]["message_imprint"] == DIGEST


def test_verify_timestamp_structure_ok():
    token = make_dev_token(DIGEST)
    assert verify_timestamp_structure(token) is Verdict.CONSISTENT
    assert verify_timestamp_structure(TimestampToken.from_dict(token)) is Verdict.CONSISTENT


def test_verify_timestamp_structure_bad_imprint():
    token = make_dev_token(DIGEST)
    token["message_imprint"] = "zz"
    assert verify_timestamp_structure(token) is Verdict.INCONSISTENT


def test_verify_timestamp_with_root_dev_and_stub():
    token = make_dev_token(DIGEST)
    assert verify_timestamp_with_root(token, None) is Verdict.CONSISTENT
    assert verify_timestamp_with_root(token, "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----") is Verdict.INDETERMINATE
