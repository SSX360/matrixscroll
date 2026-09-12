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


def test_pqc_probe_negative_result_stays_negative(monkeypatch) -> None:
    """With liboqs absent, the cached negative probe answers False on every call.

    Release 0.7.0 returned the cached "" on the second call, which pqc_available()
    read as True. The import is forced to fail here so the negative path is tested
    whether or not liboqs is installed.
    """
    import sys

    from matrixscroll import crypto_backend

    monkeypatch.setattr(crypto_backend, "_PQC_BACKEND", None)
    monkeypatch.setitem(sys.modules, "oqs", None)  # makes `import oqs` raise ImportError
    assert crypto_backend.pqc_available() is False
    assert crypto_backend.pqc_available() is False
    assert crypto_backend.pqc_available() is False
    assert crypto_backend.pqc_backend_info()["pqc_available"] == "false"


def test_pqc_probe_positive_result_stays_positive(monkeypatch) -> None:
    """With a backend that imports, the probe answers True on every call."""
    import sys
    import types

    from matrixscroll import crypto_backend

    fake = types.ModuleType("oqs")
    fake.oqs_version = lambda: "0.0-test"  # type: ignore[attr-defined]
    monkeypatch.setattr(crypto_backend, "_PQC_BACKEND", None)
    monkeypatch.setitem(sys.modules, "oqs", fake)
    assert crypto_backend.pqc_available() is True
    assert crypto_backend.pqc_available() is True
    assert crypto_backend.pqc_backend_info()["liboqs_version"] == "0.0-test"
