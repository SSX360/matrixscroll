"""Central cryptographic backend for Matrix Scroll.

All Ed25519 signing, verification, key generation, and security-relevant
SHA-256 hashing route through the ``cryptography`` package. Official PyPI
wheels ship pre-built native backends (OpenSSL and Rust components bundled
inside ``cryptography``) — users never install a Rust toolchain.

There is no pure-Python Ed25519 fallback in the reference SDK. Optional
provider paths (YubiKey PIV preview, SE050 mock transport) still delegate
Ed25519 primitives to this module when they operate in software.

See ``docs/CRYPTO_BACKEND.md`` for the middle-path design rationale.
"""

from __future__ import annotations

import binascii

import cryptography
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

_BACKEND = "cryptography"
_RAW = serialization.Encoding.Raw
_PRIV_RAW = serialization.PrivateFormat.Raw
_PUB_RAW = serialization.PublicFormat.Raw
_NOENC = serialization.NoEncryption()


def backend_info() -> dict[str, str]:
    """Return metadata about the active crypto backend (for tests and diagnostics)."""
    return {
        "backend": _BACKEND,
        "cryptography_version": cryptography.__version__,
        "ed25519_module": "cryptography.hazmat.primitives.asymmetric.ed25519",
        "sha256_module": "cryptography.hazmat.primitives.hashes.SHA256",
        "wheel_backends": "OpenSSL + Rust components (bundled in cryptography wheels)",
        "user_rust_toolchain": "not required",
    }


def generate_ed25519_private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


def load_ed25519_private_key(seed: bytes) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(seed)


def load_ed25519_public_key(raw: bytes) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(raw)


def ed25519_public_key_bytes(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.public_key().public_bytes(_RAW, _PUB_RAW)


def ed25519_private_seed(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.private_bytes(_RAW, _PRIV_RAW, _NOENC)


def ed25519_sign(private_key: Ed25519PrivateKey, message: bytes) -> bytes:
    return private_key.sign(message)


def ed25519_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        return True
    except (InvalidSignature, ValueError, TypeError, AttributeError, binascii.Error):
        return False


def sha256(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()


def sha256_hex(data: bytes) -> str:
    return sha256(data).hex()


__all__ = [
    "backend_info",
    "ed25519_private_seed",
    "ed25519_public_key_bytes",
    "ed25519_sign",
    "ed25519_verify",
    "generate_ed25519_private_key",
    "load_ed25519_private_key",
    "load_ed25519_public_key",
    "sha256",
    "sha256_hex",
]
