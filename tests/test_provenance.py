"""Tests for universal provenance action envelopes."""

from __future__ import annotations

import json

import pytest

from matrixscroll.manifest import verify_manifest
from matrixscroll.provenance import (
    ACTION_TYPES,
    build_action_envelope,
    sign_action_envelope,
    validate_action_payload,
)


@pytest.mark.parametrize("action_type", ACTION_TYPES)
def test_build_and_sign_all_action_types(action_type: str) -> None:
    payloads = {
        "git_commit": {"commit_sha": "a" * 40},
        "ci_step": {"pipeline": "ci-unit", "step": "test", "run_id": "12345"},
        "iac_change": {"tool": "terraform", "resource_type": "aws_s3_bucket", "resource_id": "logs"},
        "db_migration": {"migration_id": "20260629_add_users", "database": "app", "direction": "up"},
        "api_call": {"method": "POST", "endpoint": "/api/v1/verify", "status_code": 200},
        "contract_deploy": {
            "chain": "ethereum",
            "contract_address": "0x" + "ab" * 20,
            "tx_hash": "0x" + "cd" * 32,
        },
    }
    envelope = build_action_envelope(
        action_type,  # type: ignore[arg-type]
        payloads[action_type],
        actor_type="ci",
        tool="matrixscroll-test",
    )
    signed = sign_action_envelope(envelope)
    assert signed["schema"] == "matrixscroll.action_envelope.v1"
    assert verify_manifest(signed)
    assert signed["signature"]["mode"] == "emulated"


def test_validate_missing_fields() -> None:
    ok, err = validate_action_payload("ci_step", {"pipeline": "only"})
    assert not ok
    assert "run_id" in (err or "")


def test_sign_action_cli_roundtrip(tmp_path, monkeypatch) -> None:
    from matrixscroll.cli import main

    payload = {"pipeline": "gate", "step": "verify", "run_id": "999"}
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    out_path = tmp_path / "signed.json"
    rc = main(
        [
            "sign-action",
            "--type",
            "ci_step",
            "--payload",
            str(payload_path),
            "--output",
            str(out_path),
            "--actor-type",
            "ci",
        ]
    )
    assert rc == 0
    signed = json.loads(out_path.read_text(encoding="utf-8"))
    assert signed["action_type"] == "ci_step"
    assert verify_manifest(signed)
