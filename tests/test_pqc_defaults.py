"""PQC defaults and CNSA parameter-set readiness (no liboqs required)."""

from __future__ import annotations

from matrixscroll.constants import (
    CNSA_PREFERRED_PQC_ALGORITHM,
    DEFAULT_PQC_ALGORITHM,
    PQC_ALGORITHMS,
)
from matrixscroll.pqc import normalize_pqc_algorithm


def test_default_pqc_algorithm_is_ml_dsa_87() -> None:
    assert DEFAULT_PQC_ALGORITHM == "ml-dsa-87"
    assert CNSA_PREFERRED_PQC_ALGORITHM == "ml-dsa-87"
    assert normalize_pqc_algorithm(None) == "ml-dsa-87"


def test_cnsa_category5_algorithms_are_listed() -> None:
    for algo in (
        "ml-dsa-87",
        "slh-dsa-sha2-256s",
        "slh-dsa-sha2-256f",
    ):
        assert algo in PQC_ALGORITHMS
        assert normalize_pqc_algorithm(algo) == algo


def test_legacy_parameter_sets_remain_selectable() -> None:
    for algo in ("ml-dsa-44", "ml-dsa-65", "slh-dsa-sha2-128s", "slh-dsa-sha2-128f"):
        assert algo in PQC_ALGORITHMS
        assert normalize_pqc_algorithm(algo) == algo
