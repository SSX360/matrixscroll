"""Unit tests for MATRIXSCROLL_FIPS policy switch (no FIPS hardware required)."""

from __future__ import annotations

import pytest

from matrixscroll.errors import IdentityError
from matrixscroll.fips_mode import assert_algorithm_allowed, fips_enabled


def test_fips_enabled_reads_exact_one():
    assert fips_enabled({"MATRIXSCROLL_FIPS": "1"}) is True
    assert fips_enabled({"MATRIXSCROLL_FIPS": "0"}) is False
    assert fips_enabled({"MATRIXSCROLL_FIPS": "true"}) is False
    assert fips_enabled({}) is False


def test_assert_allows_ed25519_when_fips_on():
    assert assert_algorithm_allowed("ed25519", env={"MATRIXSCROLL_FIPS": "1"}) == "ed25519"
    assert assert_algorithm_allowed("Ed25519", env={"MATRIXSCROLL_FIPS": "1"}) == "ed25519"


def test_assert_rejects_liboqs_when_fips_on():
    with pytest.raises(IdentityError, match="MATRIXSCROLL_FIPS=1"):
        assert_algorithm_allowed("ml-dsa-87", env={"MATRIXSCROLL_FIPS": "1"})
    with pytest.raises(IdentityError, match="not CMVP"):
        assert_algorithm_allowed("slh-dsa-sha2-256s", env={"MATRIXSCROLL_FIPS": "1"})


def test_assert_passthrough_when_fips_off():
    assert assert_algorithm_allowed("ml-dsa-87", env={}) == "ml-dsa-87"
    assert assert_algorithm_allowed("ed25519", env={"MATRIXSCROLL_FIPS": "0"}) == "ed25519"


def test_assert_rejects_empty_algorithm():
    with pytest.raises(IdentityError, match="non-empty"):
        assert_algorithm_allowed("", env={})
