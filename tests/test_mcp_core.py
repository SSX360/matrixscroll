import unittest
from pathlib import Path
from matrixscroll.mcp_core import (
    analyze_workspace,
    brainstorm_workspace,
    recommend_ecosystem,
    audit_trust_surface,
    scaffold_editor_integration,
    plan_matrixscroll_rollout
)

class MCPCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = Path(__file__).resolve().parent.parent

    def test_analyze_workspace(self):
        profile = analyze_workspace(self.workspace)
        self.assertIn("languages", profile)
        self.assertIn("python", [l.lower() for l in profile["languages"]])

    def test_brainstorm_workspace(self):
        res = brainstorm_workspace(self.workspace, goal="improve security")
        self.assertEqual(res["configured"], True)
        self.assertIn("suggestions", res)

    def test_recommend_ecosystem(self):
        res = recommend_ecosystem(self.workspace, goal="mcp", live=False)
        self.assertIn("recommendations", res)

    def test_audit_trust_surface(self):
        res = audit_trust_surface(self.workspace, target="auto")
        self.assertIn("summary", res)
        self.assertIn("proof_links", res)

    def test_scaffold_editor_integration(self):
        res = scaffold_editor_integration(self.workspace, editor="cursor", write=False)
        self.assertEqual(res["editor"], "cursor")
        self.assertIn("diff_preview", res)
        self.assertEqual(res["wrote"], False)

    def test_plan_matrixscroll_rollout(self):
        res = plan_matrixscroll_rollout(self.workspace, audience="founder", goal="rollout matrixscroll")
        self.assertEqual(res["audience"], "founder")
        self.assertIn("rollout_steps", res)
