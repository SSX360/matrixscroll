"""Verify the centralized cryptography backend and public sign/verify wiring."""

from __future__ import annotations

import cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import matrixscroll
from matrixscroll.crypto_backend import (
    backend_info,
    ed25519_public_key_bytes,
    ed25519_sign,
    ed25519_verify,
    generate_ed25519_private_key,
    sha256,
    sha256_hex,
)


def test_backend_info_reports_cryptography():
    info = backend_info()
    assert info["backend"] == "cryptography"
    assert info["cryptography_version"] == cryptography.__version__
    assert "ed25519" in info["ed25519_module"]
    assert info["user_rust_toolchain"] == "not required"


def test_ed25519_sign_verify_roundtrip():
    key = generate_ed25519_private_key()
    pub = ed25519_public_key_bytes(key)
    message = b"canonical manifest bytes for roundtrip"
    signature = ed25519_sign(key, message)
    assert len(signature) == 64
    assert ed25519_verify(pub, message, signature)
    assert not ed25519_verify(pub, message + b"tamper", signature)


def test_sha256_helpers():
    data = b"MS-ABCD-EFGH"
    assert sha256_hex(data) == sha256(data).hex()
    assert len(sha256(data)) == 32


def test_public_sign_verify_delegates_to_backend():
    provider = matrixscroll.EmulatedProvider.load_or_create()
    pub = matrixscroll.public_key_b64(provider)
    message = b"release-42"
    signature = matrixscroll.sign(message, provider)
    assert matrixscroll.verify(pub, message, signature)
    assert isinstance(provider._key, Ed25519PrivateKey)
