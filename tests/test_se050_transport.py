"""Tests for SE050 mock transport and hardware provider scaffold."""

from __future__ import annotations

import base64
import json

import pytest

from matrixscroll.manifest import sign_manifest, verify_manifest
from matrixscroll.providers.hardware import HardwareProvider
from matrixscroll.providers.registry import get_provider
from matrixscroll.providers.se050_transport import (
    MockSE050Transport,
    SerialSE050Transport,
    SerialSettings,
    open_transport,
)


class FakeSerial:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self._transport = MockSE050Transport(seed=b"\x42" * 32)
        self._pending = b""

    def write(self, payload: bytes) -> int:
        request = json.loads(payload.decode("utf-8").strip())
        public_key = base64.b64encode(self._transport.public_key_bytes()).decode("ascii")
        cmd = request["cmd"]
        if cmd == "ping":
            response = {"ok": True, "result": "pong", "protocol": "ssx360.se050.poc.v1"}
        elif cmd == "pubkey":
            response = {"ok": True, "public_key": public_key}
        elif cmd == "sign":
            message = base64.b64decode(request["message"].encode("ascii"), validate=True)
            response = {
                "ok": True,
                "public_key": public_key,
                "signature": base64.b64encode(self._transport.sign(message)).decode("ascii"),
            }
        else:
            response = {"ok": False, "error": f"unsupported cmd: {cmd}"}
        self._pending = json.dumps(response, separators=(",", ":")).encode("utf-8") + b"\n"
        return len(payload)

    def flush(self) -> None:
        return None

    def readline(self) -> bytes:
        pending, self._pending = self._pending, b""
        return pending


def test_mock_transport_sign_and_verify():
    transport = MockSE050Transport()
    assert transport.ping()
    message = b"canonical manifest bytes"
    signature = transport.sign(message)
    assert len(signature) == 64
    assert len(transport.public_key_bytes()) == 32


def test_open_transport_without_mock_returns_none(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MATRIXSCROLL_SE050_MOCK", raising=False)
    monkeypatch.delenv("MATRIXSCROLL_SE050_PORT", raising=False)
    assert open_transport() is None


def test_serial_transport_ping_pubkey_and_sign():
    transport = SerialSE050Transport(
        SerialSettings(port="COM77", baudrate=230400, timeout_ms=1500),
        serial_cls=FakeSerial,
    )
    assert transport.ping()
    public_key = transport.public_key_bytes()
    assert len(public_key) == 32
    signature = transport.sign(b"canonical manifest bytes")
    assert len(signature) == 64


def test_open_transport_uses_serial_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MATRIXSCROLL_SE050_MOCK", raising=False)
    monkeypatch.setenv("MATRIXSCROLL_SE050_PORT", "COM99")
    monkeypatch.setenv("MATRIXSCROLL_SE050_BAUD", "230400")
    monkeypatch.setenv("MATRIXSCROLL_SE050_TIMEOUT_MS", "900")
    monkeypatch.setattr(
        "matrixscroll.providers.se050_transport._load_serial_class",
        lambda: FakeSerial,
    )
    transport = open_transport()
    assert isinstance(transport, SerialSE050Transport)
    assert transport.ping()
    assert transport.public_key_bytes() == MockSE050Transport(seed=b"\x42" * 32).public_key_bytes()


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
    monkeypatch.delenv("MATRIXSCROLL_SE050_PORT", raising=False)
    provider = HardwareProvider()
    available, reason = provider.is_available()
    assert not available
    assert reason is not None
