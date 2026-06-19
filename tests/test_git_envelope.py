"""Tests for Matrix Scroll commit envelope helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from matrixscroll import sign_manifest, verify_manifest
from matrixscroll.git import (
    COMMIT_ENVELOPE_SCHEMA,
    build_commit_envelope,
    compute_commit_id,
    sign_commit_envelope,
)


def test_compute_commit_id_matches_git_format():
    commit_id = compute_commit_id(
        tree="d8329fc1cc938780ff89978712c630256214f016",
        parents=[],
        author={"name": "A", "email": "a@example.com", "date": "1000000000 +0000"},
        committer={"name": "A", "email": "a@example.com", "date": "1000000000 +0000"},
        message="initial\n",
    )
    assert len(commit_id) == 40
    assert commit_id.islower()


def test_sign_and_verify_commit_envelope():
    envelope = {
        "schema": COMMIT_ENVELOPE_SCHEMA,
        "commit": {
            "expected_id": "abc123" + "0" * 34,
            "tree": "d8329fc1cc938780ff89978712c630256214f016",
            "parents": [],
            "author": {"name": "T", "email": "t@example.com", "date": "1"},
            "committer": {"name": "T", "email": "t@example.com", "date": "1"},
            "message": "test",
        },
        "provenance": {"actor_type": "human", "tool": "pytest"},
        "repository": {"name": "matrixscroll"},
    }
    signed = sign_commit_envelope(envelope)
    assert signed["signature"]["schema"] == "matrixscroll.signature.v1"
    assert verify_manifest(signed)


def test_build_commit_envelope_in_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=tmp_path, check=True)
    sample = tmp_path / "hello.txt"
    sample.write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "hello.txt"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    envelope = build_commit_envelope(message="init\n", root=tmp_path)
    assert envelope["schema"] == COMMIT_ENVELOPE_SCHEMA
    assert envelope["commit"]["tree"]
    assert envelope["provenance"]["tool"]


def test_example_commit_envelope_schema_constant():
    example = Path(__file__).resolve().parents[1] / "examples" / "commit-envelope.json"
    data = json.loads(example.read_text(encoding="utf-8"))
    assert data["schema"] == COMMIT_ENVELOPE_SCHEMA
