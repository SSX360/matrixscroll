"""Tests for GUAC export and Rekor dry-run publish."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from matrixscroll.gate import export_envelope_bundle
from matrixscroll.guac_export import export_guac_jsonl
from matrixscroll.rekor_publish import publish_rekor_dry_run


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


def _sign_and_save(repo: Path, sha: str) -> None:
    from matrixscroll.git import build_commit_envelope, save_envelope, sign_commit_envelope

    envelope = build_commit_envelope(commit_sha=sha, root=repo)
    save_envelope(sign_commit_envelope(envelope), repo)


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MATRIXSCROLL_MODE", "emulated")
    import matrixscroll._core as core

    core._PROVIDER = None
    yield tmp_path


def test_export_guac_jsonl(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "guac test")
    _sign_and_save(repo, sha)
    bundle_dir = tmp_path / "bundle"
    export_envelope_bundle("", sha, bundle_dir, root=repo)
    output = tmp_path / "guac.jsonl"
    result = export_guac_jsonl(bundle_dir, output, root=repo)
    assert result["ok"]
    assert result["exported"] == 1
    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    statement = json.loads(lines[0])
    assert statement["predicateType"] == "https://matrixscroll.com/attestation/commit-envelope/v1"
    assert statement["subject"][0]["digest"]["sha1"] == sha


def test_publish_rekor_dry_run(isolated_env, tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    sha = _commit_file(repo, "a.txt", "rekor test")
    _sign_and_save(repo, sha)
    bundle_dir = tmp_path / "bundle"
    export_envelope_bundle("", sha, bundle_dir, root=repo)
    out_dir = tmp_path / "rekor"
    result = publish_rekor_dry_run(bundle_dir, out_dir, root=repo)
    assert result["ok"]
    assert (out_dir / f"{sha}.rekor.json").is_file()
    assert (out_dir / "manifest.json").is_file()
