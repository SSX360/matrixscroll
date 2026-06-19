"""Executable proof for the agentic-AI guidance mapping.

These tests intentionally validate documentation and control metadata. They make
sure "we meet the guidance" remains tied to concrete files in the repo instead
of becoming a stale marketing claim.
"""

import json
import tempfile
import unittest
from pathlib import Path

import matrixscroll
from matrixscroll import EmulatedProvider

ROOT = Path(__file__).resolve().parent.parent
CONTROLS = ROOT / "controls" / "agentic_ai_controls.json"
DOC = ROOT / "docs" / "AGENTIC_AI_SECURITY.md"
EXAMPLE = ROOT / "examples" / "agentic_ai_evidence_manifest.json"


class AgenticGuidanceControlMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(CONTROLS.read_text(encoding="utf-8"))
        cls.controls = cls.matrix["controls"]
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_control_matrix_has_expected_schema_and_sources(self):
        self.assertEqual(self.matrix["schema"], "matrixscroll.agentic_ai_controls.v1")
        self.assertGreaterEqual(len(self.matrix["sources"]), 4)
        self.assertTrue(any("media.defense.gov" in src for src in self.matrix["sources"]))
        self.assertTrue(any("cisa.gov" in src for src in self.matrix["sources"]))
        self.assertTrue(any("ncsc.gov" in src for src in self.matrix["sources"]))

    def test_every_control_has_required_fields_and_repo_evidence(self):
        seen = set()
        for control in self.controls:
            with self.subTest(control=control.get("id")):
                self.assertRegex(control["id"], r"^AAI-[0-9]{2}$")
                self.assertNotIn(control["id"], seen)
                seen.add(control["id"])
                for key in ("title", "guidance", "matrixscroll_control", "goes_beyond"):
                    self.assertGreater(len(control[key]), 20)
                self.assertGreaterEqual(len(control["evidence_paths"]), 2)
                for rel in control["evidence_paths"]:
                    self.assertTrue((ROOT / rel).exists(), rel)

    def test_human_doc_mentions_every_control_id(self):
        for control in self.controls:
            self.assertIn(control["id"], self.doc)


class AgenticEvidenceManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_manifest_contains_guidance_critical_fields(self):
        task = self.manifest["task"]
        least_privilege = self.manifest["least_privilege"]
        accountability = self.manifest["human_accountability"]
        risk = self.manifest["risk_controls"]
        self.assertEqual(task["classification"], "low-risk bounded pilot")
        self.assertIn("deploy", task["denied_operations"])
        self.assertIn("temporary", least_privilege["credential_type"])
        self.assertTrue(least_privilege["revocation_required"])
        self.assertTrue(accountability["reviewer_required"])
        self.assertIn("kill_switch", accountability)
        self.assertTrue(risk["threat_model_completed"])
        self.assertFalse(risk["sensitive_data_allowed"])
        self.assertTrue(risk["prompt_injection_assumed"])

    def test_example_manifest_signs_and_detects_scope_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = EmulatedProvider.load_or_create(Path(tmp))
            signed = matrixscroll.sign_manifest(self.manifest, provider)
        self.assertTrue(matrixscroll.verify_manifest(signed))
        signed["task"]["allowed_operations"].append("deploy")
        self.assertFalse(matrixscroll.verify_manifest(signed))

    def test_example_manifest_covers_all_declared_controls(self):
        required = set(self.manifest["policy"]["required_controls"])
        matrix = json.loads(CONTROLS.read_text(encoding="utf-8"))
        available = {control["id"] for control in matrix["controls"]}
        self.assertEqual(required, available)


if __name__ == "__main__":
    unittest.main()
