"""Matrix Scroll root of trust — Ed25519 device identity and signing.

This is the "software emulation first" layer for the Matrix Scroll hardware key.
The same API serves the local emulator today and the physical NXP SE050 device
later, selected via the MATRIXSCROLL_MODE environment variable.

Security contract:
  - Private keys never leave the provider. Public callers only ever see the
    public key, the derived device id, and signatures.
  - In emulated mode the private seed is stored locally under
    ~/.matrixscroll/device.json. The directory is created 0700 and the file is
    opened 0600 at creation time (never write-then-chmod), so the seed is never
    momentarily world-readable. A corrupt store fails loud rather than silently
    re-minting identity. On real hardware the seed is sealed in the secure
    element and this file holds only public material.
"""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

SCHEMA = "matrixscroll.identity.v1"
SIGNATURE_SCHEMA = "matrixscroll.signature.v1"
ALGORITHM = "ed25519"
DEVICE_FILE = "device.json"

_RAW = serialization.Encoding.Raw
_PRIV_RAW = serialization.PrivateFormat.Raw
_PUB_RAW = serialization.PublicFormat.Raw
_NOENC = serialization.NoEncryption()

SEED_LEN = 32
DIR_MODE = 0o700
FILE_MODE = 0o600


class IdentityError(Exception):
    """Raised when the device key store cannot be read or is untrustworthy."""


def store_dir() -> Path:
    """Resolve the device store directory (override via MATRIXSCROLL_HOME)."""
    env = os.environ.get("MATRIXSCROLL_HOME", "").strip()
    base = Path(env).expanduser() if env else (Path.home() / ".matrixscroll")
    return base


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _write_secret(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` created with owner-only (0o600) permissions.

    The file is opened with O_CREAT|O_EXCL via os.open so the private seed is
    never momentarily world-readable (which a write-then-chmod sequence allows).
    On Windows the POSIX mode is advisory, but O_EXCL still prevents clobbering.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(str(path), flags, FILE_MODE)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)
    try:
        os.chmod(path, FILE_MODE)
    except OSError:
        pass


def device_id(public_key: bytes) -> str:
    """Derive a stable, human-readable id (MS-XXXX-XXXX) from a public key."""
    digest = hashlib.sha256(public_key).hexdigest().upper()
    return f"MS-{digest[:4]}-{digest[4:8]}"


class IdentityProvider(ABC):
    """A root-of-trust provider. Signing happens here; keys never escape."""

    mode: str = "unknown"

    @abstractmethod
    def public_key_bytes(self) -> bytes:
        ...

    @abstractmethod
    def sign(self, data: bytes) -> bytes:
        ...

    @property
    def created_at(self) -> str:
        return ""

    def is_available(self) -> tuple[bool, str | None]:
        """Whether this provider can actually serve keys/signatures right now.

        Returns ``(True, None)`` when usable; ``(False, reason)`` when the
        provider is selected but not yet operational (e.g. the hardware stub).
        Soft status surfaces use this to avoid crashing read-only endpoints
        when the SE050 path is not yet wired; signing paths still raise loud.
        """
        return True, None


class EmulatedProvider(IdentityProvider):
    """Software Matrix Scroll. Holds an Ed25519 key in process memory."""

    mode = "emulated"

    def __init__(self, private_key: Ed25519PrivateKey, created_at: str) -> None:
        self._key = private_key
        self._created_at = created_at

    @classmethod
    def load_or_create(cls, directory: Path | None = None) -> "EmulatedProvider":
        directory = directory or store_dir()
        path = directory / DEVICE_FILE
        if path.is_file():
            return cls._load(path)

        key = Ed25519PrivateKey.generate()
        created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pub = key.public_key().public_bytes(_RAW, _PUB_RAW)
        doc = {
            "schema": SCHEMA,
            "mode": cls.mode,
            "created_at": created,
            "device_id": device_id(pub),
            "public_key": _b64(pub),
            "private_key": _b64(key.private_bytes(_RAW, _PRIV_RAW, _NOENC)),
        }
        directory.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(directory, DIR_MODE)
        except OSError:
            pass
        _write_secret(path, json.dumps(doc, indent=2) + "\n")
        return cls(key, created)

    @classmethod
    def _load(cls, path: Path) -> "EmulatedProvider":
        """Load an existing key store, failing loud (never re-minting) if it is
        corrupt so a tampered or truncated file cannot silently rotate identity."""
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            seed = _unb64(doc["private_key"])
        except (OSError, ValueError, KeyError, AttributeError, binascii.Error) as exc:
            raise IdentityError(f"device key store at {path} is unreadable: {exc}")
        if len(seed) != SEED_LEN:
            raise IdentityError(
                f"device key store at {path} has an invalid {len(seed)}-byte seed"
            )
        try:
            key = Ed25519PrivateKey.from_private_bytes(seed)
        except ValueError as exc:
            raise IdentityError(f"device key store at {path} is corrupt: {exc}")
        return cls(key, doc.get("created_at", ""))

    def public_key_bytes(self) -> bytes:
        return self._key.public_key().public_bytes(_RAW, _PUB_RAW)

    def sign(self, data: bytes) -> bytes:
        return self._key.sign(data)

    @property
    def created_at(self) -> str:
        return self._created_at


class HardwareProvider(IdentityProvider):
    """Stub for the physical NXP SE050 device (not yet wired)."""

    mode = "hardware"
    UNAVAILABLE_REASON = (
        "Matrix Scroll hardware provider is not available yet. "
        "Use MATRIXSCROLL_MODE=emulated (default) for the software key."
    )

    def is_available(self) -> tuple[bool, str | None]:
        return False, self.UNAVAILABLE_REASON

    def public_key_bytes(self) -> bytes:  # pragma: no cover - hardware path
        raise NotImplementedError(self.UNAVAILABLE_REASON)

    def sign(self, data: bytes) -> bytes:  # pragma: no cover - hardware path
        raise NotImplementedError(self.UNAVAILABLE_REASON)


_PROVIDER: IdentityProvider | None = None


def get_provider(*, refresh: bool = False) -> IdentityProvider:
    """Return the active root-of-trust provider (cached).

    Mode is chosen by MATRIXSCROLL_MODE (default "emulated"). The hardware path
    is reserved for the physical device.
    """
    global _PROVIDER
    if _PROVIDER is not None and not refresh:
        return _PROVIDER
    mode = os.environ.get("MATRIXSCROLL_MODE", "emulated").strip().lower()
    if mode == "hardware":
        _PROVIDER = HardwareProvider()
    else:
        _PROVIDER = EmulatedProvider.load_or_create()
    return _PROVIDER


def public_key_b64(provider: IdentityProvider | None = None) -> str:
    provider = provider or get_provider()
    return _b64(provider.public_key_bytes())


def identity_info(provider: IdentityProvider | None = None) -> dict[str, Any]:
    """Public-only identity material. Never includes the private key."""
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
    """Soft identity status for read-only surfaces (e.g. an HTTP API).

    Mirrors :func:`identity_info` when the provider is available and adds an
    ``available`` flag. When the provider is selected but not yet operational
    (the hardware stub today), returns ``available=False`` with a ``reason``
    and no key material instead of raising — so dashboards stay green when the
    SSX360 device path is configured before the SE050 transport is wired.
    """
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
    """Verify a signature against a public key. Returns False on any mismatch."""
    try:
        pub = public_key if isinstance(public_key, bytes) else _unb64(public_key)
        sig = signature if isinstance(signature, bytes) else _unb64(signature)
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, data)
        return True
    except (InvalidSignature, ValueError, TypeError, AttributeError, binascii.Error):
        return False


def _canonical(payload: dict[str, Any]) -> bytes:
    """Deterministic bytes for signing, identical across platforms and runs.

    Contract: the top-level ``signature`` block is excluded; keys are sorted
    recursively; whitespace is stripped; non-ASCII is escaped (``ensure_ascii``)
    so byte output never depends on locale or terminal encoding; and NaN/Infinity
    are rejected (``allow_nan=False``) because they have no portable JSON form and
    would otherwise produce signatures other verifiers cannot reproduce.
    """
    body = {k: v for k, v in payload.items() if k != "signature"}
    return json.dumps(
        body,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sign_manifest(
    manifest: dict[str, Any], provider: IdentityProvider | None = None
) -> dict[str, Any]:
    """Return a copy of ``manifest`` with a Matrix Scroll signature block attached."""
    provider = provider or get_provider()
    info = identity_info(provider)
    signed = copy.deepcopy(manifest)
    signed.pop("signature", None)
    signature_value = _b64(provider.sign(_canonical(signed)))
    signed["signature"] = {
        "schema": SIGNATURE_SCHEMA,
        "algorithm": ALGORITHM,
        "device_id": info["device_id"],
        "public_key": info["public_key"],
        "mode": info["mode"],
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "value": signature_value,
    }
    return signed


def verify_manifest(manifest: dict[str, Any]) -> bool:
    """Verify a manifest produced by :func:`sign_manifest`.

    Malformed signature blocks return ``False`` instead of raising. Version and
    algorithm checks intentionally happen before the cryptographic verify so a
    future schema cannot be accidentally accepted under v1 rules.
    """
    if not isinstance(manifest, dict):
        return False
    block = manifest.get("signature")
    if not isinstance(block, dict):
        return False
    if block.get("schema") != SIGNATURE_SCHEMA or block.get("algorithm") != ALGORITHM:
        return False
    public_key = block.get("public_key")
    signature = block.get("value")
    if not isinstance(public_key, str) or not isinstance(signature, str):
        return False
    try:
        public_key_bytes = _unb64(public_key)
    except (ValueError, binascii.Error):
        return False
    if block.get("device_id") != device_id(public_key_bytes):
        return False
    try:
        signing_input = _canonical(manifest)
    except (TypeError, ValueError):
        return False
    return verify(public_key_bytes, signing_input, signature)

