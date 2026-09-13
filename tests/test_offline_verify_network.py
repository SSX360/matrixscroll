"""Regression: core verify paths must not fetch matrixscroll.com."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from matrixscroll.gate import verify_commit_envelope_for_sha, verify_envelope_range
from matrixscroll.manifest import sign_manifest, verify_manifest

ROOT = Path(__file__).resolve().parent.parent
VALID_MANIFEST = json.loads((ROOT / "vectors" / "valid_simple.json").read_text(encoding="utf-8"))


def _block_matrixscroll_http(*_args, **kwargs):
    url = kwargs.get("url") or (_args[0] if _args else "")
    if "matrixscroll.com" in str(url):
        raise AssertionError(f"unexpected HTTP to matrixscroll.com: {url}")
    raise urllib.error.URLError("blocked for test")


def _init_repo(tmp_path: Path) -> str:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Dev"], cwd=tmp_path, check=True)
    (tmp_path / "file.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


@mock.patch("urllib.request.urlopen", side_effect=_block_matrixscroll_http)
@mock.patch("urllib.request.Request", wraps=urllib.request.Request)
def test_verify_manifest_never_fetches_matrixscroll_com(_request, _urlopen):
    assert verify_manifest(VALID_MANIFEST) is True


@mock.patch("urllib.request.urlopen", side_effect=_block_matrixscroll_http)
@mock.patch("urllib.request.Request", wraps=urllib.request.Request)
def test_verify_commit_envelope_never_fetches_matrixscroll_com(_request, _urlopen, tmp_path):
    from matrixscroll.git import build_commit_envelope, sign_commit_envelope

    sha = _init_repo(tmp_path)
    envelope = sign_commit_envelope(build_commit_envelope(commit_sha=sha, root=tmp_path))
    result = verify_commit_envelope_for_sha(envelope, sha, root=tmp_path)
    assert result.ok is True


@mock.patch("urllib.request.urlopen", side_effect=_block_matrixscroll_http)
@mock.patch("urllib.request.Request", wraps=urllib.request.Request)
def test_verify_envelope_range_never_fetches_matrixscroll_com(_request, _urlopen, tmp_path):
    from matrixscroll.git import build_commit_envelope, save_envelope, sign_commit_envelope

    sha = _init_repo(tmp_path)
    (tmp_path / "file2.txt").write_text("y\n", encoding="utf-8")
    subprocess.run(["git", "add", "file2.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "second"], cwd=tmp_path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    envelope = sign_commit_envelope(build_commit_envelope(commit_sha=head, root=tmp_path))
    save_envelope(envelope, tmp_path)
    summary = verify_envelope_range(sha, head, source="local", root=tmp_path, allow_empty=False)
    assert summary["ok"] is True


@mock.patch("urllib.request.urlopen", side_effect=_block_matrixscroll_http)
@mock.patch("urllib.request.Request", wraps=urllib.request.Request)
def test_sign_manifest_roundtrip_never_fetches_matrixscroll_com(_request, _urlopen):
    signed = sign_manifest({"schema": "matrixscroll.test.v0", "payload": {"a": 1}})
    assert verify_manifest(signed) is True
