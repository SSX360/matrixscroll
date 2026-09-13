"""ML-KEM (FIPS 203) key-encapsulation primitives for the CNSA 2.0 full-suite track.

Status: the primitives are **Shipping now** (0.8.0); sealed evidence packs that use
them are **Shipping now** (0.9.0) via ``matrixscroll.sealed``. Checked against the
NIST ACVP sample vectors (``vectors/acvp-mlkem-fips203.json``,
``tests/test_acvp_mlkem.py``).

The functions wrap liboqs through ``liboqs-python`` (``pip install matrixscroll[pqc]``)
and follow the same conventions as the signature overlay in ``crypto_backend``:
Matrix Scroll identifiers are lower-case (``ml-kem-1024``), liboqs mechanism names
are resolved at run time, and the default is the CNSA 2.0 parameter set.

This is parameter-set readiness through liboqs. It is not a CNSA 2.0 certification,
a FIPS CMVP validation, or an NSA approval, and the Open Quantum Safe project does
not recommend relying on liboqs in production.
"""

from __future__ import annotations

from .crypto_backend import pqc_available, pqc_backend_info, resolve_oqs_mechanism

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
    try:
        return pqc_available()
    except SystemExit:
        return False


def _enabled_kem_mechanisms() -> list[str]:
    import oqs  # type: ignore[import-untyped]

    return list(oqs.get_enabled_kem_mechanisms())


def oqs_kem_mechanism_name(algorithm: str) -> str | None:
    """Return the liboqs KEM mechanism enabled for ``algorithm``, or None.

    The cache-and-resolve step is ``crypto_backend.resolve_oqs_mechanism``, shared
    with the signature map, so a resolution fix lands in one place.
    """
    return resolve_oqs_mechanism(_OQS_KEM_RESOLVED, _OQS_KEM_CANDIDATES, algorithm, _enabled_kem_mechanisms)


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
    name = _mechanism(algorithm)  # validates the identifier and the backend before oqs is imported
    import oqs  # type: ignore[import-untyped]

    with oqs.KeyEncapsulation(name) as kem:
        if seed is None:
            public_key = kem.generate_keypair()
        else:
            if len(seed) != kem.details["length_keypair_seed"]:
                raise ValueError(f"seed must be {kem.details['length_keypair_seed']} bytes for {algorithm}")
            public_key = kem.generate_keypair_seed(seed)
        return bytes(public_key), bytes(kem.export_secret_key())


def kem_encapsulate(algorithm: str, encapsulation_key: bytes) -> tuple[bytes, bytes]:
    """Return ``(ciphertext, shared_secret)`` for the holder of ``encapsulation_key``."""
    name = _mechanism(algorithm)
    import oqs  # type: ignore[import-untyped]

    with oqs.KeyEncapsulation(name) as kem:
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
    name = _mechanism(algorithm)
    import oqs  # type: ignore[import-untyped]

    # Check both lengths before liboqs sees the key: a wrong-length key handed to the
    # constructor would surface as a backend error, not as this module's ValueError.
    with oqs.KeyEncapsulation(name) as probe:
        details = probe.details
    if len(decapsulation_key) != details["length_secret_key"]:
        raise ValueError(f"decapsulation key must be {details['length_secret_key']} bytes for {algorithm}")
    if len(ciphertext) != details["length_ciphertext"]:
        raise ValueError(f"ciphertext must be {details['length_ciphertext']} bytes for {algorithm}")
    with oqs.KeyEncapsulation(name, secret_key=decapsulation_key) as kem:
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
