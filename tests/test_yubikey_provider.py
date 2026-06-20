"""Tests for YubiKey provider prototype boundary."""

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


def test_yubikey_sign_raises_without_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MODULE", "/nonexistent/ykcs11.so")
    provider = YubiKeyProvider()
    with pytest.raises(Exception):
        provider.sign(b"test")


def test_yubikey_mock_sign_and_verify(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_MODE", "yubikey")
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MOCK", "1")
    from matrixscroll.manifest import sign_manifest, verify_manifest
    from matrixscroll.providers.registry import get_provider

    provider = get_provider(refresh=True)
    manifest = {"schema": "matrixscroll.test.v1", "payload": "yubikey-demo"}
    signed = sign_manifest(manifest, provider)
    assert signed["signature"]["algorithm"] == "ecdsa-p256"
    assert signed["signature"]["mode"] == "yubikey"
    assert verify_manifest(signed)


def test_yubikey_mock_public_key_bytes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MOCK", "1")
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
