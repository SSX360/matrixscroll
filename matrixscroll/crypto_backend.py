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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

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


_ED25519_P = 2**255 - 19

# The y coordinates of the eight points of small order on edwards25519, in the
# RFC 8032 little-endian encoding with the x-sign bit cleared: the identity (y = 1),
# the point of order 2 (y = p - 1), the two of order 4 (y = 0) and the four of
# order 8, plus the non-canonical spellings y = p and y = p + 1. This is the
# blocklist libsodium checks in ``ge25519_has_small_order``. ``tests/test_independent_verifier.py``
# regenerates the list from the pure-Python curve arithmetic of the independent
# verifier, so the two implementations agree on what they reject.
_ED25519_SMALL_ORDER_Y: frozenset[bytes] = frozenset(
    bytes.fromhex(h)
    for h in (
        "0000000000000000000000000000000000000000000000000000000000000000",
        "0100000000000000000000000000000000000000000000000000000000000000",
        "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
        "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
        "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
        "edffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
        "eeffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
    )
)


def ed25519_point_is_acceptable(raw: bytes) -> bool:
    """RFC 8032 point encoding checks that OpenSSL does not make on its own.

    A public key or an ``R`` value is rejected when its y coordinate is not
    reduced modulo p (RFC 8032 section 5.1.3 says decoding fails) or when the
    point has small order: with such a key the verification equation holds for
    a signature that needs no private key (``R`` the identity, ``S`` zero).
    """
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != 32:
        return False
    if (int.from_bytes(raw, "little") & ((1 << 255) - 1)) >= _ED25519_P:
        return False
    return bytes(raw[:31]) + bytes([raw[31] & 0x7F]) not in _ED25519_SMALL_ORDER_Y


def ed25519_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    if not ed25519_point_is_acceptable(public_key):
        return False
    if not isinstance(signature, (bytes, bytearray)) or len(signature) != 64:
        return False
    if not ed25519_point_is_acceptable(signature[:32]):
        return False
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        return True
    except (InvalidSignature, ValueError, TypeError, AttributeError, binascii.Error):
        return False


def sha256(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()


def sha256_digest(data: bytes) -> bytes:
    """Alias for ``sha256`` (raw digest bytes)."""
    return sha256(data)


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


def resolve_oqs_mechanism(
    cache: dict[str, str],
    candidates: dict[str, tuple[str, ...]],
    algorithm: str,
    enabled_mechanisms: "Callable[[], Iterable[str]]",
) -> str | None:
    """Map a Matrix Scroll identifier to the liboqs mechanism this build enables.

    One implementation serves the signature map (``oqs_mechanism_name``) and the
    KEM map (``matrixscroll.kem.oqs_kem_mechanism_name``); only the candidate table
    and the mechanism-list query differ. Both outcomes are cached per process in
    ``cache``: the resolved name, or "" for an identifier the build does not enable,
    so repeated calls for an unsupported set do not re-query the list. A missing
    liboqs is a stable negative answer for every identifier because the backend
    probe is cached too.
    """
    if algorithm in cache:
        return cache[algorithm] or None
    names = candidates.get(algorithm)
    if not names:
        return None
    if not _probe_pqc():
        cache[algorithm] = ""
        return None
    try:
        enabled = set(enabled_mechanisms())
    except Exception:
        enabled = set()
    for name in names:
        if name in enabled:
            cache[algorithm] = name
            return name
    cache[algorithm] = ""
    return None


def _enabled_sig_mechanisms() -> list[str]:
    import oqs  # type: ignore[import-untyped]

    return list(oqs.get_enabled_sig_mechanisms())


def oqs_mechanism_name(algorithm: str) -> str | None:
    """Return the liboqs signature mechanism enabled for ``algorithm``, or None."""
    return resolve_oqs_mechanism(_OQS_RESOLVED, _OQS_ALG_CANDIDATES, algorithm, _enabled_sig_mechanisms)


def _probe_pqc() -> str | None:
    global _PQC_BACKEND
    if _PQC_BACKEND is not None:
        # "" is the cached negative result; report it as None on every call, not only the first.
        return _PQC_BACKEND or None
    try:
        import oqs  # type: ignore[import-untyped]

        _ = oqs.oqs_version()
        _PQC_BACKEND = "liboqs"
    except (Exception, SystemExit):
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
    "sha256_digest",
    "sha256_hex",
]
