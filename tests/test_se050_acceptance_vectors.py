"""Acceptance vectors from the completed SSX360 SE050 hardware signer."""

from __future__ import annotations

import base64
import json
import unittest
from pathlib import Path

import matrixscroll
from matrixscroll.canonical import canonical_bytes
from matrixscroll.constants import ALGORITHM, SIGNATURE_SCHEMA
from matrixscroll.providers.emulated import device_id
from matrixscroll.providers.registry import verify

SE050_VECTORS_DIR = Path(__file__).resolve().parent.parent / "vectors" / "se050"


def _load(name: str) -> dict:
    return json.loads((SE050_VECTORS_DIR / name).read_text(encoding="utf-8"))


class SE050AcceptanceVectorTests(unittest.TestCase):
    def test_vector_01_verifies_with_matrixscroll_contract(self):
        manifest = _load("vector_01.json")
        block = manifest["signature"]

        self.assertEqual(manifest.get("schema"), "ssx360.test-vector.v1")
        self.assertEqual(manifest.get("seq"), 1)
        self.assertEqual(block.get("schema"), SIGNATURE_SCHEMA)
        self.assertEqual(block.get("algorithm"), ALGORITHM)
        self.assertEqual(block.get("mode"), "hardware")

        public_key = base64.b64decode(block["public_key"], validate=True)
        self.assertEqual(block["device_id"], device_id(public_key))
        self.assertTrue(matrixscroll.verify_manifest(manifest))

    def test_vector_01_uses_pure_ed25519_over_canonical_bytes(self):
        manifest = _load("vector_01.json")
        block = manifest["signature"]
        signing_input = canonical_bytes(manifest)
        public_key = base64.b64decode(block["public_key"], validate=True)
        signature = base64.b64decode(block["value"], validate=True)

        self.assertEqual(len(signing_input), len(json.dumps(
            {k: v for k, v in manifest.items() if k != "signature"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")))
        self.assertTrue(verify(public_key, signing_input, signature))


if __name__ == "__main__":
    unittest.main()
