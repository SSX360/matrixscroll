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


def test_parse_commit_with_gpgsig_header():
    from matrixscroll.git import _commit_headers_and_body, compute_commit_id

    raw = (
        "tree d8329fc1cc938780ff89978712c630256214f016\n"
        "parent 5d81bf8ee076675e943c5fca5c24ba8fc6af21b6\n"
        "author Dev <dev@example.com> 1000000000 +0000\n"
        "committer Dev <dev@example.com> 1000000000 +0000\n"
        "gpgsig -----BEGIN PGP SIGNATURE-----\n"
        " \n"
        " signed-body\n"
        " -----END PGP SIGNATURE-----\n"
        "\n"
        "feat: signed commit\n"
    )
    tree, parents, author, committer, body = _commit_headers_and_body(raw)
    assert body == "feat: signed commit\n"
    commit_id = compute_commit_id(
        tree=tree,
        parents=parents,
        author=author,
        committer=committer,
        message=body,
    )
    assert len(commit_id) == 40


def test_github_gpgsig_fixture_parse():
    from matrixscroll.git import _commit_headers_and_body, _commit_object_sha

    fixture = Path(__file__).resolve().parent / "fixtures" / "github-gpgsig-commit.txt"
    raw_bytes = fixture.read_bytes()
    expected_sha = _commit_object_sha(raw_bytes)
    raw = raw_bytes.decode("utf-8").replace("\r\n", "\n")
    tree, parents, author, committer, body = _commit_headers_and_body(raw)
    assert tree
    assert author["email"]
    assert body.startswith("feat: Scroll Gate")
    assert expected_sha == "449abcd4799578bfce0ca128a088af8c298f762a"


def test_parse_commit_matches_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import subprocess

    from matrixscroll.git import parse_commit

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=tmp_path, check=True)
    sample = tmp_path / "hello.txt"
    sample.write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "hello.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    parsed = parse_commit(sha, tmp_path)
    assert parsed["actual_id"] == sha
    assert parsed["message"].startswith("init")


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


def test_tampered_envelope_fails_verify():
    envelope = {
        "schema": COMMIT_ENVELOPE_SCHEMA,
        "commit": {
            "actual_id": "abc123" + "0" * 34,
            "tree": "d8329fc1cc938780ff89978712c630256214f016",
            "parents": [],
            "author": {"name": "T", "email": "t@example.com", "date": "1 +0000"},
            "committer": {"name": "T", "email": "t@example.com", "date": "1 +0000"},
            "message": "test",
        },
        "provenance": {"actor_type": "agent", "tool": "pytest"},
        "repository": {"name": "matrixscroll"},
    }
    signed = sign_commit_envelope(envelope)
    signed["provenance"]["tool"] = "tampered"
    assert not verify_manifest(signed)
