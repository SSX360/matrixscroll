"""NIST ACVP known-answer tests for the ML-KEM-1024 primitives in ``matrixscroll.kem``.

The vectors in ``vectors/acvp-mlkem-fips203.json`` are copied from the NIST
ACVP-Server gen-val sample files for FIPS 203. Three groups are checked:

* keyGen: the seed ``d || z`` must produce NIST's encapsulation and decapsulation keys;
* encapsulation: a NIST-produced ciphertext for a known decapsulation key must
  decapsulate to NIST's shared secret (liboqs draws the encapsulation randomness
  itself, so the encapsulation side is checked through decapsulation);
* decapsulation: valid ciphertexts return NIST's shared secret, and modified
  ciphertexts return NIST's implicit-rejection value rather than raising.

This is an evidence mapping to NIST sample vectors, not a certification claim
(``docs/CRYPTO_ROADMAP.md``). The provenance test runs everywhere; the vector
tests skip when liboqs is not installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from matrixscroll.kem import (
    DEFAULT_KEM_ALGORITHM,
    KEM_ALGORITHMS,
    kem_available,
    kem_decapsulate,
    kem_encapsulate,
    kem_generate_keypair,
    oqs_kem_mechanism_name,
)

VECTORS = Path(__file__).resolve().parent.parent / "vectors" / "acvp-mlkem-fips203.json"

needs_liboqs = pytest.mark.skipif(not kem_available(), reason="liboqs PQC backend not installed")


def _load() -> dict:
    return json.loads(VECTORS.read_text(encoding="utf-8"))


def _cases(mode: str) -> list[dict]:
    return [test for group in _load()["groups"] if group["mode"] == mode for test in group["tests"]]


def _ids(prefix: str):
    return lambda test: f"{prefix}-tc{test['tcId']}"


def test_vector_file_declares_its_provenance() -> None:
    doc = _load()
    prov = doc["_provenance"]
    for source in prov["sources"].values():
        assert source["url"].startswith("https://raw.githubusercontent.com/usnistgov/ACVP-Server/")
        assert len(source["sha256"]) == 64
    assert {g["algorithm"] for g in doc["groups"]} == {"ML-KEM-1024"}
    assert {g["mode"] for g in doc["groups"]} == {"keyGen", "encapsulation", "decapsulation"}
    assert all(g["source"] in prov["sources"] for g in doc["groups"])
    reasons = {t["reason"] for t in _cases("decapsulation")}
    assert "modified ciphertext" in reasons, "the implicit-rejection cases must be present"


def test_default_is_the_cnsa_parameter_set() -> None:
    assert DEFAULT_KEM_ALGORITHM == "ml-kem-1024"
    assert DEFAULT_KEM_ALGORITHM in KEM_ALGORITHMS


@needs_liboqs
def test_mechanism_resolves_to_fips_203_names() -> None:
    import oqs  # type: ignore[import-untyped]

    enabled = set(oqs.get_enabled_kem_mechanisms())
    if "ML-KEM-1024" not in enabled:
        pytest.skip("this liboqs build has no ML-KEM mechanisms")
    assert oqs_kem_mechanism_name("ml-kem-1024") == "ML-KEM-1024"
    assert oqs_kem_mechanism_name("ml-kem-768") == "ML-KEM-768"
    assert oqs_kem_mechanism_name("kyber-1024") is None


@needs_liboqs
@pytest.mark.parametrize("test", _cases("keyGen"), ids=_ids("keyGen"))
def test_keygen_from_seed_matches_nist(test: dict) -> None:
    if not oqs_kem_mechanism_name("ml-kem-1024"):
        pytest.skip("ML-KEM-1024 is not enabled in this liboqs build")
    seed = bytes.fromhex(test["d"]) + bytes.fromhex(test["z"])
    ek, dk = kem_generate_keypair("ml-kem-1024", seed=seed)
    assert ek == bytes.fromhex(test["ek"]), f"tcId {test['tcId']}: encapsulation key differs"
    assert dk == bytes.fromhex(test["dk"]), f"tcId {test['tcId']}: decapsulation key differs"


@needs_liboqs
@pytest.mark.parametrize("test", _cases("encapsulation") + _cases("decapsulation"), ids=_ids("decap"))
def test_decapsulation_matches_nist(test: dict) -> None:
    if not oqs_kem_mechanism_name("ml-kem-1024"):
        pytest.skip("ML-KEM-1024 is not enabled in this liboqs build")
    shared = kem_decapsulate("ml-kem-1024", bytes.fromhex(test["dk"]), bytes.fromhex(test["c"]))
    assert shared == bytes.fromhex(test["k"]), f"tcId {test['tcId']}: {test['reason']}"


@needs_liboqs
@pytest.mark.parametrize("algorithm", sorted(KEM_ALGORITHMS))
def test_round_trip_and_wrong_key(algorithm: str) -> None:
    if not oqs_kem_mechanism_name(algorithm):
        pytest.skip(f"{algorithm} is not enabled in this liboqs build")
    ek, dk = kem_generate_keypair(algorithm)
    ek2, dk2 = kem_generate_keypair(algorithm)
    ciphertext, shared = kem_encapsulate(algorithm, ek)
    assert len(shared) == 32
    assert kem_decapsulate(algorithm, dk, ciphertext) == shared
    # Implicit rejection: the wrong key yields a different secret and no exception.
    other = kem_decapsulate(algorithm, dk2, ciphertext)
    assert other != shared and len(other) == 32
    with pytest.raises(ValueError):
        kem_decapsulate(algorithm, dk, ciphertext[:-1])
    with pytest.raises(ValueError):
        kem_decapsulate(algorithm, dk[:-1], ciphertext)
    with pytest.raises(ValueError):
        kem_encapsulate(algorithm, ek[:-1])
