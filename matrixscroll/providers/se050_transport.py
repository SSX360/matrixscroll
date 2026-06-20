"""SE050 transport protocol and mock backend (SSX-7 scaffold).

Real I2C transport ships when Pico 2 + OM-SE050ARD-E kits are on the bench.
Set ``MATRIXSCROLL_SE050_MOCK=1`` for in-process Ed25519 stand-in during development.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ..constants import SEED_LEN


@dataclass
class SignResponse:
    signature: bytes
    public_key: bytes


class SE050Transport(Protocol):
    """Host-to-secure-element framing for sign and public-key export."""

    def ping(self) -> bool:
        ...

    def public_key_bytes(self) -> bytes:
        ...

    def sign(self, message: bytes) -> bytes:
        ...


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


def open_transport() -> SE050Transport | None:
    """Return an active transport or None when hardware is unavailable."""
    mock = os.environ.get("MATRIXSCROLL_SE050_MOCK", "").strip().lower()
    if mock in {"1", "true", "yes"}:
        return MockSE050Transport()
    # Future: serial/I2C backend when launch/firmware/ssx360-se050 ships on device.
    return None
