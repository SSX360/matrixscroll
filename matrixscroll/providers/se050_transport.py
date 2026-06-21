"""SE050 transport protocol and mock backend (SSX-7 scaffold).

Real device traffic uses newline-delimited JSON over USB CDC ACM:

* ``{"cmd":"ping"}``
* ``{"cmd":"pubkey"}``
* ``{"cmd":"sign","message":"<base64 canonical bytes>"}``

Responses mirror that framing and return ``ok`` plus base64 fields for signing
artifacts. Set ``MATRIXSCROLL_SE050_MOCK=1`` for an in-process Ed25519 stand-in
during development and CI.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ..constants import SEED_LEN

DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT_MS = 3000


class TransportProtocolError(RuntimeError):
    """Raised when the USB CDC protocol returns malformed data."""


class TransportUnavailable(RuntimeError):
    """Raised when a hardware transport cannot be opened or used."""


@dataclass
class SignResponse:
    signature: bytes
    public_key: bytes


@dataclass(frozen=True)
class SerialSettings:
    port: str
    baudrate: int = DEFAULT_BAUDRATE
    timeout_ms: int = DEFAULT_TIMEOUT_MS


class SE050Transport(Protocol):
    """Host-to-secure-element framing for sign and public-key export."""

    def ping(self) -> bool:
        ...

    def public_key_bytes(self) -> bytes:
        ...

    def sign(self, message: bytes) -> bytes:
        ...


class ErrorSE050Transport:
    """Placeholder transport that preserves the reason hardware is unavailable."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def ping(self) -> bool:
        return False

    def public_key_bytes(self) -> bytes:
        raise TransportUnavailable(self.reason)

    def sign(self, message: bytes) -> bytes:
        raise TransportUnavailable(self.reason)


class MockSE050Transport:
    """Software stand-in for SE050 responses (development / CI only)."""

    def __init__(self, seed: bytes | None = None) -> None:
        raw = seed if seed is not None else os.urandom(SEED_LEN)
        if len(raw) < SEED_LEN:
            raw = raw.ljust(SEED_LEN, b"\x00")
        self._private = Ed25519PrivateKey.from_private_bytes(raw[:SEED_LEN])
        self._public = self._private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def ping(self) -> bool:
        return True

    def public_key_bytes(self) -> bytes:
        return self._public

    def sign(self, message: bytes) -> bytes:
        return self._private.sign(message)


class SerialSE050Transport:
    """USB CDC transport for the RP2350 <-> SE050 PoC bridge."""

    protocol = "ssx360.se050.poc.v1"

    def __init__(self, settings: SerialSettings, serial_cls=None) -> None:
        self._settings = settings
        self._public_key: bytes | None = None
        self.reason: str | None = None
        serial_factory = serial_cls or _load_serial_class()
        timeout_seconds = max(settings.timeout_ms, 1) / 1000.0
        try:
            self._serial = serial_factory(
                port=settings.port,
                baudrate=settings.baudrate,
                timeout=timeout_seconds,
                write_timeout=timeout_seconds,
            )
        except Exception as exc:  # pragma: no cover - exercised via open_transport
            raise TransportUnavailable(
                f"could not open SE050 serial transport on {settings.port}: {exc}"
            ) from exc

    def _exchange(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        self._serial.write(request)
        flush = getattr(self._serial, "flush", None)
        if callable(flush):
            flush()
        raw = self._serial.readline()
        if not raw:
            raise TransportProtocolError(
                f"timeout waiting for SE050 response on {self._settings.port}"
            )
        try:
            response = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransportProtocolError(f"invalid JSON from SE050 transport: {exc}") from exc
        if not isinstance(response, dict):
            raise TransportProtocolError("SE050 response must be a JSON object")
        if response.get("ok") is False:
            error = response.get("error")
            detail = str(error) if error else "device returned an unspecified error"
            raise TransportProtocolError(detail)
        return response

    @staticmethod
    def _decode_base64(field: Any, label: str) -> bytes:
        if not isinstance(field, str):
            raise TransportProtocolError(f"{label} missing from SE050 response")
        try:
            return base64.b64decode(field.encode("ascii"), validate=True)
        except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
            raise TransportProtocolError(f"{label} was not valid base64") from exc

    def ping(self) -> bool:
        try:
            response = self._exchange({"cmd": "ping"})
        except TransportProtocolError as exc:
            self.reason = str(exc)
            return False
        self.reason = None
        return response.get("result") == "pong"

    def public_key_bytes(self) -> bytes:
        response = self._exchange({"cmd": "pubkey"})
        public_key = self._decode_base64(response.get("public_key"), "public_key")
        self._public_key = public_key
        return public_key

    def sign(self, message: bytes) -> bytes:
        response = self._exchange(
            {
                "cmd": "sign",
                "message": base64.b64encode(message).decode("ascii"),
            }
        )
        signature = self._decode_base64(response.get("signature"), "signature")
        public_key = response.get("public_key")
        if public_key is not None:
            decoded = self._decode_base64(public_key, "public_key")
            if self._public_key is not None and decoded != self._public_key:
                raise TransportProtocolError("device public_key changed during session")
            self._public_key = decoded
        return signature


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


def _load_serial_class():
    try:
        import serial
    except ImportError as exc:  # pragma: no cover - depends on local install
        raise TransportUnavailable(
            'pyserial is required for MATRIXSCROLL_MODE=hardware. '
            'Install with pip install "matrixscroll[hardware]==0.2.6".'
        ) from exc
    return serial.Serial


def _serial_settings_from_env() -> SerialSettings | None:
    port = os.environ.get("MATRIXSCROLL_SE050_PORT", "").strip()
    if not port:
        return None
    baudrate = int(os.environ.get("MATRIXSCROLL_SE050_BAUD", str(DEFAULT_BAUDRATE)).strip())
    timeout_ms = int(os.environ.get("MATRIXSCROLL_SE050_TIMEOUT_MS", str(DEFAULT_TIMEOUT_MS)).strip())
    return SerialSettings(port=port, baudrate=baudrate, timeout_ms=timeout_ms)


def open_transport() -> SE050Transport | None:
    """Return an active transport or None when hardware is unavailable."""
    if _env_flag("MATRIXSCROLL_SE050_MOCK"):
        return MockSE050Transport()
    settings = _serial_settings_from_env()
    if settings is None:
        return None
    try:
        return SerialSE050Transport(settings)
    except TransportUnavailable as exc:
        return ErrorSE050Transport(str(exc))
