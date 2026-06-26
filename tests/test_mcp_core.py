"""Tests for provenance-only Matrix Scroll MCP helpers."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from matrixscroll.gate import verify_envelope_range
from matrixscroll.git import (
    build_commit_envelope,
    install_hooks,
    save_envelope,
    sign_commit_envelope,
)
from matrixscroll.mcp_core import create_envelope, status, verify_envelope


class MCPProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(self._mkdtemp())
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "mcp@test.local"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "MCP Test"], cwd=self.repo, check=True)
        (self.repo / "README.md").write_text("mcp test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.repo, check=True, capture_output=True)

    @staticmethod
    def _mkdtemp() -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="matrixscroll-mcp-")

    def test_status_reports_hooks_and_envelopes(self) -> None:
        install_hooks(self.repo)
        envelope = sign_commit_envelope(build_commit_envelope(commit_sha="HEAD", root=self.repo))
        save_envelope(envelope, self.repo)
        res = status(str(self.repo))
        self.assertTrue(res["ok"])
        self.assertGreaterEqual(res["envelope_count"], 1)
        self.assertTrue(res["hooks"]["post-commit"])

    def test_create_and_verify_envelope(self) -> None:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        created = create_envelope(
            str(self.repo),
            commit_sha=sha,
            actor_type="agent",
            tool="pytest",
        )
        self.assertTrue(created["ok"])
        self.assertTrue(created["signed"])
        verified = verify_envelope(str(self.repo), commit_sha=sha)
        self.assertTrue(verified["ok"], verified)

    def test_verify_pr_range_local(self) -> None:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        envelope = sign_commit_envelope(build_commit_envelope(commit_sha=sha, root=self.repo))
        save_envelope(envelope, self.repo)
        summary = verify_envelope_range(sha, sha, source="local", root=self.repo)
        self.assertTrue(summary["ok"])


if __name__ == "__main__":
    unittest.main()
