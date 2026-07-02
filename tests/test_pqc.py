"""Tests for post-quantum overlay (ML-DSA / SLH-DSA)."""

from __future__ import annotations

import json
import os

import pytest

from matrixscroll.canonical import canonical_bytes, canonical_bytes_pqc
from matrixscroll.constants import DEFAULT_PQC_ALGORITHM
from matrixscroll.crypto_backend import pqc_available
from matrixscroll.manifest import (
    sign_manifest,
    sign_manifest_with_pqc,
    verify_manifest,
    verify_manifest_full,
    verify_manifest_pqc,
)
from matrixscroll.policy import VerifyPolicy, verify_manifest_with_policy
from matrixscroll.errors import IdentityError
from matrixscroll.pqc import attach_pqc_overlay, configured_pqc_algorithm

pytestmark = pytest.mark.skipif(not pqc_available(), reason="liboqs PQC backend not installed")


@pytest.fixture(autouse=True)
def _enable_pqc_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_PQC", DEFAULT_PQC_ALGORITHM)


@pytest.fixture
def simple_manifest() -> dict:
    return {"schema": "matrixscroll.test.v0", "payload": "hello-pqc"}


@pytest.fixture
def signed_manifest(simple_manifest: dict) -> dict:
    return sign_manifest(simple_manifest)


def test_canonical_pqc_excludes_signature_blocks(signed_manifest: dict) -> None:
    ed25519_bytes = canonical_bytes(signed_manifest)
    overlay = attach_pqc_overlay(signed_manifest, DEFAULT_PQC_ALGORITHM)
    pqc_bytes = canonical_bytes_pqc(overlay)
    assert ed25519_bytes == pqc_bytes


def test_sign_and_verify_pqc_overlay(signed_manifest: dict) -> None:
    overlay = attach_pqc_overlay(signed_manifest, DEFAULT_PQC_ALGORITHM)
    assert verify_manifest(overlay)
    assert verify_manifest_pqc(overlay)
    assert verify_manifest_full(overlay)


def test_sign_manifest_with_pqc_env(simple_manifest: dict) -> None:
    signed = sign_manifest_with_pqc(simple_manifest)
    assert "pqc_signatures" in signed
    assert signed["pqc_signatures"][0]["algorithm"] == DEFAULT_PQC_ALGORITHM
    assert verify_manifest_full(signed)


def test_hardware_mode_rejects_pqc_overlay(signed_manifest: dict) -> None:
    hardware_like = json.loads(json.dumps(signed_manifest))
    hardware_like["signature"]["mode"] = "hardware"
    with pytest.raises(IdentityError):
        attach_pqc_overlay(hardware_like, DEFAULT_PQC_ALGORITHM)


def test_policy_require_pqc_emulated_only(signed_manifest: dict) -> None:
    policy = VerifyPolicy(require_pqc="emulated_only")
    ok, reason = verify_manifest_with_policy(signed_manifest, policy)
    assert not ok
    assert reason and "pqc" in reason.lower()

    overlay = attach_pqc_overlay(signed_manifest, DEFAULT_PQC_ALGORITHM)
    ok, reason = verify_manifest_with_policy(overlay, policy)
    assert ok, reason


def test_policy_hardware_exempt_from_require_pqc(signed_manifest: dict) -> None:
    hardware_like = json.loads(json.dumps(signed_manifest))
    hardware_like["signature"]["mode"] = "hardware"
    policy = VerifyPolicy(require_pqc="true")
    ok, reason = verify_manifest_with_policy(hardware_like, policy)
    assert ok, reason


def test_tampered_pqc_fails(signed_manifest: dict) -> None:
    overlay = attach_pqc_overlay(signed_manifest, DEFAULT_PQC_ALGORITHM)
    overlay["pqc_signatures"][0]["value"] = "AAAA"
    assert not verify_manifest_pqc(overlay)
    assert not verify_manifest_full(overlay)


def test_configured_pqc_algorithm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_PQC", "ml-dsa-44")
    assert configured_pqc_algorithm() == "ml-dsa-44"
    monkeypatch.setenv("MATRIXSCROLL_PQC", "off")
    assert configured_pqc_algorithm() is None
