"""NIST ACVP signature-verification known-answer tests for the PQC overlay.

The vectors in ``vectors/acvp-sigver-fips204-fips205.json`` are copied from the
NIST ACVP-Server gen-val sample files (external interface, pure variant). Each
test names its NIST tcId and expected verdict. sigVer groups carry NIST's valid
and deliberately modified inputs; sigGen groups carry NIST's expected signatures
over an empty context string, restated as positive verification cases. The tests
run the vectors through the same liboqs mechanism that
``matrixscroll.crypto_backend.pqc_verify`` uses, so they check three things: that
the overlay's own empty-context path accepts NIST-valid signatures, that the
backend rejects what NIST says is invalid, and that the name mapping from Matrix
Scroll's algorithm identifiers to liboqs mechanisms is the FIPS 204 / FIPS 205
pure variant and not something else. This is an evidence mapping to NIST sample
vectors, not a certification claim (see docs/CRYPTO_ROADMAP.md).

The provenance test needs only the JSON and runs everywhere; the other tests skip
when liboqs is not installed. Tests with a non-empty context string need a
liboqs-python build that exposes ``verify_with_ctx_str``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from matrixscroll.crypto_backend import oqs_mechanism_name, pqc_available, pqc_verify
from tests._pqc_support import liboqs_family_enabled

VECTORS = Path(__file__).resolve().parent.parent / "vectors" / "acvp-sigver-fips204-fips205.json"

# Matrix Scroll identifier for each ACVP parameter set in the vector file.
_ALGORITHM_IDS = {
    "ML-DSA-87": "ml-dsa-87",
    "SLH-DSA-SHA2-256s": "slh-dsa-sha2-256s",
    "SLH-DSA-SHA2-256f": "slh-dsa-sha2-256f",
}

# The provenance test reads only the JSON and runs everywhere; the two liboqs-dependent
# tests carry the skip themselves.
needs_liboqs = pytest.mark.skipif(not pqc_available(), reason="liboqs PQC backend not installed")


def _load_cases() -> list[tuple[str, str, dict]]:
    doc = json.loads(VECTORS.read_text(encoding="utf-8"))
    cases: list[tuple[str, str, dict]] = []
    for group in doc["groups"]:
        for test in group["tests"]:
            cases.append((group["algorithm"], group["mode"], test))
    return cases


def _case_id(case: tuple[str, str, dict]) -> str:
    algorithm, mode, test = case
    return f"{algorithm}-{mode}-tc{test['tcId']}-{'valid' if test['testPassed'] else 'invalid'}"


CASES = _load_cases()


def test_vector_file_declares_its_provenance() -> None:
    doc = json.loads(VECTORS.read_text(encoding="utf-8"))
    prov = doc["_provenance"]
    for source in prov["sources"].values():
        assert source["url"].startswith("https://raw.githubusercontent.com/usnistgov/ACVP-Server/")
        assert len(source["sha256"]) == 64
    assert {g["algorithm"] for g in doc["groups"]} == set(_ALGORITHM_IDS)
    assert all(g["signatureInterface"] == "external" and g["preHash"] == "pure" for g in doc["groups"])
    assert all(g["source"] in prov["sources"] for g in doc["groups"])
    # Every parameter set has at least one NIST-valid signature over an empty context,
    # so the overlay's own verify path (pqc_verify) is exercised positively for each.
    for parameter_set in _ALGORITHM_IDS:
        assert any(
            g["algorithm"] == parameter_set and t["testPassed"] and not t.get("context")
            for g in doc["groups"]
            for t in g["tests"]
        ), f"no valid empty-context vector for {parameter_set}"


@needs_liboqs
@pytest.mark.parametrize("parameter_set", sorted(_ALGORITHM_IDS))
def test_mechanism_resolves_to_the_pure_fips_variant(parameter_set: str) -> None:
    """The identifier must resolve to the pure (non-prehash, SHA2) mechanism of its family.

    A build without the family skips; a build with the family but no resolution fails,
    so a wrong name mapping is reported as a failure and not hidden as a skip.
    """
    family = "ML-DSA" if parameter_set.startswith("ML-DSA") else "SLH-DSA"
    if not liboqs_family_enabled(family):
        pytest.skip(f"this liboqs build has no {family} mechanisms")
    name = oqs_mechanism_name(_ALGORITHM_IDS[parameter_set])
    assert name, f"{parameter_set} does not resolve to an enabled liboqs mechanism"
    assert "PREHASH" not in name.upper() and "SHAKE" not in name.upper()


@needs_liboqs
@pytest.mark.parametrize("case", CASES, ids=_case_id)
def test_acvp_sigver_vector(case: tuple[str, str, dict]) -> None:
    import oqs  # type: ignore[import-untyped]

    parameter_set, _mode, test = case
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
            # An exception here is a test failure, not a negative verdict: NIST's modified
            # inputs keep valid lengths, so the verifier must answer, not raise.
            verdict = bool(sig.verify_with_ctx_str(message, signature, context, public_key))
    else:
        # The empty-context path is exactly what Matrix Scroll's overlay uses.
        verdict = pqc_verify(algorithm, public_key, message, signature)

    assert verdict == expected, f"tcId {test['tcId']}: {test['reason']}"
