"""NIST ACVP signature-verification known-answer tests for the PQC overlay.

The vectors in ``vectors/acvp-sigver-fips204-fips205.json`` are copied from the
NIST ACVP-Server gen-val sample files (external interface, pure variant). Each
test names its NIST tcId and expected verdict. The tests run the vectors through
the same liboqs mechanism that ``matrixscroll.crypto_backend.pqc_verify`` uses,
so they check two things at once: that the backend verifies what NIST says is
valid and rejects what NIST says is invalid, and that the name mapping from
Matrix Scroll's algorithm identifiers to liboqs mechanisms is the FIPS 204 /
FIPS 205 pure variant and not something else.

Every test skips when liboqs is not installed. Tests with a non-empty context
string need a liboqs-python build that exposes ``verify_with_ctx_str``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from matrixscroll.crypto_backend import oqs_mechanism_name, pqc_available, pqc_verify

VECTORS = Path(__file__).resolve().parent.parent / "vectors" / "acvp-sigver-fips204-fips205.json"

# Matrix Scroll identifier for each ACVP parameter set in the vector file.
_ALGORITHM_IDS = {
    "ML-DSA-87": "ml-dsa-87",
    "SLH-DSA-SHA2-256s": "slh-dsa-sha2-256s",
    "SLH-DSA-SHA2-256f": "slh-dsa-sha2-256f",
}

pytestmark = pytest.mark.skipif(not pqc_available(), reason="liboqs PQC backend not installed")


def _load_cases() -> list[tuple[str, dict]]:
    doc = json.loads(VECTORS.read_text(encoding="utf-8"))
    cases: list[tuple[str, dict]] = []
    for group in doc["groups"]:
        for test in group["tests"]:
            cases.append((group["algorithm"], test))
    return cases


def _case_id(case: tuple[str, dict]) -> str:
    algorithm, test = case
    return f"{algorithm}-tc{test['tcId']}-{'valid' if test['testPassed'] else 'invalid'}"


CASES = _load_cases()


def test_vector_file_declares_its_provenance() -> None:
    doc = json.loads(VECTORS.read_text(encoding="utf-8"))
    prov = doc["_provenance"]
    for source in prov["sources"].values():
        assert source["url"].startswith("https://raw.githubusercontent.com/usnistgov/ACVP-Server/")
        assert len(source["sha256"]) == 64
    assert {g["algorithm"] for g in doc["groups"]} == set(_ALGORITHM_IDS)
    assert all(g["signatureInterface"] == "external" and g["preHash"] == "pure" for g in doc["groups"])


@pytest.mark.parametrize("parameter_set", sorted(_ALGORITHM_IDS))
def test_mechanism_resolves_to_the_pure_fips_variant(parameter_set: str) -> None:
    name = oqs_mechanism_name(_ALGORITHM_IDS[parameter_set])
    assert name, f"{parameter_set} is not enabled in this liboqs build"
    assert "PREHASH" not in name.upper()
    assert "SHAKE" not in name.upper() or parameter_set.startswith("ML-DSA")


@pytest.mark.parametrize("case", CASES, ids=_case_id)
def test_acvp_sigver_vector(case: tuple[str, dict]) -> None:
    import oqs  # type: ignore[import-untyped]

    parameter_set, test = case
    algorithm = _ALGORITHM_IDS[parameter_set]
    mechanism = oqs_mechanism_name(algorithm)
    if not mechanism:
        pytest.skip(f"{parameter_set} is not enabled in this liboqs build")
    public_key = bytes.fromhex(test["pk"])
    message = bytes.fromhex(test["message"])
    signature = bytes.fromhex(test["signature"])
    context = bytes.fromhex(test.get("context") or "")
    expected = bool(test["testPassed"])

    if context:
        with oqs.Signature(mechanism) as sig:
            if not hasattr(sig, "verify_with_ctx_str"):
                pytest.skip("liboqs-python build has no verify_with_ctx_str")
            try:
                verdict = bool(sig.verify_with_ctx_str(message, signature, context, public_key))
            except Exception:
                verdict = False
    else:
        # The empty-context path is exactly what Matrix Scroll's overlay uses.
        verdict = pqc_verify(algorithm, public_key, message, signature)

    assert verdict == expected, f"tcId {test['tcId']}: {test['reason']}"
