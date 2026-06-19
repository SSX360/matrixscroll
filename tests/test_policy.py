"""Tests for policy-aware verification."""

from __future__ import annotations

from matrixscroll import sign_manifest
from matrixscroll.policy import VerifyPolicy, verify_manifest_with_policy


def test_verify_manifest_with_policy_require_mode():
    signed = sign_manifest({"schema": "matrixscroll.release.v1", "release": {"version": "0.1.0"}})
    ok, reason = verify_manifest_with_policy(signed, VerifyPolicy(require_mode="hardware"))
    assert not ok
    assert "required mode" in (reason or "")

    ok, _ = verify_manifest_with_policy(signed, VerifyPolicy(require_mode="emulated"))
    assert ok


def test_verify_manifest_with_policy_trusted_keys():
    signed = sign_manifest({"schema": "test.v1"})
    pub = signed["signature"]["public_key"]
    ok, _ = verify_manifest_with_policy(signed, VerifyPolicy(trusted_public_keys={pub}))
    assert ok
    ok, reason = verify_manifest_with_policy(signed, VerifyPolicy(trusted_public_keys={"wrong"}))
    assert not ok
    assert reason == "public key not in trusted set"
