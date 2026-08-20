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


def test_verify_envelope_range_empty_fails_closed(isolated_env, tmp_path: Path):
    """An empty range is not a pass. Before this behaviour it returned ok: true."""
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    summary = verify_envelope_range(sha, sha, source="local", root=repo)
    assert not summary["ok"]
    assert summary["total"] == 0
    assert summary["empty_range"] is True
    assert summary["allow_empty_range"] is False
    assert "nothing was verified" in summary["error"]


def test_verify_envelope_range_empty_opt_out(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    summary = verify_envelope_range(sha, sha, source="local", root=repo, allow_empty=True)
    assert summary["ok"]
    assert summary["total"] == 0
    assert summary["empty_range"] is True
    assert summary["allow_empty_range"] is True
    assert "error" not in summary


def test_verified_range_is_distinguishable_from_empty(isolated_env, tmp_path: Path):
    """The two ok: true cases carry different structures, which is the point."""
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha)

    verified = verify_envelope_range("", sha, source="local", root=repo)
    empty = verify_envelope_range(sha, sha, source="local", root=repo, allow_empty=True)
    assert verified["ok"] and empty["ok"]
    assert verified["empty_range"] is False
    assert empty["empty_range"] is True


def test_range_rows_report_agent_scope(isolated_env, tmp_path: Path):
    """verify-agent-scope is recheckable downstream once the row carries the URI."""
    repo = _init_repo(tmp_path / "repo")
    scope = repo / "scope.json"
    from matrixscroll._core import sign_manifest

    scope.write_text(
        json.dumps(sign_manifest({"schema": "matrixscroll.agent_scope.v1", "task": "issue-123"})),
        encoding="utf-8",
    )
    sha = _commit_file(repo, "a.txt", "first")
    envelope = build_commit_envelope(commit_sha=sha, root=repo)
    envelope["provenance"]["agent_scope"] = "scope.json"
    save_envelope(sign_commit_envelope(envelope), repo)

    summary = verify_envelope_range("", sha, source="local", root=repo)
    assert summary["ok"]
    assert summary["agent_scope_verified_count"] == 1
    row = summary["results"][0]
    assert row["agent_scope"] == "scope.json"
    assert row["agent_scope_verified"] is True


def test_failed_range_row_preserves_declared_agent_scope(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    envelope = build_commit_envelope(commit_sha=sha, root=repo)
    envelope["provenance"]["agent_scope"] = "scope.json"
    signed = sign_commit_envelope(envelope)
    signed["commit"]["message"] = "tampered after signing"
    save_envelope(signed, repo)

    summary = verify_envelope_range("", sha, source="local", root=repo)

    assert not summary["ok"]
    row = summary["results"][0]
    assert row["agent_scope"] == "scope.json"
    assert row["agent_scope_verified"] is False


def test_range_rows_omit_agent_scope_when_absent(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "first")
    _sign_and_save(repo, sha)

    summary = verify_envelope_range("", sha, source="local", root=repo)
    assert summary["agent_scope_verified_count"] == 0
    assert "agent_scope" not in summary["results"][0]


def test_format_range_summary():
    from matrixscroll.gate import format_range_summary

    md = format_range_summary({"ok": True, "verified_count": 2, "total": 2, "agent_count": 1, "human_count": 1, "modes": ["emulated"], "results": []})
    assert "Matrix Scroll provenance gate" in md
    assert "Agent commits" in md


def test_format_range_summary_names_the_empty_range():
    from matrixscroll.gate import format_range_summary

    md = format_range_summary(
        {"ok": False, "verified_count": 0, "total": 0, "empty_range": True, "results": []}
    )
    assert "**Status:** failed" in md
    assert "No commit was checked" in md
