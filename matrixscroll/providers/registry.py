"""Provider selection and low-level sign/verify helpers."""

from __future__ import annotations

import base64
import binascii
import os
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from ..constants import ALGORITHM, SCHEMA
from .base import IdentityProvider
from .emulated import EmulatedProvider, device_id, store_dir
from .hardware import HardwareProvider

_PROVIDER: IdentityProvider | None = None


def get_provider(*, refresh: bool = False) -> IdentityProvider:
    global _PROVIDER
    if _PROVIDER is not None and not refresh:
        return _PROVIDER
    mode = os.environ.get("MATRIXSCROLL_MODE", "emulated").strip().lower()
    if mode == "hardware":
        _PROVIDER = HardwareProvider()
    elif mode == "yubikey":
        from .yubikey import YubiKeyProvider

        _PROVIDER = YubiKeyProvider()
    elif mode == "tpm":
        from .tpm import TpmProvider

        _PROVIDER = TpmProvider()
    else:
        _PROVIDER = EmulatedProvider.load_or_create()
    return _PROVIDER


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def public_key_b64(provider: IdentityProvider | None = None) -> str:
    provider = provider or get_provider()
    return _b64(provider.public_key_bytes())


def identity_info(provider: IdentityProvider | None = None) -> dict[str, Any]:
    provider = provider or get_provider()
    pub = provider.public_key_bytes()
    return {
        "schema": SCHEMA,
        "device_id": device_id(pub),
        "public_key": _b64(pub),
        "algorithm": ALGORITHM,
        "mode": provider.mode,
        "created_at": provider.created_at,
    }


def status(provider: IdentityProvider | None = None) -> dict[str, Any]:
    provider = provider or get_provider()
    available, reason = provider.is_available()
    base: dict[str, Any] = {
        "schema": SCHEMA,
        "available": available,
        "algorithm": ALGORITHM,
        "mode": provider.mode,
        "created_at": provider.created_at,
    }
    if not available:
        base["reason"] = reason
        return base
    pub = provider.public_key_bytes()
    base["device_id"] = device_id(pub)
    base["public_key"] = _b64(pub)
    return base


def sign(data: bytes, provider: IdentityProvider | None = None) -> bytes:
    provider = provider or get_provider()
    return provider.sign(data)


def verify(public_key: str | bytes, data: bytes, signature: str | bytes) -> bool:
    try:
        pub = public_key if isinstance(public_key, bytes) else _unb64(public_key)
        sig = signature if isinstance(signature, bytes) else _unb64(signature)
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, data)
        return True
    except (InvalidSignature, ValueError, TypeError, AttributeError, binascii.Error):
        return False


__all__ = [
    "device_id",
    "get_provider",
    "identity_info",
    "public_key_b64",
    "sign",
    "status",
    "store_dir",
    "verify",
]
