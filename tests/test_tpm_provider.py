"""Tests for TPM provider prototype boundary."""

from __future__ import annotations

import pytest

from matrixscroll.manifest import sign_manifest, verify_manifest
from matrixscroll.providers.tpm import TpmProvider


def test_tpm_provider_mock_available(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("MATRIXSCROLL_TPM_MOCK", "1")
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "ms"))
    provider = TpmProvider()
    available, reason = provider.is_available()
    assert available
    assert reason is None


def test_tpm_mock_sign_and_verify(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("MATRIXSCROLL_MODE", "tpm")
    monkeypatch.setenv("MATRIXSCROLL_TPM_MOCK", "1")
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "ms"))
    from matrixscroll.providers.registry import get_provider

    provider = get_provider(refresh=True)
    manifest = {"schema": "matrixscroll.test.v1", "payload": "tpm-demo"}
    signed = sign_manifest(manifest, provider)
    assert signed["signature"]["mode"] == "tpm"
    assert verify_manifest(signed)
