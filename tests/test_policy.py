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


def test_verify_envelope_attribution_policy_actor_types():
    from matrixscroll.policy import verify_envelope_attribution_policy

    envelope = {"provenance": {"actor_type": "agent", "tool": "pytest"}}
    ok, _ = verify_envelope_attribution_policy(
        envelope, VerifyPolicy(require_actor_types={"agent"})
    )
    assert ok
    ok, reason = verify_envelope_attribution_policy(
        envelope, VerifyPolicy(deny_actor_types={"agent"})
    )
    assert not ok
    assert "denied" in (reason or "")


def test_verify_envelope_attribution_policy_delegation_required():
    from matrixscroll.policy import verify_envelope_attribution_policy

    envelope = {"provenance": {"actor_type": "agent", "tool": "pytest"}}
    ok, reason = verify_envelope_attribution_policy(
        envelope, VerifyPolicy(require_delegation_for_actor_types={"agent"})
    )
    assert not ok
    assert "delegation" in (reason or "")

    envelope["delegation"] = {"owner_id": "owner@example.com"}
    ok, _ = verify_envelope_attribution_policy(
        envelope, VerifyPolicy(require_delegation_for_actor_types={"agent"})
    )
    assert ok


def test_verify_policy_is_empty():
    assert VerifyPolicy().is_empty()
    assert not VerifyPolicy(require_mode="emulated").is_empty()
    assert not VerifyPolicy(require_timestamp=True).is_empty()
    assert not VerifyPolicy(require_receipt=True).is_empty()


def test_trusted_key_validity_window():
    import json
    from pathlib import Path

    signed = sign_manifest({"schema": "test.v1"})
    pub = signed["signature"]["public_key"]
    path = Path("tests/_tmp_trusted_keys_window.json")
    path.write_text(
        json.dumps(
            {
                "trusted_public_keys": [
                    {
                        "public_key": pub,
                        "not_before": "2099-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    try:
        policy = VerifyPolicy.from_json_file(path)
        ok, reason = verify_manifest_with_policy(signed, policy)
        assert not ok
        assert "not yet valid" in (reason or "")
    finally:
        path.unlink(missing_ok=True)


def test_require_timestamp_policy():
    from matrixscroll.timestamp import attach_timestamp, make_dev_token

    signed = sign_manifest({"schema": "test.v1"})
    ok, reason = verify_manifest_with_policy(signed, VerifyPolicy(require_timestamp=True))
    assert not ok
    assert "timestamp" in (reason or "")
    stamped = attach_timestamp(signed, make_dev_token("ab" * 32))
    # Structure ok but cryptographic verify still uses original signature bytes.
    ok, _ = verify_manifest_with_policy(stamped, VerifyPolicy(require_timestamp=True))
    assert ok
