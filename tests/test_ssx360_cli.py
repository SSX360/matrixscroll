"""Smoke tests for SSX360 platform CLI wrappers."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest import mock

from matrixscroll import ssx360_cli


class Ssx360CliTests(unittest.TestCase):
    def test_help_exits_nonzero(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ssx360_cli.main([])
        self.assertEqual(rc, 1)

    def test_normalize_framework_aliases(self):
        self.assertEqual(ssx360_cli._normalize_framework("soc2"), "SOC2")
        self.assertEqual(ssx360_cli._normalize_framework("ISO-27001"), "ISO27001")
        self.assertEqual(ssx360_cli._normalize_framework("nist-ssdf"), "NIST-SSDF")

    def test_ledger_main_requires_export(self):
        with self.assertRaises(SystemExit):
            ssx360_cli.ledger_main([])

    @mock.patch.dict("os.environ", {}, clear=True)
    @mock.patch("matrixscroll.gate.export_envelope_bundle")
    def test_ledger_export_local(self, export_mock):
        export_mock.return_value = {"bundle": ".matrixscroll/audit-export", "count": 1}
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ssx360_cli.ledger_main(["--export", "SOC2"])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["framework"], "SOC2")

    @mock.patch.dict("os.environ", {}, clear=True)
    @mock.patch("matrixscroll.gate.verify_envelope_range")
    def test_check_local_range(self, verify_mock):
        verify_mock.return_value = {"ok": True, "verified_count": 2, "total": 2}
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ssx360_cli.main(["check", "--base", "abc123", "--head", "def456", "--source", "local"])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
