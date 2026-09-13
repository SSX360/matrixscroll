"""Conformance vectors. Every implementation of Matrix Scroll should pass
this exact set of fixtures from `vectors/`. The Python reference implementation
running this test serves as the canonical expected behavior."""

import json
import unittest
from pathlib import Path

import matrixscroll

VECTORS_DIR = Path(__file__).resolve().parent.parent / "vectors"


def _load(name: str) -> dict:
    return json.loads((VECTORS_DIR / name).read_text(encoding="utf-8"))


class ValidVectorTests(unittest.TestCase):
    def test_valid_simple_manifest_verifies(self):
        self.assertTrue(matrixscroll.verify_manifest(_load("valid_simple.json")))

    def test_valid_nested_manifest_verifies(self):
        self.assertTrue(matrixscroll.verify_manifest(_load("valid_nested.json")))

    def test_valid_unicode_manifest_verifies(self):
        self.assertTrue(matrixscroll.verify_manifest(_load("valid_unicode.json")))


class TamperedVectorTests(unittest.TestCase):
    def test_tampered_field_fails(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("tampered_field.json")))

    def test_tampered_nested_fails(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("tampered_nested.json")))

    def test_tampered_signature_value_fails(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("tampered_signature.json")))

    def test_tampered_schema_fails(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("tampered_schema.json")))

    def test_tampered_algorithm_fails(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("tampered_algorithm.json")))

    def test_tampered_device_id_fails(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("tampered_device_id.json")))

    def test_malformed_public_key_fails(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("tampered_public_key.json")))


class UnsignedVectorTests(unittest.TestCase):
    def test_unsigned_manifest_rejected(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("unsigned_no_block.json")))

    def test_signature_block_without_value_rejected(self):
        self.assertFalse(matrixscroll.verify_manifest(_load("unsigned_empty_block.json")))


if __name__ == "__main__":
    unittest.main()
