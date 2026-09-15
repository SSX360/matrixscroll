"""Unit tests for matrixscroll.signing_modes."""

from __future__ import annotations

import pytest

from matrixscroll.crypto_backend import pqc_available
from matrixscroll.errors import IdentityError
from matrixscroll.signing_modes import (
    PRIMARY_MODES,
    algorithm_covered_by_signature,
    assert_primary_signing_supported,
    resolve_primary_mode,
)


def test_primary_modes_tuple():
    assert "ed25519" in PRIMARY_MODES
    assert "ml-dsa-87" in PRIMARY_MODES
    assert "composite-ml-dsa-65-ed25519" in PRIMARY_MODES


def test_resolve_primary_mode_default():
    assert resolve_primary_mode({}) == "ed25519"
    assert resolve_primary_mode({"MATRIXSCROLL_PRIMARY_ALG": ""}) == "ed25519"


def test_resolve_primary_mode_explicit():
    assert resolve_primary_mode({"MATRIXSCROLL_PRIMARY_ALG": "ml-dsa-87"}) == "ml-dsa-87"
    assert (
        resolve_primary_mode({"MATRIXSCROLL_PRIMARY_ALG": "composite-ml-dsa-65-ed25519"})
        == "composite-ml-dsa-65-ed25519"
    )


def test_resolve_primary_mode_unknown_falls_back():
    assert resolve_primary_mode({"MATRIXSCROLL_PRIMARY_ALG": "rsa"}) == "ed25519"


def test_algorithm_covered_by_signature():
    assert algorithm_covered_by_signature(
        {"schema": "matrixscroll.signature.v1", "algorithm": "ed25519"}
    )
    assert not algorithm_covered_by_signature({})
    assert not algorithm_covered_by_signature(None)


def test_assert_primary_signing_supported_ed25519():
    assert assert_primary_signing_supported("ed25519") == "ed25519"


def test_assert_primary_signing_supported_ml_dsa():
    if pqc_available():
        assert assert_primary_signing_supported("ml-dsa-87") == "ml-dsa-87"
    else:
        with pytest.raises(IdentityError, match="matrixscroll\\[pqc\\]"):
            assert_primary_signing_supported("ml-dsa-87")
