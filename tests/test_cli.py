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


if __name__ == "__main__":
    unittest.main()
