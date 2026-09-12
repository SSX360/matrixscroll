"""Tests for post-quantum overlay (ML-DSA / SLH-DSA)."""

from __future__ import annotations

import json

import pytest

from matrixscroll.canonical import canonical_bytes, canonical_bytes_pqc
from matrixscroll.constants import DEFAULT_PQC_ALGORITHM, PQC_ALGORITHMS
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
from tests._pqc_support import liboqs_family_enabled

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


@pytest.mark.parametrize("algorithm", sorted(PQC_ALGORITHMS))
def test_every_listed_algorithm_signs_and_verifies(
    algorithm: str, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Each identifier in PQC_ALGORITHMS must resolve to an enabled liboqs mechanism,
    generate a key, sign, verify, and reject a tampered signature."""
    import base64

    from matrixscroll.crypto_backend import oqs_mechanism_name
    from matrixscroll.pqc import sign_pqc_block, verify_pqc_block

    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    family = "ML-DSA" if algorithm.startswith("ml-dsa") else "SLH-DSA"
    if not liboqs_family_enabled(family):
        pytest.skip(f"this liboqs build has no {family} mechanisms")
    assert oqs_mechanism_name(algorithm), f"{algorithm} does not resolve to an enabled liboqs mechanism"
    manifest = {"schema": "matrixscroll.test.v0", "payload": f"probe-{algorithm}"}
    block = sign_pqc_block(manifest, algorithm)
    assert block["algorithm"] == algorithm
    assert verify_pqc_block(manifest, block)
    raw = bytearray(base64.b64decode(block["value"]))
    raw[0] ^= 0x01
    tampered = dict(block, value=base64.b64encode(bytes(raw)).decode("ascii"))
    assert not verify_pqc_block(manifest, tampered)


def test_signing_with_a_key_set_this_build_lacks_raises_identity_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """An existing key file naming a set the build does not enable fails through IdentityError,
    the same contract as key generation, not through the backend's ValueError."""
    from matrixscroll import crypto_backend
    from matrixscroll.pqc import sign_pqc_block

    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    manifest = {"schema": "matrixscroll.test.v0", "payload": "probe-missing-set"}
    sign_pqc_block(manifest, "ml-dsa-87")  # writes the key file for ml-dsa-87
    monkeypatch.setitem(crypto_backend._OQS_RESOLVED, "ml-dsa-87", "")  # this build "lacks" it now
    with pytest.raises(IdentityError, match="not enabled in this liboqs build"):
        sign_pqc_block(manifest, "ml-dsa-87")
