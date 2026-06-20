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


def test_yubikey_sign_raises_in_prototype(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MODULE", "/nonexistent/ykcs11.so")
    provider = YubiKeyProvider()
    with pytest.raises(Exception):
        provider.sign(b"test")


def test_get_provider_selects_yubikey_mode(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("MATRIXSCROLL_MODE", "yubikey")
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "ms"))
    monkeypatch.setenv("MATRIXSCROLL_YKCS11_MODULE", "/nonexistent/ykcs11.so")
    from matrixscroll.providers.registry import get_provider

    get_provider(refresh=True)
    provider = get_provider()
    assert provider.mode == "yubikey"
