import os
import stat
import tempfile
import unittest
from pathlib import Path

import matrixscroll
from matrixscroll import EmulatedProvider, HardwareProvider, IdentityError
from matrixscroll._core import DEVICE_FILE, _canonical


def _provider(directory: Path) -> EmulatedProvider:
    return EmulatedProvider.load_or_create(directory)


class IdentityPersistenceTests(unittest.TestCase):
    def test_same_device_id_recovered_across_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            first = matrixscroll.identity_info(_provider(d))
            second = matrixscroll.identity_info(_provider(d))
            self.assertEqual(first["device_id"], second["device_id"])
            self.assertEqual(first["public_key"], second["public_key"])

    def test_device_id_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = matrixscroll.identity_info(_provider(Path(tmp)))
            self.assertRegex(info["device_id"], r"^MS-[0-9A-F]{4}-[0-9A-F]{4}$")

    def test_identity_info_excludes_private_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = matrixscroll.identity_info(_provider(Path(tmp)))
            self.assertNotIn("private_key", info)


class StatusSurfaceTests(unittest.TestCase):
    def test_status_emulated_is_backward_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _provider(Path(tmp))
            info = matrixscroll.identity_info(p)
            status = matrixscroll.status(p)
            self.assertTrue(status["available"])
            self.assertNotIn("reason", status)
            for key in ("schema", "device_id", "public_key", "algorithm", "mode", "created_at"):
                self.assertEqual(status[key], info[key])

    def test_status_hardware_reports_unavailable_without_raising(self):
        status = matrixscroll.status(HardwareProvider())
        self.assertFalse(status["available"])
        self.assertEqual(status["mode"], "hardware")
        self.assertIn("reason", status)
        self.assertNotIn("device_id", status)
        self.assertNotIn("public_key", status)

    def test_identity_info_still_raises_for_unavailable_provider(self):
        with self.assertRaises(IdentityError):
            matrixscroll.identity_info(HardwareProvider())


class CryptoIntegrityTests(unittest.TestCase):
    def test_sign_verify_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _provider(Path(tmp))
            pub = matrixscroll.public_key_b64(p)
            sig = matrixscroll.sign(b"release-42", p)
            self.assertTrue(matrixscroll.verify(pub, b"release-42", sig))

    def test_verify_rejects_tampered_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _provider(Path(tmp))
            pub = matrixscroll.public_key_b64(p)
            sig = matrixscroll.sign(b"release-42", p)
            self.assertFalse(matrixscroll.verify(pub, b"release-43", sig))

    def test_verify_rejects_tampered_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _provider(Path(tmp))
            pub = matrixscroll.public_key_b64(p)
            sig = bytearray(matrixscroll.sign(b"data", p))
            sig[0] ^= 0x01
            self.assertFalse(matrixscroll.verify(pub, b"data", bytes(sig)))

    def test_verify_rejects_mismatched_public_key(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            signer = _provider(Path(a))
            other = matrixscroll.public_key_b64(_provider(Path(b)))
            sig = matrixscroll.sign(b"data", signer)
            self.assertFalse(matrixscroll.verify(other, b"data", sig))


class ManifestSigningTests(unittest.TestCase):
    def _nested_manifest(self) -> dict:
        return {
            "run_id": "r1",
            "meta": {"z": 1, "a": {"deep": [3, 2, 1]}},
            "kpis": [{"label": "rate", "actual": 66.7}],
        }

    def test_sign_and_verify_nested_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _provider(Path(tmp))
            signed = matrixscroll.sign_manifest(self._nested_manifest(), p)
            self.assertTrue(matrixscroll.verify_manifest(signed))

    def test_verify_detects_nested_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _provider(Path(tmp))
            signed = matrixscroll.sign_manifest(self._nested_manifest(), p)
            signed["meta"]["a"]["deep"][0] = 99
            self.assertFalse(matrixscroll.verify_manifest(signed))

    def test_verify_manifest_without_signature_block(self):
        self.assertFalse(matrixscroll.verify_manifest({"run_id": "r1"}))

    def test_signed_manifest_is_deep_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = self._nested_manifest()
            signed = matrixscroll.sign_manifest(manifest, _provider(Path(tmp)))
            manifest["meta"]["a"]["deep"][0] = 99
            self.assertTrue(matrixscroll.verify_manifest(signed))


class StrictVerificationTests(unittest.TestCase):
    def _signed(self) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            return matrixscroll.sign_manifest({"release": "v0.1.0"}, _provider(Path(tmp)))

    def test_rejects_wrong_signature_schema(self):
        signed = self._signed()
        signed["signature"]["schema"] = "matrixscroll.signature.v999"
        self.assertFalse(matrixscroll.verify_manifest(signed))

    def test_rejects_wrong_algorithm(self):
        signed = self._signed()
        signed["signature"]["algorithm"] = "ed448"
        self.assertFalse(matrixscroll.verify_manifest(signed))

    def test_rejects_mismatched_device_id(self):
        signed = self._signed()
        signed["signature"]["device_id"] = "MS-0000-0000"
        self.assertFalse(matrixscroll.verify_manifest(signed))

    def test_rejects_missing_public_key_without_raising(self):
        signed = self._signed()
        signed["signature"].pop("public_key")
        self.assertFalse(matrixscroll.verify_manifest(signed))

    def test_rejects_malformed_public_key_without_raising(self):
        signed = self._signed()
        signed["signature"]["public_key"] = "not base64!!"
        self.assertFalse(matrixscroll.verify_manifest(signed))

    def test_rejects_non_dict_manifest_without_raising(self):
        self.assertFalse(matrixscroll.verify_manifest([]))  # type: ignore[arg-type]


class CanonicalTests(unittest.TestCase):
    def test_key_order_independent(self):
        a = _canonical({"b": 1, "a": {"y": 2, "x": 1}})
        b = _canonical({"a": {"x": 1, "y": 2}, "b": 1})
        self.assertEqual(a, b)

    def test_signature_block_excluded(self):
        base = {"run_id": "r1"}
        withsig = {"run_id": "r1", "signature": {"value": "abc"}}
        self.assertEqual(_canonical(base), _canonical(withsig))

    def test_unicode_is_ascii_escaped(self):
        out = _canonical({"name": "café"})
        self.assertEqual(out, b'{"name":"caf\\u00e9"}')

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            _canonical({"x": float("nan")})


class EdgeCaseTests(unittest.TestCase):
    def test_corrupted_key_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / DEVICE_FILE
            path.write_text("{ not valid json", encoding="utf-8")
            with self.assertRaises(IdentityError):
                EmulatedProvider.load_or_create(Path(tmp))

    def test_invalid_seed_length_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / DEVICE_FILE
            path.write_text('{"private_key": "QUJD"}', encoding="utf-8")
            with self.assertRaises(IdentityError):
                EmulatedProvider.load_or_create(Path(tmp))

    @unittest.skipIf(os.name == "nt", "POSIX file modes not enforced on Windows")
    def test_private_key_file_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            _provider(Path(tmp))
            path = Path(tmp) / DEVICE_FILE
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
