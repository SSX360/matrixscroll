"""Sealed evidence packs: hybrid X25519 + ML-KEM-1024, AES-256-GCM, dual signatures.

Status: **Shipping now** (0.9.0). Uses ``matrixscroll.kem`` (ACVP-checked ML-KEM)
and the Ed25519 + ML-DSA-87 overlay. Key agreement concatenates the ML-KEM and
X25519 shared secrets and expands them with HKDF-SHA256 (TLS-style hybrid
combiner). This is parameter-set readiness through liboqs; it is not a CNSA 2.0
certification, FIPS CMVP validation, or NSA approval.
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .constants import DEFAULT_PQC_ALGORITHM
from .errors import IdentityError
from .kem import DEFAULT_KEM_ALGORITHM, kem_available, kem_decapsulate, kem_encapsulate
from .manifest import sign_manifest, verify_manifest
from .pqc import attach_pqc_overlay, verify_pqc_signatures

SEALED_SCHEMA = "matrixscroll.sealed-evidence-pack.v1"
#: Domain-separated salt for the sealed-pack HKDF (TLS-style concatenate-then-HKDF).
HKDF_SALT = b"matrixscroll-sealed-v1"
#: HKDF info label; AES-256-GCM key length is 32 bytes.
HKDF_INFO = b"aes-256-gcm"


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _derive_aes_key(ss_mlkem: bytes, ss_x25519: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=HKDF_SALT,
        info=HKDF_INFO,
    ).derive(ss_mlkem + ss_x25519)


def seal_evidence_pack(
    plaintext: bytes | dict[str, Any],
    *,
    recipient_kem_public: bytes,
    recipient_x25519_public: bytes,
    subject: dict[str, Any] | None = None,
    kem_algorithm: str = DEFAULT_KEM_ALGORITHM,
    content_type: str | None = None,
    provider=None,
    pqc_algorithm: str | None = DEFAULT_PQC_ALGORITHM,
) -> dict[str, Any]:
    """Seal ``plaintext`` to a recipient's hybrid public keys and sign the pack.

    Requires ``matrixscroll[pqc]``. The recipient supplies an ML-KEM encapsulation
    key and a long-term X25519 public key. The pack carries an ephemeral X25519
    public key, the KEM ciphertext, and AES-256-GCM ciphertext (tag included).
    Canonical pack fields (including ciphertext) are signed with Ed25519; when
    ``pqc_algorithm`` is set (default ``ml-dsa-87``), an overlay is attached.
    """
    if not kem_available():
        raise RuntimeError("PQC backend not available; install matrixscroll[pqc]")
    if isinstance(plaintext, dict):
        body = json.dumps(plaintext, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
        resolved_type = content_type or "application/json"
    else:
        body = plaintext
        resolved_type = content_type or "application/octet-stream"

    kem_ct, ss_mlkem = kem_encapsulate(kem_algorithm, recipient_kem_public)
    eph = X25519PrivateKey.generate()
    ss_x25519 = eph.exchange(X25519PublicKey.from_public_bytes(recipient_x25519_public))
    aes_key = _derive_aes_key(ss_mlkem, ss_x25519)
    nonce = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, body, None)

    pack: dict[str, Any] = {
        "schema": SEALED_SCHEMA,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "subject": subject or {"type": "evidence", "id": "sealed"},
        "kem_algorithm": kem_algorithm,
        "kem_ciphertext": _b64(kem_ct),
        "x25519_ephemeral_public": _b64(eph.public_key().public_bytes_raw()),
        "x25519_recipient_public": _b64(recipient_x25519_public),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
        "content_type": resolved_type,
    }
    signed = sign_manifest(pack, provider)
    if pqc_algorithm:
        signed = attach_pqc_overlay(signed, pqc_algorithm)
    return signed


def unseal_evidence_pack(
    pack: dict[str, Any],
    *,
    recipient_kem_secret: bytes,
    recipient_x25519_secret: bytes,
    require_pqc: bool = True,
) -> bytes:
    """Verify Ed25519 (+ optional PQC) over the pack, then decrypt the body.

    Raises ``IdentityError`` when the schema or signatures fail. Raises
    ``cryptography.exceptions.InvalidTag`` when AES-GCM authentication fails
    (wrong key or tampered ciphertext after a valid signature).
    """
    if not isinstance(pack, dict) or pack.get("schema") != SEALED_SCHEMA:
        raise IdentityError("not a matrixscroll.sealed-evidence-pack.v1 document")
    if not verify_manifest(pack):
        raise IdentityError("Ed25519 signature verification failed")
    if require_pqc:
        if not pack.get("pqc_signatures"):
            raise IdentityError("sealed pack missing required pqc_signatures")
        if not verify_pqc_signatures(pack):
            raise IdentityError("PQC signature verification failed")
    elif pack.get("pqc_signatures") and not verify_pqc_signatures(pack):
        raise IdentityError("PQC signature verification failed")

    if not kem_available():
        raise RuntimeError("PQC backend not available; install matrixscroll[pqc]")

    algo = str(pack["kem_algorithm"])
    ss_mlkem = kem_decapsulate(algo, recipient_kem_secret, _unb64(pack["kem_ciphertext"]))
    eph_pub = X25519PublicKey.from_public_bytes(_unb64(pack["x25519_ephemeral_public"]))
    ss_x25519 = X25519PrivateKey.from_private_bytes(recipient_x25519_secret).exchange(eph_pub)
    aes_key = _derive_aes_key(ss_mlkem, ss_x25519)
    return AESGCM(aes_key).decrypt(_unb64(pack["nonce"]), _unb64(pack["ciphertext"]), None)


__all__ = [
    "HKDF_INFO",
    "HKDF_SALT",
    "SEALED_SCHEMA",
    "seal_evidence_pack",
    "unseal_evidence_pack",
]
