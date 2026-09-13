"""Round-trip tests for sealed evidence packs (requires matrixscroll[pqc])."""

from __future__ import annotations

import base64
import copy
import json

import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from matrixscroll.errors import IdentityError
from matrixscroll.kem import DEFAULT_KEM_ALGORITHM, kem_available, kem_generate_keypair
from matrixscroll.manifest import sign_manifest
from matrixscroll.pqc import attach_pqc_overlay
from matrixscroll.sealed import (
    HKDF_INFO,
    HKDF_SALT,
    SEALED_SCHEMA,
    seal_evidence_pack,
    unseal_evidence_pack,
)

needs_pqc = pytest.mark.skipif(not kem_available(), reason="matrixscroll[pqc] / liboqs required")


def _recipient() -> tuple[bytes, bytes, bytes, bytes]:
    kem_pub, kem_sec = kem_generate_keypair(DEFAULT_KEM_ALGORITHM)
    x = X25519PrivateKey.generate()
    return kem_pub, kem_sec, x.public_key().public_bytes_raw(), x.private_bytes_raw()


def test_hkdf_labels_are_stable() -> None:
    assert HKDF_SALT == b"matrixscroll-sealed-v1"
    assert HKDF_INFO == b"aes-256-gcm"


def test_requires_pqc_backend_message(monkeypatch) -> None:
    monkeypatch.setattr("matrixscroll.sealed.kem_available", lambda: False)
    with pytest.raises(RuntimeError, match=r"matrixscroll\[pqc\]"):
        seal_evidence_pack(
            b"x",
            recipient_kem_public=b"\x00" * 1568,
            recipient_x25519_public=b"\x00" * 32,
        )


@needs_pqc
def test_seal_unseal_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    kem_pub, kem_sec, x_pub, x_sec = _recipient()
    payload = {"commit": "abc123", "gate": "scroll", "ok": True}
    pack = seal_evidence_pack(
        payload,
        recipient_kem_public=kem_pub,
        recipient_x25519_public=x_pub,
        subject={"type": "commit", "id": "abc123"},
    )
    assert pack["schema"] == SEALED_SCHEMA
    assert pack.get("pqc_signatures")
    assert pack["pqc_signatures"][0]["algorithm"] == "ml-dsa-87"
    out = unseal_evidence_pack(pack, recipient_kem_secret=kem_sec, recipient_x25519_secret=x_sec)
    assert json.loads(out.decode("utf-8")) == payload


@needs_pqc
def test_tampered_ciphertext_fails_signature(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    kem_pub, kem_sec, x_pub, x_sec = _recipient()
    pack = seal_evidence_pack(
        b"hello-sealed",
        recipient_kem_public=kem_pub,
        recipient_x25519_public=x_pub,
        content_type="application/octet-stream",
    )
    bad = copy.deepcopy(pack)
    raw = bytearray(base64.b64decode(bad["ciphertext"]))
    raw[0] ^= 0x01
    bad["ciphertext"] = base64.b64encode(bytes(raw)).decode("ascii")
    with pytest.raises(IdentityError, match="Ed25519"):
        unseal_evidence_pack(bad, recipient_kem_secret=kem_sec, recipient_x25519_secret=x_sec)


@needs_pqc
def test_tampered_ciphertext_after_resign_fails_gcm(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    kem_pub, kem_sec, x_pub, x_sec = _recipient()
    pack = seal_evidence_pack(
        {"n": 1},
        recipient_kem_public=kem_pub,
        recipient_x25519_public=x_pub,
    )
    bad = copy.deepcopy(pack)
    raw = bytearray(base64.b64decode(bad["ciphertext"]))
    raw[-1] ^= 0x01
    bad["ciphertext"] = base64.b64encode(bytes(raw)).decode("ascii")
    bad.pop("signature", None)
    bad.pop("pqc_signatures", None)
    resigned = attach_pqc_overlay(sign_manifest(bad), "ml-dsa-87")
    with pytest.raises(InvalidTag):
        unseal_evidence_pack(
            resigned, recipient_kem_secret=kem_sec, recipient_x25519_secret=x_sec
        )


@needs_pqc
def test_wrong_kem_key_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    kem_pub, _, x_pub, x_sec = _recipient()
    pack = seal_evidence_pack(
        {"n": 1},
        recipient_kem_public=kem_pub,
        recipient_x25519_public=x_pub,
    )
    _, wrong_sec, _, _ = _recipient()
    with pytest.raises(InvalidTag):
        unseal_evidence_pack(pack, recipient_kem_secret=wrong_sec, recipient_x25519_secret=x_sec)


@needs_pqc
def test_mutated_pack_fails_signature(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    kem_pub, kem_sec, x_pub, x_sec = _recipient()
    pack = seal_evidence_pack(
        {"n": 1},
        recipient_kem_public=kem_pub,
        recipient_x25519_public=x_pub,
        subject={"type": "commit", "id": "one"},
    )
    bad = copy.deepcopy(pack)
    bad["subject"] = {"type": "commit", "id": "two"}
    with pytest.raises(IdentityError, match="Ed25519"):
        unseal_evidence_pack(bad, recipient_kem_secret=kem_sec, recipient_x25519_secret=x_sec)
