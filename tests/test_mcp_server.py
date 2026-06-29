import unittest
import tempfile
import subprocess
import json
import asyncio
from pathlib import Path

from matrixscroll.mcp import (
    create_envelope,
    verify_envelope,
    verify_pr_range,
    publish_notes,
    status,
    audit_export,
    mcp,
)


def _schema_description_coverage(input_schema: dict) -> float:
    props = (input_schema or {}).get("properties") or {}
    if not props:
        return 100.0
    with_desc = sum(1 for spec in props.values() if (spec or {}).get("description"))
    return (with_desc / len(props)) * 100.0


class MCPToolDefinitionTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_schema_description_coverage(self):
        tools = await mcp.list_tools()
        self.assertGreaterEqual(len(tools), 9)
        for tool in tools:
            coverage = _schema_description_coverage(tool.inputSchema or {})
            self.assertGreaterEqual(
                coverage,
                80.0,
                msg=f"{tool.name} schema description coverage {coverage:.0f}%",
            )

    async def test_tool_annotations_present(self):
        tools = await mcp.list_tools()
        for tool in tools:
            self.assertIsNotNone(
                tool.annotations,
                msg=f"{tool.name} missing MCP annotations",
            )
            ann = tool.annotations
            self.assertIsNotNone(ann.readOnlyHint, msg=f"{tool.name} missing readOnlyHint")
            self.assertIsNotNone(ann.destructiveHint, msg=f"{tool.name} missing destructiveHint")


class MCPServerTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmpdir.name).resolve()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.workspace, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "agent@matrixscroll.com"], cwd=self.workspace, check=True)
        subprocess.run(["git", "config", "user.name", "Agent Attester"], cwd=self.workspace, check=True)
        
        # Create an initial commit so we have a HEAD
        test_file = self.workspace / "test.txt"
        test_file.write_text("Hello World", encoding="utf-8")
        subprocess.run(["git", "add", "test.txt"], cwd=self.workspace, check=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=self.workspace, check=True)
        
        self.first_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.workspace, capture_output=True, text=True, check=True
        ).stdout.strip()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_status(self):
        res = status(str(self.workspace))
        self.assertEqual(res.get("ok"), True)
        self.assertEqual(res["config"].get("actor_type"), "human")
        self.assertIn("envelope_count", res)

    def test_create_envelope_and_verify(self):
        # Create a signed scope manifest first
        from matrixscroll.manifest import sign_manifest
        signed_scope = sign_manifest({"task": "bounded-pilot"})
        scope_file = self.workspace / "agent-scope.json"
        scope_file.write_text(json.dumps(signed_scope), encoding="utf-8")

        # Stage a new change
        test_file = self.workspace / "test.txt"
        test_file.write_text("Hello World Updated", encoding="utf-8")
        subprocess.run(["git", "add", "test.txt"], cwd=self.workspace, check=True)

        # Create envelope (pre-commit, staged state)
        res = create_envelope(
            workspace=str(self.workspace),
            actor_type="agent",
            tool="test-runner",
            agent_scope="agent-scope.json",
            commit_sha=""
        )
        self.assertEqual(res["ok"], True)
        self.assertIn("path", res)
        self.assertIn("envelope", res)

        # Verify the generated envelope
        envelope = res["envelope"]
        self.assertEqual(envelope["provenance"]["actor_type"], "agent")
        self.assertEqual(envelope["provenance"]["tool"], "test-runner")
        self.assertEqual(envelope["provenance"]["agent_scope"], "agent-scope.json")

        # Now commit the changes
        subprocess.run(["git", "commit", "-m", "feat: agent updated text"], cwd=self.workspace, check=True)
        second_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.workspace, capture_output=True, text=True, check=True
        ).stdout.strip()

        # Let's save the envelope with the actual commit SHA
        envelope["commit"]["actual_id"] = second_sha
        
        # Re-sign and save the envelope
        from matrixscroll.git import sign_commit_envelope, save_envelope
        signed = sign_commit_envelope(envelope)
        save_envelope(signed, self.workspace)

        # Verify envelope using verify_envelope tool
        verify_res = verify_envelope(workspace=str(self.workspace), commit_sha=second_sha)
        self.assertEqual(verify_res.get("ok"), True)
        self.assertEqual(verify_res.get("actor_type"), "agent")

        # Verify PR range (first_sha..second_sha)
        range_res = verify_pr_range(workspace=str(self.workspace), base=self.first_sha, head=second_sha, source="local")
        self.assertEqual(range_res["ok"], True)
        self.assertEqual(range_res["verified_count"], 1)

        # Publish notes
        publish_res = publish_notes(workspace=str(self.workspace), base=self.first_sha, head=second_sha)
        self.assertEqual(publish_res["ok"], True)
        self.assertEqual(publish_res["published"], 1)

        # Audit export
        export_dir = self.workspace / "audit_bundle"
        export_res = audit_export(
            workspace=str(self.workspace),
            base=self.first_sha,
            head=second_sha,
            output_dir=str(export_dir)
        )
        self.assertEqual(export_res["ok"], True)
        self.assertEqual(export_res["bundle"]["exported"], 1)
        self.assertTrue((export_dir / f"{second_sha}.json").is_file())
