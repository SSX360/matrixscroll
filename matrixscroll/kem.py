"""ML-KEM (FIPS 203) key-encapsulation primitives for the CNSA 2.0 full-suite track.

Status: **In progress** (see ``docs/CRYPTO_ROADMAP.md``, "CNSA 2.0 full-suite track").
No envelope, manifest or evidence-pack format uses this module yet. It exists so
that the sealed evidence-pack design can be built on primitives that are already
checked against the NIST ACVP sample vectors (``vectors/acvp-mlkem-fips203.json``,
``tests/test_acvp_mlkem.py``) instead of on a specification alone.

The functions wrap liboqs through ``liboqs-python`` (``pip install matrixscroll[pqc]``)
and follow the same conventions as the signature overlay in ``crypto_backend``:
Matrix Scroll identifiers are lower-case (``ml-kem-1024``), liboqs mechanism names
are resolved at run time, and the default is the CNSA 2.0 parameter set.

This is parameter-set readiness through liboqs. It is not a CNSA 2.0 certification,
a FIPS CMVP validation, or an NSA approval, and the Open Quantum Safe project does
not recommend relying on liboqs in production.
"""

from __future__ import annotations

from .crypto_backend import pqc_available, pqc_backend_info

#: Matrix Scroll identifiers for the FIPS 203 parameter sets the track uses.
#: ``ml-kem-1024`` is the CNSA 2.0 key-establishment set; ``ml-kem-768`` is kept
#: for interoperability tests with the TLS hybrid ``X25519MLKEM768``.
KEM_ALGORITHMS: frozenset[str] = frozenset({"ml-kem-768", "ml-kem-1024"})

#: The CNSA 2.0 key-establishment parameter set (NIST Category 5).
DEFAULT_KEM_ALGORITHM = "ml-kem-1024"

_OQS_KEM_CANDIDATES: dict[str, tuple[str, ...]] = {
    "ml-kem-768": ("ML-KEM-768",),
    "ml-kem-1024": ("ML-KEM-1024",),
}
_OQS_KEM_RESOLVED: dict[str, str] = {}


def kem_available() -> bool:
    """True when liboqs is importable; the same probe the signature overlay uses."""
    return pqc_available()


def oqs_kem_mechanism_name(algorithm: str) -> str | None:
    """Return the liboqs KEM mechanism enabled for ``algorithm``, or None.

    Both outcomes are cached per process, as ``oqs_mechanism_name`` does for
    signatures.
    """
    if algorithm in _OQS_KEM_RESOLVED:
        return _OQS_KEM_RESOLVED[algorithm] or None
    candidates = _OQS_KEM_CANDIDATES.get(algorithm)
    if not candidates or not pqc_available():
        return None
    import oqs  # type: ignore[import-untyped]

    try:
        enabled = set(oqs.get_enabled_kem_mechanisms())
    except Exception:
        enabled = set()
    for name in candidates:
        if name in enabled:
            _OQS_KEM_RESOLVED[algorithm] = name
            return name
    _OQS_KEM_RESOLVED[algorithm] = ""
    return None


def _mechanism(algorithm: str) -> str:
    if algorithm not in KEM_ALGORITHMS:
        raise ValueError(f"unknown KEM algorithm {algorithm!r}; choose one of {sorted(KEM_ALGORITHMS)}")
    if not pqc_available():
        raise RuntimeError("PQC backend not available; install matrixscroll[pqc]")
    name = oqs_kem_mechanism_name(algorithm)
    if not name:
        raise RuntimeError(
            f"KEM algorithm {algorithm!r} is not enabled in this liboqs build "
            f"({pqc_backend_info().get('liboqs_version', 'unknown')})."
        )
    return name


def kem_generate_keypair(algorithm: str = DEFAULT_KEM_ALGORITHM, seed: bytes | None = None) -> tuple[bytes, bytes]:
    """Return ``(encapsulation_key, decapsulation_key)``.

    With ``seed`` (the 64-byte FIPS 203 value ``d || z``) key generation is
    deterministic, which is how the NIST keyGen vectors are checked. Without it
    liboqs draws the seed from the operating system.
    """
    import oqs  # type: ignore[import-untyped]

    with oqs.KeyEncapsulation(_mechanism(algorithm)) as kem:
        if seed is None:
            public_key = kem.generate_keypair()
        else:
            if len(seed) != kem.details["length_keypair_seed"]:
                raise ValueError(f"seed must be {kem.details['length_keypair_seed']} bytes for {algorithm}")
            public_key = kem.generate_keypair_seed(seed)
        return bytes(public_key), bytes(kem.export_secret_key())


def kem_encapsulate(algorithm: str, encapsulation_key: bytes) -> tuple[bytes, bytes]:
    """Return ``(ciphertext, shared_secret)`` for the holder of ``encapsulation_key``."""
    import oqs  # type: ignore[import-untyped]

    with oqs.KeyEncapsulation(_mechanism(algorithm)) as kem:
        if len(encapsulation_key) != kem.details["length_public_key"]:
            raise ValueError(f"encapsulation key must be {kem.details['length_public_key']} bytes for {algorithm}")
        ciphertext, shared_secret = kem.encap_secret(encapsulation_key)
        return bytes(ciphertext), bytes(shared_secret)


def kem_decapsulate(algorithm: str, decapsulation_key: bytes, ciphertext: bytes) -> bytes:
    """Return the shared secret for ``ciphertext``.

    FIPS 203 decapsulation never fails on a well-formed ciphertext: a modified
    ciphertext yields the implicit-rejection value ``J(z || c)``, which the NIST
    vectors pin. A ciphertext of the wrong length raises ``ValueError``.
    """
    import oqs  # type: ignore[import-untyped]

    with oqs.KeyEncapsulation(_mechanism(algorithm), secret_key=decapsulation_key) as kem:
        if len(decapsulation_key) != kem.details["length_secret_key"]:
            raise ValueError(f"decapsulation key must be {kem.details['length_secret_key']} bytes for {algorithm}")
        if len(ciphertext) != kem.details["length_ciphertext"]:
            raise ValueError(f"ciphertext must be {kem.details['length_ciphertext']} bytes for {algorithm}")
        return bytes(kem.decap_secret(ciphertext))


def kem_backend_info() -> dict[str, str]:
    """Diagnostics: backend, liboqs version and the resolved mechanism per identifier."""
    info = dict(pqc_backend_info())
    for algorithm in sorted(KEM_ALGORITHMS):
        info[f"kem_{algorithm}"] = oqs_kem_mechanism_name(algorithm) or "not enabled"
    return info


__all__ = [
    "DEFAULT_KEM_ALGORITHM",
    "KEM_ALGORITHMS",
    "kem_available",
    "kem_backend_info",
    "kem_decapsulate",
    "kem_encapsulate",
    "kem_generate_keypair",
    "oqs_kem_mechanism_name",
]
