"""Formal spec registry and Scroll Gate trace alignment tests."""

from __future__ import annotations

import unittest

from matrixscroll.formal import FORMAL_PROPERTIES, by_hypothesis_id, property_ids
from matrixscroll.gate import verify_envelope_range


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


class ScrollGateTraceTests(unittest.TestCase):
    """Implementation scenarios aligned with formal/tla/ScrollGate.tla invariants."""

    def test_empty_range_passes(self):
        summary = verify_envelope_range("HEAD", "HEAD", source="local")
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["total"], 0)

    def test_enforce_semantics_all_valid_required(self):
        """F-G3: if all commits valid, gate passes — tested via empty range baseline."""
        summary = verify_envelope_range("HEAD", "HEAD", source="local")
        self.assertTrue(summary["ok"])


if __name__ == "__main__":
    unittest.main()
