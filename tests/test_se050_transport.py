"""Tests for SE050 mock transport and hardware provider scaffold."""

from __future__ import annotations

import pytest

from matrixscroll.manifest import sign_manifest, verify_manifest
from matrixscroll.providers.hardware import HardwareProvider
from matrixscroll.providers.registry import get_provider
from matrixscroll.providers.se050_transport import MockSE050Transport, open_transport


def test_mock_transport_sign_and_verify():
    transport = MockSE050Transport()
    assert transport.ping()
    message = b"canonical manifest bytes"
    signature = transport.sign(message)
    assert len(signature) == 64
    assert len(transport.public_key_bytes()) == 32


def test_open_transport_without_mock_returns_none(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MATRIXSCROLL_SE050_MOCK", raising=False)
    assert open_transport() is None


def test_hardware_provider_mock_sign(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "ms"))
    monkeypatch.setenv("MATRIXSCROLL_MODE", "hardware")
    monkeypatch.setenv("MATRIXSCROLL_SE050_MOCK", "1")
    import matrixscroll._core as core

    core._PROVIDER = None
    provider = get_provider(refresh=True)
    assert provider.mode == "hardware"
    available, reason = provider.is_available()
    assert available, reason
    manifest = {"schema": "matrixscroll.test.v1", "payload": "se050-mock"}
    signed = sign_manifest(manifest, provider)
    assert signed["signature"]["mode"] == "hardware"
    assert verify_manifest(signed)


def test_hardware_provider_unavailable_without_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MATRIXSCROLL_SE050_MOCK", raising=False)
    provider = HardwareProvider()
    available, reason = provider.is_available()
    assert not available
    assert reason is not None
