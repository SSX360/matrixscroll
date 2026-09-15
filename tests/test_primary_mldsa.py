"""Primary ML-DSA-87 signing (MATRIXSCROLL_PRIMARY_ALG=ml-dsa-87)."""

from __future__ import annotations

import os

import pytest

from matrixscroll.crypto_backend import pqc_available
from matrixscroll.manifest import sign_manifest, verify_manifest

pytestmark = pytest.mark.skipif(
    not pqc_available(),
    reason="matrixscroll[pqc] / liboqs required for ML-DSA primary",
)


def test_ml_dsa_87_primary_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("MATRIXSCROLL_PRIMARY_ALG", "ml-dsa-87")
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "home"))
    signed = sign_manifest({"release": "0.10.0", "note": "primary-mldsa"})
    block = signed["signature"]
    assert block["algorithm"] == "ml-dsa-87"
    assert block["schema"] == "matrixscroll.signature.v1"
    assert verify_manifest(signed) is True
    signed["note"] = "tampered"
    assert verify_manifest(signed) is False


def test_ed25519_default_unchanged(monkeypatch, tmp_path):
    monkeypatch.delenv("MATRIXSCROLL_PRIMARY_ALG", raising=False)
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "home2"))
    signed = sign_manifest({"release": "0.10.0"})
    assert signed["signature"]["algorithm"] == "ed25519"
    assert verify_manifest(signed) is True
