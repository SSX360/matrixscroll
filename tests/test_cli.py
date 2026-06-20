"""CLI smoke tests. Runs `matrixscroll.cli.main` in-process with an isolated
MATRIXSCROLL_HOME so the user's key store is never touched."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import matrixscroll
from matrixscroll import cli
from matrixscroll._core import get_provider


def _isolated_env(tmp: Path):
    return mock.patch.dict(
        os.environ,
        {"MATRIXSCROLL_HOME": str(tmp), "MATRIXSCROLL_MODE": "emulated"},
        clear=False,
    )


def _reset_provider_cache():
    import matrixscroll._core as core
    core._PROVIDER = None


class _RunMixin:
    def _run(self, args: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(args)
        return rc, buf.getvalue()


class StatusCommandTests(_RunMixin, unittest.TestCase):
    def test_status_prints_available_emulated_identity(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            rc, out = self._run(["status"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertTrue(data["available"])
            self.assertEqual(data["mode"], "emulated")
            self.assertIn("device_id", data)
            self.assertNotIn("private_key", data)

    def test_no_args_defaults_to_status(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            rc, out = self._run([])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertTrue(data["available"])


class VerifyCommandTests(_RunMixin, unittest.TestCase):
    def _signed_path(self, tmp: Path, manifest: dict) -> Path:
        _reset_provider_cache()
        signed = matrixscroll.sign_manifest(manifest, get_provider())
        path = tmp / "manifest.json"
        path.write_text(json.dumps(signed), encoding="utf-8")
        return path

    def test_verify_passes_for_signed_manifest(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            path = self._signed_path(Path(tmp), {"product": "Digital Rain", "release": "test"})
            rc, out = self._run(["verify", str(path)])
            self.assertEqual(rc, 0)
            self.assertTrue(json.loads(out)["ok"])

    def test_verify_fails_for_tampered_manifest(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            signed = matrixscroll.sign_manifest({"product": "Digital Rain"}, get_provider())
            signed["product"] = "Tampered"
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(signed), encoding="utf-8")
            rc, out = self._run(["verify", str(path)])
            self.assertEqual(rc, 2)
            self.assertFalse(json.loads(out)["ok"])

    def test_verify_fails_for_unreadable_manifest(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            rc, out = self._run(["verify", str(Path(tmp) / "missing.json")])
            self.assertEqual(rc, 2)
            self.assertIn("error", json.loads(out))

    def test_verify_accepts_utf8_bom_manifest_from_windows_tools(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            path = self._signed_path(Path(tmp), {"release": "bom-ok"})
            text = path.read_text(encoding="utf-8")
            path.write_text(text, encoding="utf-8-sig")
            rc, out = self._run(["verify", str(path)])
            self.assertEqual(rc, 0)
            self.assertTrue(json.loads(out)["ok"])

    def test_verify_require_mode_passes_for_matching_mode(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            path = self._signed_path(Path(tmp), {"release": "policy-ok"})
            rc, out = self._run(["verify", str(path), "--require-mode", "emulated"])
            self.assertEqual(rc, 0)
            self.assertTrue(json.loads(out)["ok"])

    def test_verify_require_mode_fails_for_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            path = self._signed_path(Path(tmp), {"release": "policy-fail"})
            rc, out = self._run(["verify", str(path), "--require-mode", "hardware"])
            self.assertEqual(rc, 2)
            self.assertIn("required mode hardware", json.loads(out)["error"])

    def test_verify_trusted_keys_passes_for_signer_key(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            path = self._signed_path(Path(tmp), {"release": "trusted-ok"})
            signed = json.loads(path.read_text(encoding="utf-8"))
            pub = signed["signature"]["public_key"]
            keys_path = Path(tmp) / "trusted-keys.json"
            keys_path.write_text(json.dumps({"trusted_public_keys": [pub]}), encoding="utf-8")
            rc, out = self._run(["verify", str(path), "--trusted-keys", str(keys_path)])
            self.assertEqual(rc, 0)
            self.assertTrue(json.loads(out)["ok"])

    def test_verify_trusted_keys_fails_for_unknown_key(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            path = self._signed_path(Path(tmp), {"release": "trusted-fail"})
            keys_path = Path(tmp) / "trusted-keys.json"
            keys_path.write_text(json.dumps({"trusted_public_keys": ["wrong-key"]}), encoding="utf-8")
            rc, out = self._run(["verify", str(path), "--trusted-keys", str(keys_path)])
            self.assertEqual(rc, 2)
            self.assertIn("trusted set", json.loads(out)["error"])


class SignCommandTests(_RunMixin, unittest.TestCase):
    def test_sign_then_verify_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            src = Path(tmp) / "in.json"
            src.write_text(json.dumps({"release": "v0.1.0"}), encoding="utf-8")
            rc, out = self._run(["sign", str(src)])
            self.assertEqual(rc, 0)
            signed = json.loads(out)
            self.assertIn("signature", signed)
            self.assertTrue(matrixscroll.verify_manifest(signed))

    def test_sign_accepts_utf8_bom_manifest_from_windows_tools(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            src = Path(tmp) / "in.json"
            src.write_text(json.dumps({"release": "bom-ok"}), encoding="utf-8-sig")
            rc, out = self._run(["sign", str(src)])
            self.assertEqual(rc, 0)
            self.assertTrue(matrixscroll.verify_manifest(json.loads(out)))


class GateCommandTests(_RunMixin, unittest.TestCase):
    def _init_repo(self, tmp: Path) -> Path:
        import subprocess

        repo = tmp / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Dev"], cwd=repo, check=True)
        return repo

    def _commit(self, repo: Path, name: str, message: str) -> str:
        import subprocess

        (repo / name).write_text(f"{name}\n", encoding="utf-8")
        subprocess.run(["git", "add", name], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    def _save_envelope(self, repo: Path, sha: str) -> None:
        from matrixscroll.git import build_commit_envelope, save_envelope, sign_commit_envelope

        envelope = build_commit_envelope(commit_sha=sha, root=repo)
        save_envelope(sign_commit_envelope(envelope), repo)

    def test_envelope_export_and_verify_range(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            repo = self._init_repo(Path(tmp))
            sha = self._commit(repo, "a.txt", "first")
            self._save_envelope(repo, sha)
            bundle = Path(tmp) / "bundle"
            old_cwd = os.getcwd()
            try:
                os.chdir(repo)
                rc, out = self._run(["envelope-export", "--head", sha, "--output", str(bundle)])
                self.assertEqual(rc, 0)
                data = json.loads(out)
                self.assertEqual(data["exported"], 1)
                rc, out = self._run([
                    "envelope-verify-range",
                    "--head", sha,
                    "--source", "bundle",
                    "--bundle", str(bundle),
                ])
                self.assertEqual(rc, 0)
                summary = json.loads(out)
                self.assertTrue(summary["ok"])
                self.assertEqual(summary["verified_count"], 1)
                self.assertIn("verified_count", summary)
                self.assertIn("results", summary)
            finally:
                os.chdir(old_cwd)

    def test_envelope_verify_range_fails_missing(self):
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            repo = self._init_repo(Path(tmp))
            sha = self._commit(repo, "a.txt", "first")
            old_cwd = os.getcwd()
            try:
                os.chdir(repo)
                rc, out = self._run(["envelope-verify-range", "--head", sha, "--source", "local"])
                self.assertEqual(rc, 2)
                summary = json.loads(out)
                self.assertFalse(summary["ok"])
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
