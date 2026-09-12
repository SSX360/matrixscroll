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


# --- Post-quantum (ML-DSA / SLH-DSA) via liboqs when matrixscroll[pqc] is installed ---

# liboqs mechanism identifiers, first match wins. liboqs 0.13 and later name the
# FIPS 205 pure variants SLH_DSA_PURE_SHA2_256S and so on; the hyphenated spellings
# are kept as fallbacks for builds that expose them.
_OQS_ALG_CANDIDATES: dict[str, tuple[str, ...]] = {
    "ml-dsa-44": ("ML-DSA-44",),
    "ml-dsa-65": ("ML-DSA-65",),
    "ml-dsa-87": ("ML-DSA-87",),
    "slh-dsa-sha2-128s": ("SLH_DSA_PURE_SHA2_128S", "SLH-DSA-SHA2-128s"),
    "slh-dsa-sha2-128f": ("SLH_DSA_PURE_SHA2_128F", "SLH-DSA-SHA2-128f"),
    "slh-dsa-sha2-256s": ("SLH_DSA_PURE_SHA2_256S", "SLH-DSA-SHA2-256s"),
    "slh-dsa-sha2-256f": ("SLH_DSA_PURE_SHA2_256F", "SLH-DSA-SHA2-256f"),
}

_PQC_BACKEND: str | None = None
_OQS_RESOLVED: dict[str, str] = {}


def oqs_mechanism_name(algorithm: str) -> str | None:
    """Return the liboqs mechanism identifier enabled for ``algorithm``, or None.

    Both outcomes are cached per process: a resolved name, and "" for an identifier
    that this liboqs build does not enable, so repeated calls for an unsupported set
    do not re-query the mechanism list.
    """
    if algorithm in _OQS_RESOLVED:
        return _OQS_RESOLVED[algorithm] or None
    candidates = _OQS_ALG_CANDIDATES.get(algorithm)
    if not candidates:
        return None
    if not _probe_pqc():
        # The backend probe is cached for the process too, so a missing liboqs is a
        # stable negative answer for every identifier.
        _OQS_RESOLVED[algorithm] = ""
        return None
    import oqs  # type: ignore[import-untyped]

    try:
        enabled = set(oqs.get_enabled_sig_mechanisms())
    except Exception:
        enabled = set()
    for name in candidates:
        if name in enabled:
            _OQS_RESOLVED[algorithm] = name
            return name
    _OQS_RESOLVED[algorithm] = ""
    return None


def _probe_pqc() -> str | None:
    global _PQC_BACKEND
    if _PQC_BACKEND is not None:
        # "" is the cached negative result; report it as None on every call, not only the first.
        return _PQC_BACKEND or None
    try:
        import oqs  # type: ignore[import-untyped]

        _ = oqs.oqs_version()
        _PQC_BACKEND = "liboqs"
    except Exception:
        _PQC_BACKEND = ""
    return _PQC_BACKEND or None


def pqc_available() -> bool:
    return _probe_pqc() is not None


def pqc_backend_info() -> dict[str, str]:
    backend = _probe_pqc()
    info: dict[str, str] = {
        "pqc_available": "true" if backend else "false",
        "pqc_backend": backend or "none",
    }
    if backend:
        import oqs  # type: ignore[import-untyped]

        info["liboqs_version"] = str(oqs.oqs_version())
    return info


def pqc_sign(algorithm: str, secret_key: bytes, message: bytes) -> bytes:
    backend = _probe_pqc()
    if not backend:
        raise RuntimeError("PQC backend not available")
    import oqs  # type: ignore[import-untyped]

    oqs_name = oqs_mechanism_name(algorithm)
    if not oqs_name:
        raise ValueError(f"unsupported PQC algorithm for this liboqs build: {algorithm}")
    with oqs.Signature(oqs_name, secret_key=secret_key) as sig:
        return sig.sign(message)


def pqc_verify(algorithm: str, public_key: bytes, message: bytes, signature: bytes) -> bool:
    backend = _probe_pqc()
    if not backend:
        return False
    import oqs  # type: ignore[import-untyped]

    oqs_name = oqs_mechanism_name(algorithm)
    if not oqs_name:
        return False
    try:
        with oqs.Signature(oqs_name) as sig:
            return bool(sig.verify(message, signature, public_key))
    except Exception:
        return False


__all__ = [
    "backend_info",
    "oqs_mechanism_name",
    "ed25519_private_seed",
    "ed25519_public_key_bytes",
    "ed25519_sign",
    "ed25519_verify",
    "generate_ed25519_private_key",
    "load_ed25519_private_key",
    "load_ed25519_public_key",
    "pqc_available",
    "pqc_backend_info",
    "pqc_sign",
    "pqc_verify",
    "sha256",
    "sha256_hex",
]
