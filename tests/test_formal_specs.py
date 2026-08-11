"""Formal spec registry and Scroll Gate trace alignment tests."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from matrixscroll.formal import FORMAL_PROPERTIES, by_hypothesis_id, property_ids
from matrixscroll.gate import verify_envelope_range

TLA_DIR = Path(__file__).resolve().parents[1] / "formal" / "tla"


class FormalRegistryTests(unittest.TestCase):
    def test_property_ids_unique(self):
        ids = property_ids()
        self.assertEqual(len(ids), len(set(ids)))

    def test_hypothesis_bridge_covers_crypto(self):
        bridged = {p.hypothesis_id for p in FORMAL_PROPERTIES if p.hypothesis_id}
        self.assertTrue({"P1", "P2", "P3", "P4"}.issubset(bridged))

    def test_p1_has_formal_and_hypothesis(self):
        props = by_hypothesis_id("P1")
        self.assertTrue(any(p.id == "F-P1" for p in props))


class FormalRegistryMatchesSpecsTests(unittest.TestCase):
    """Every registered property must exist in its module and be checked by TLC.

    Without this, renaming or dropping a TLA+ property leaves the registry and
    formal/PROPERTIES.md silently pointing at nothing.
    """

    def test_registered_property_defined_in_module(self):
        for prop in FORMAL_PROPERTIES:
            with self.subTest(prop.id):
                module = TLA_DIR / prop.module
                self.assertTrue(module.is_file(), f"{prop.module} missing")
                pattern = rf"^{re.escape(prop.invariant)}\s*=="
                self.assertRegex(
                    module.read_text(encoding="utf-8"),
                    re.compile(pattern, re.MULTILINE),
                    f"{prop.id}: {prop.invariant} not defined in {prop.module}",
                )

    def test_registered_property_checked_by_tlc_config(self):
        for prop in FORMAL_PROPERTIES:
            with self.subTest(prop.id):
                cfg = TLA_DIR / prop.module.replace(".tla", ".cfg")
                self.assertTrue(cfg.is_file(), f"{cfg.name} missing")
                keyword = "PROPERTY" if prop.invariant.startswith("Prop_") else "INVARIANT"
                pattern = rf"^{keyword}\s+{re.escape(prop.invariant)}\s*$"
                self.assertRegex(
                    cfg.read_text(encoding="utf-8"),
                    re.compile(pattern, re.MULTILINE),
                    f"{prop.id}: {prop.invariant} not checked in {cfg.name}",
                )

    def test_registered_property_listed_in_properties_doc(self):
        doc = (TLA_DIR.parent / "PROPERTIES.md").read_text(encoding="utf-8")
        for prop in FORMAL_PROPERTIES:
            with self.subTest(prop.id):
                self.assertIn(f"`{prop.invariant}`", doc)
                self.assertIn(f"**{prop.id}**", doc)


class ScrollGateTraceTests(unittest.TestCase):
    """Implementation scenarios aligned with formal/tla/ScrollGate.tla invariants."""

    def test_empty_range_fails_closed(self):
        """F-G5: `AllValid` is vacuously true over an empty range, and does not pass."""
        summary = verify_envelope_range("HEAD", "HEAD", source="local")
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["total"], 0)
        self.assertTrue(summary["empty_range"])

    def test_empty_range_opt_out_is_labelled(self):
        """A caller may accept an empty range, and the result still says it was empty."""
        summary = verify_envelope_range("HEAD", "HEAD", source="local", allow_empty=True)
        self.assertTrue(summary["ok"])
        self.assertTrue(summary["empty_range"])


if __name__ == "__main__":
    unittest.main()
