"""Tests for the experimental YubiKey provider boundary."""

from __future__ import annotations

import os

import pytest

from matrixscroll.providers.yubikey import YubiKeyProvider


def test_yubikey_provider_unavailable_without_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MODULE", "/nonexistent/ykcs11.so")
    provider = YubiKeyProvider()
    available, reason = provider.is_available()
    assert not available
    assert reason is not None
    assert "disabled in the public SDK" in reason


def test_yubikey_sign_raises_without_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MODULE", "/nonexistent/ykcs11.so")
    provider = YubiKeyProvider()
    with pytest.raises(Exception):
        provider.sign(b"test")


def test_yubikey_mock_provider_is_available_only_with_experimental_flag(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MOCK", "1")
    monkeypatch.setenv("MATRIXSCROLL_ENABLE_EXPERIMENTAL_PIV", "1")
    provider = YubiKeyProvider()
    available, reason = provider.is_available()
    assert available
    assert reason is None


def test_sign_manifest_rejects_non_ed25519_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_MODE", "yubikey")
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MOCK", "1")
    monkeypatch.setenv("MATRIXSCROLL_ENABLE_EXPERIMENTAL_PIV", "1")
    from matrixscroll.manifest import sign_manifest
    from matrixscroll.providers.registry import get_provider

    provider = get_provider(refresh=True)
    manifest = {"schema": "matrixscroll.test.v1", "payload": "yubikey-demo"}
    with pytest.raises(Exception):
        sign_manifest(manifest, provider)


def test_yubikey_mock_public_key_bytes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MOCK", "1")
    monkeypatch.setenv("MATRIXSCROLL_ENABLE_EXPERIMENTAL_PIV", "1")
    provider = YubiKeyProvider()
    pub = provider.public_key_bytes()
    assert len(pub) > 0
    pub2 = provider.public_key_bytes()
    assert pub == pub2


def test_get_provider_selects_yubikey_mode(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("MATRIXSCROLL_MODE", "yubikey")
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "ms"))
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MODULE", "/nonexistent/ykcs11.so")
    from matrixscroll.providers.registry import get_provider

    get_provider(refresh=True)
    provider = get_provider()
    assert provider.mode == "yubikey"
