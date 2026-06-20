"""Tests for PR provenance gate helpers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from matrixscroll.git import (
    build_commit_envelope,
    envelope_path,
    save_envelope,
    sign_commit_envelope,
)
from matrixscroll.gate import (
    BUNDLE_INDEX,
    DEFAULT_NOTES_REF,
    export_envelope_bundle,
    fetch_notes,
    publish_envelopes_to_notes,
    verify_commit_envelope_for_sha,
    verify_envelope_range,
)
from matrixscroll.policy import VerifyPolicy


def _init_repo(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=tmp_path, check=True)
    return tmp_path


def _commit_file(repo: Path, name: str, message: str) -> str:
    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def _sign_and_save(repo: Path, sha: str, *, actor_type: str = "human") -> None:
    envelope = build_commit_envelope(commit_sha=sha, root=repo)
    envelope["provenance"]["actor_type"] = actor_type
    signed = sign_commit_envelope(envelope)
    save_envelope(signed, repo)


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MATRIXSCROLL_MODE", "emulated")
    import matrixscroll._core as core

    core._PROVIDER = None
    yield tmp_path


def test_verify_commit_envelope_for_sha_passes(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha)

    envelope = json.loads(envelope_path(sha, repo).read_text(encoding="utf-8"))
    result = verify_commit_envelope_for_sha(envelope, sha)
    assert result.ok
    assert result.device_id
    assert result.mode == "emulated"
    assert result.actor_type == "human"


def test_verify_commit_envelope_for_sha_fails_on_mismatch(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha)

    envelope = json.loads(envelope_path(sha, repo).read_text(encoding="utf-8"))
    wrong_sha = "0" * 40
    result = verify_commit_envelope_for_sha(envelope, wrong_sha)
    assert not result.ok
    assert "mismatch" in (result.error or "")


def test_verify_commit_envelope_for_sha_fails_policy(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha)

    envelope = json.loads(envelope_path(sha, repo).read_text(encoding="utf-8"))
    result = verify_commit_envelope_for_sha(
        envelope, sha, VerifyPolicy(require_mode="hardware")
    )
    assert not result.ok
    assert "required mode" in (result.error or "")


def test_export_envelope_bundle(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha1 = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha1)
    sha2 = _commit_file(repo, "b.txt", "second")
    _sign_and_save(repo, sha2, actor_type="agent")

    out = tmp_path / "bundle"
    result = export_envelope_bundle("", sha2, out, root=repo)
    assert result["ok"]
    assert result["exported"] == 2
    assert (out / f"{sha1}.json").is_file()
    assert (out / f"{sha2}.json").is_file()
    index = json.loads((out / BUNDLE_INDEX).read_text(encoding="utf-8"))
    assert index["schema"] == "matrixscroll.envelope_bundle.v1"
    assert sha1 in index["commits"]
    assert sha2 in index["commits"]


def test_verify_envelope_range_local(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha1 = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha1)
    sha2 = _commit_file(repo, "b.txt", "second")
    _sign_and_save(repo, sha2, actor_type="agent")

    summary = verify_envelope_range("", sha2, source="local", root=repo)
    assert summary["ok"]
    assert summary["verified_count"] == 2
    assert summary["agent_count"] == 1
    assert summary["human_count"] == 1
    assert "emulated" in summary["modes"]


def test_verify_envelope_range_missing_envelope(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha1 = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha1)
    sha2 = _commit_file(repo, "b.txt", "second")

    summary = verify_envelope_range("", sha2, source="local", root=repo)
    assert not summary["ok"]
    assert summary["verified_count"] == 1
    missing = [r for r in summary["results"] if not r["ok"]]
    assert any(r["sha"] == sha2 and "missing" in r["error"] for r in missing)


def test_verify_envelope_range_from_bundle(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha)

    bundle = tmp_path / "bundle"
    export_envelope_bundle("", sha, bundle, root=repo)

    summary = verify_envelope_range("", sha, source="bundle", bundle_dir=bundle, root=repo)
    assert summary["ok"]
    assert summary["verified_count"] == 1


def test_publish_and_verify_notes(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha)

    pub = publish_envelopes_to_notes("", sha, root=repo, notes_ref=DEFAULT_NOTES_REF)
    assert pub["ok"]
    assert pub["published"] == 1

    summary = verify_envelope_range(
        "", sha, source="notes", root=repo, notes_ref=DEFAULT_NOTES_REF
    )
    assert summary["ok"]
    assert summary["verified_count"] == 1


def test_fetch_notes_calls_git(isolated_env, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = _init_repo(tmp_path / "repo")
    calls: list[list[str]] = []

    def fake_run(*args: str, cwd=None, strip=True):
        calls.append(list(args))
        return ""

    monkeypatch.setattr("matrixscroll.gate._run_git", fake_run)
    result = fetch_notes("origin", root=repo, notes_ref=DEFAULT_NOTES_REF)
    assert result["ok"]
    assert calls == [["fetch", "origin", f"{DEFAULT_NOTES_REF}:{DEFAULT_NOTES_REF}"]]


def test_verify_envelope_range_empty(isolated_env, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    summary = verify_envelope_range(sha, sha, source="local", root=repo)
    assert summary["ok"]
    assert summary["total"] == 0
    assert summary.get("note") == "no commits in range"


def test_format_range_summary():
    from matrixscroll.gate import format_range_summary

    md = format_range_summary({"ok": True, "verified_count": 2, "total": 2, "agent_count": 1, "human_count": 1, "modes": ["emulated"], "results": []})
    assert "Matrix Scroll provenance gate" in md
    assert "Agent commits" in md
