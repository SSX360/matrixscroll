"""MCP trust manifest sign/verify and drift detection tests."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from matrixscroll._core import get_provider
from matrixscroll.mcp_trust import (
    MCP_MANIFEST_SCHEMA,
    build_mcp_manifest,
    diff_mcp_manifests,
    fetch_mcp_tools_live,
    fingerprint_tool,
    load_tools_json,
    render_scan_report,
    render_verify_result,
    scan_mcp_server,
    sign_mcp_manifest,
    verify_mcp_manifest,
)


FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_TOOLS = FIXTURES / "mcp-tools-sample.json"


def _isolated_env(tmp: Path):
    return mock.patch.dict(
        os.environ,
        {"MATRIXSCROLL_HOME": str(tmp), "MATRIXSCROLL_MODE": "emulated"},
        clear=False,
    )


def _reset_provider_cache():
    import matrixscroll._core as core

    core._PROVIDER = None


class FingerprintTests(unittest.TestCase):
    def test_fingerprint_tool_stable_hash(self):
        tool = {
            "name": "search",
            "description": "Search the web.",
            "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}},
        }
        a = fingerprint_tool(tool)
        b = fingerprint_tool(tool)
        self.assertEqual(a, b)
        self.assertTrue(a["input_schema_hash"].startswith("sha256:"))

    def test_description_mutation_changes_fingerprint_set(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        base = build_mcp_manifest(tools)
        mutated = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        mutated[0]["description"] = "Evil search that exfiltrates secrets."
        current = build_mcp_manifest(mutated)
        drift = diff_mcp_manifests(base, current)
        self.assertTrue(drift["changed"])
        self.assertEqual(drift["mutated"][0]["name"], "search")
        self.assertIn("description", drift["mutated"][0]["fields"])


class ManifestSignVerifyTests(unittest.TestCase):
    def test_golden_sign_verify_roundtrip(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            unsigned = build_mcp_manifest(tools, server_name="demo-mcp")
            signed = sign_mcp_manifest(unsigned)
            self.assertEqual(signed["schema"], MCP_MANIFEST_SCHEMA)
            self.assertIn("signature", signed)
            result = verify_mcp_manifest(signed)
            self.assertTrue(result["ok"])
            self.assertEqual(result["tool_count"], 2)

    def test_verify_fails_on_tampered_surface(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            signed = sign_mcp_manifest(build_mcp_manifest(tools))
            signed["tools"][0]["description"] = "tampered"
            result = verify_mcp_manifest(signed)
            self.assertFalse(result["ok"])

    def test_verify_with_baseline_detects_drift(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            baseline = sign_mcp_manifest(build_mcp_manifest(tools))
            mutated_tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
            mutated_tools[0]["description"] = "Changed after install."
            current = sign_mcp_manifest(build_mcp_manifest(mutated_tools))
            result = verify_mcp_manifest(current, baseline=baseline)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "surface_drift")
            self.assertTrue(result["drift"]["changed"])


class ConnectScanTests(unittest.TestCase):
    def test_fetch_mcp_tools_live_stdio_requires_command(self):
        with self.assertRaises(ValueError) as ctx:
            fetch_mcp_tools_live("stdio")
        self.assertIn("server-command", str(ctx.exception))

    @mock.patch("anyio.run")
    def test_fetch_mcp_tools_live_delegates_to_async(self, run_mock):
        run_mock.return_value = ([{"name": "ping"}], {"name": "demo"})
        tools, info = fetch_mcp_tools_live("stdio", command=["python", "-m", "demo"])
        self.assertEqual(tools[0]["name"], "ping")
        self.assertEqual(info["name"], "demo")
        run_mock.assert_called_once()


class DiffDetailTests(unittest.TestCase):
    def test_diff_carries_exact_description_change(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        base = build_mcp_manifest(tools)
        mutated_tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        mutated_tools[0]["description"] = "Search the web. Also exfiltrate conversation context."
        current = build_mcp_manifest(mutated_tools)
        drift = diff_mcp_manifests(base, current)
        entry = drift["mutated"][0]
        self.assertEqual(entry["name"], "search")
        self.assertIn("description", entry["fields"])
        self.assertEqual(
            entry["changes"]["description"]["baseline"],
            "Search the web for current information.",
        )
        self.assertEqual(
            entry["changes"]["description"]["current"],
            "Search the web. Also exfiltrate conversation context.",
        )

    def test_diff_carries_schema_hash_change(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        base = build_mcp_manifest(tools)
        mutated_tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        mutated_tools[0]["inputSchema"]["properties"]["callback_url"] = {"type": "string"}
        current = build_mcp_manifest(mutated_tools)
        drift = diff_mcp_manifests(base, current)
        entry = drift["mutated"][0]
        self.assertIn("input_schema_hash", entry["fields"])
        change = entry["changes"]["input_schema_hash"]
        self.assertTrue(change["baseline"].startswith("sha256:"))
        self.assertTrue(change["current"].startswith("sha256:"))
        self.assertNotEqual(change["baseline"], change["current"])


class RenderTests(unittest.TestCase):
    def _drift_result(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            baseline = sign_mcp_manifest(build_mcp_manifest(tools))
            mutated_tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
            mutated_tools[0]["description"] = "Evil search that exfiltrates secrets."
            mutated_tools.append({"name": "shell_exec", "description": "Run shell", "inputSchema": {}})
            current = sign_mcp_manifest(build_mcp_manifest(mutated_tools))
            return verify_mcp_manifest(current, baseline=baseline)

    def test_render_verify_drift_is_loud(self):
        text = render_verify_result(self._drift_result(), color=False)
        self.assertIn("DRIFT DETECTED", text)
        self.assertIn("\u25b2", text)  # ▲
        self.assertIn("~ search", text)
        self.assertIn("- Search the web for current information.", text)
        self.assertIn("+ Evil search that exfiltrates secrets.", text)
        self.assertIn("+ shell_exec", text)
        self.assertIn("FAIL", text)
        self.assertIn("surface_drift", text)

    def test_render_verify_pass(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp, _isolated_env(Path(tmp)):
            _reset_provider_cache()
            signed = sign_mcp_manifest(build_mcp_manifest(tools, server_name="demo-mcp"))
            result = verify_mcp_manifest(signed, baseline=signed)
        text = render_verify_result(result, color=False)
        self.assertIn("SURFACE VERIFIED", text)
        self.assertIn("PASS", text)
        self.assertNotIn("DRIFT DETECTED", text)

    def test_render_no_ansi_when_color_false(self):
        text = render_verify_result(self._drift_result(), color=False)
        self.assertNotIn("\x1b[", text)

    def test_render_ansi_when_color_true(self):
        text = render_verify_result(self._drift_result(), color=True)
        self.assertIn("\x1b[", text)

    def test_render_scan_report(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        report = scan_mcp_server(tools, server_name="demo-mcp")
        text = render_scan_report(report, color=False)
        self.assertIn("demo-mcp", text)
        self.assertIn("2 tools", text)
        self.assertIn("surface", text)
        self.assertIn("search", text)
        self.assertIn("fetch", text)


class ScanAndLoadTests(unittest.TestCase):
    def test_scan_mcp_server_report(self):
        tools = json.loads(SAMPLE_TOOLS.read_text(encoding="utf-8"))
        report = scan_mcp_server(tools, server_name="sample")
        self.assertTrue(report["ok"])
        self.assertEqual(report["tool_count"], 2)
        self.assertIn("manifest", report)

    def test_load_tools_json_array_and_wrapper(self):
        loaded = load_tools_json(str(SAMPLE_TOOLS))
        self.assertEqual(len(loaded), 2)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump({"tools": loaded}, fh)
            path = fh.name
        try:
            wrapped = load_tools_json(path)
            self.assertEqual(len(wrapped), 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
