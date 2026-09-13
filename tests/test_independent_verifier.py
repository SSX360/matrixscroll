"""The second implementation of the verifier must agree with the SDK.

``tools/independent_verify.py`` re-implements SPEC.md sections 3 to 6 (and the
section 11 overlay when liboqs is present) from the specification text, with a
pure-Python RFC 8032 Ed25519 and its own canonical serializer, and imports
nothing from ``matrixscroll``. These tests hold the two implementations against
each other on the committed vectors and on freshly generated manifests, so that a
divergence in canonical bytes or in a verdict fails CI.
"""

from __future__ import annotations

import base64
import copy
import importlib.util
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import pytest

import matrixscroll
from matrixscroll import crypto_backend
from matrixscroll.canonical import canonical_bytes
from matrixscroll.crypto_backend import pqc_available
from matrixscroll.manifest import sign_manifest, verify_manifest_full
from matrixscroll.providers.emulated import EmulatedProvider

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "independent_verify.py"
VECTORS = ROOT / "vectors"


def _load_tool():
    if not TOOL.is_file():
        # A loud collection error is intended: the second implementation is a release
        # requirement (README, "Ten-minute check for reviewers") and ships in the sdist.
        raise FileNotFoundError(f"{TOOL} is missing; the independent verifier is required, not optional")
    spec = importlib.util.spec_from_file_location("independent_verify", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


iv = _load_tool()


def _fixture_files() -> list[Path]:
    return sorted(f for f in VECTORS.glob("*.json") if not f.name.startswith(("_", "acvp-")))


def test_tool_imports_nothing_from_the_sdk() -> None:
    source = TOOL.read_text(encoding="utf-8")
    imported = [line.split()[1] for line in source.splitlines() if line.startswith(("import ", "from "))]
    assert not any(name == "matrixscroll" or name.startswith("matrixscroll.") for name in imported), imported


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_verdicts_and_canonical_bytes_agree_on_committed_vectors(path: Path) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    sdk_verdict = matrixscroll.verify_manifest(manifest)
    tool_verdict, reason = iv.verify_ed25519_block(manifest)
    assert tool_verdict == sdk_verdict, f"{path.name}: SDK {sdk_verdict}, tool {tool_verdict} ({reason})"
    expected = iv.expected_from_name(path)
    assert expected is not None, f"{path.name}: no expectation can be read from the file name prefix"
    assert tool_verdict == expected
    assert iv.canonical_bytes(manifest) == canonical_bytes(manifest)


def test_command_line_run_over_vectors_exits_zero() -> None:
    proc = subprocess.run([sys.executable, str(TOOL), "--json", str(VECTORS)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    results = json.loads(proc.stdout)["results"]
    assert len(results) == len(_fixture_files())
    assert all(r["agrees"] is True for r in results)


_ALPHABET = "abc xyz 0123 \"quote\" back\\slash tab\t newline\n é ü 汉字 🎉   \x01 \x7f ﷺ"


# Floats whose shortest round-trip spelling exercises every branch of the repr
# algorithm: zero and negative zero, the largest and smallest normal values, the
# smallest subnormal, the exponent-notation thresholds (1e16 and 1e-5 in Python's
# repr), and values that are not exactly representable.
_EDGE_FLOATS = [
    0.0,
    -0.0,
    1.0,
    -1.5,
    0.1 + 0.2,
    123456.789,
    1e16,
    9999999999999998.0,
    1e-5,
    0.0001,
    1e-7,
    2.5e300,
    1.7976931348623157e308,
    2.2250738585072014e-308,
    5e-324,
    -5e-324,
    4.9406564584124654e-324,
    1e22,
    1e23,
]


def _random_value(rng: random.Random, depth: int = 0):
    kind = rng.choice(["str", "int", "float", "bool", "none", "list", "dict"]) if depth < 3 else rng.choice(["str", "int", "float", "bool", "none"])
    if kind == "str":
        return "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(0, 12)))
    if kind == "int":
        return rng.randint(-(10**18), 10**18)
    if kind == "float":
        return rng.choice(_EDGE_FLOATS + [float(rng.randint(-1000, 1000)) / 7, rng.random() * 10 ** rng.randint(-310, 308)])
    if kind == "bool":
        return rng.choice([True, False])
    if kind == "none":
        return None
    if kind == "list":
        return [_random_value(rng, depth + 1) for _ in range(rng.randint(0, 4))]
    keys = ["".join(rng.choice(_ALPHABET) for _ in range(rng.randint(1, 6))) for _ in range(rng.randint(0, 5))]
    return {k: _random_value(rng, depth + 1) for k in keys}


def test_canonical_serializers_agree_on_random_documents() -> None:
    rng = random.Random(20260912)
    for _ in range(500):
        doc = {"schema": "matrixscroll.test.v0", "payload": _random_value(rng), "signature": {"drop": "me"}}
        assert iv.canonical_bytes(doc) == canonical_bytes(doc)


def test_canonical_serializers_agree_on_edge_floats() -> None:
    """The SDK encodes floats through json.dumps and the tool through repr(); CPython's
    JSON encoder formats a finite float with float.__repr__, so the two are the same
    algorithm, and this test is where that assumption is checked on the values that
    exercise it (subnormals included)."""
    for value in _EDGE_FLOATS:
        doc = {"x": value, "nested": [value, {"y": value}]}
        assert iv.canonical_bytes(doc) == canonical_bytes(doc), repr(value)


def test_canonical_serializer_rejects_non_finite_floats() -> None:
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError):
            iv.canonical_bytes({"x": bad})
        with pytest.raises(ValueError):
            canonical_bytes({"x": bad})


def test_fresh_signatures_verify_and_tampering_is_detected_by_both(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    provider = EmulatedProvider.load_or_create(tmp_path)
    rng = random.Random(7)
    for _ in range(25):
        manifest = {"schema": "matrixscroll.test.v0", "payload": _random_value(rng)}
        signed = sign_manifest(manifest, provider)
        assert matrixscroll.verify_manifest(signed)
        assert iv.verify_ed25519_block(signed) == (True, "ed25519 signature verifies over the canonical bytes")
        tampered = copy.deepcopy(signed)
        tampered["payload"] = {"changed": True}
        assert not matrixscroll.verify_manifest(tampered)
        assert iv.verify_ed25519_block(tampered)[0] is False


_ED25519_P = 2**255 - 19
_IDENTITY_ENCODING = bytes([1]) + bytes(31)


def _forged_manifest(public_key: bytes, r_value: bytes, s_value: bytes = bytes(32)) -> dict:
    return {
        "schema": "matrixscroll.test.v0",
        "payload": "no private key was used to sign this",
        "signature": {
            "schema": "matrixscroll.signature.v1",
            "algorithm": "ed25519",
            "device_id": iv.device_id(public_key),
            "public_key": base64.b64encode(public_key).decode("ascii"),
            "value": base64.b64encode(r_value + s_value).decode("ascii"),
        },
    }


def test_sdk_small_order_blocklist_matches_the_tool_arithmetic() -> None:
    """The SDK rejects small-order points by a blocklist of encodings; the tool rejects
    them by computing [8]P. The blocklist is regenerated here from the tool's curve
    arithmetic so the two rules cannot drift apart."""
    order_eight = iv._point_decompress(bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05"))
    assert order_eight is not None and iv._has_small_order(order_eight)
    assert not iv._point_equal(iv._point_mul(4, order_eight), iv._IDENTITY)
    torsion_y: set[bytes] = set()
    for k in range(8):
        x, y, z, _ = iv._point_mul(k, order_eight) if k else iv._IDENTITY
        y = y * iv._inv(z) % _ED25519_P
        torsion_y.add(y.to_bytes(32, "little"))
        if y + _ED25519_P < 2**255:  # the non-canonical spelling of the same point
            torsion_y.add((y + _ED25519_P).to_bytes(32, "little"))
    assert torsion_y == set(crypto_backend._ED25519_SMALL_ORDER_Y)
    assert not iv._has_small_order(iv._G)
    assert crypto_backend.ed25519_point_is_acceptable(bytes.fromhex("5866666666666666666666666666666666666666666666666666666666666666"))


@pytest.mark.parametrize(
    ("label", "public_key", "r_value"),
    [
        ("identity key, identity R", _IDENTITY_ENCODING, _IDENTITY_ENCODING),
        ("identity key with the sign bit set", bytes([1]) + bytes(30) + bytes([0x80]), _IDENTITY_ENCODING),
        ("order-2 key", (_ED25519_P - 1).to_bytes(32, "little"), _IDENTITY_ENCODING),
        ("order-4 key", bytes(32), _IDENTITY_ENCODING),
        ("order-8 key", bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05"), _IDENTITY_ENCODING),
        ("non-canonical identity key (y = p + 1)", (_ED25519_P + 1).to_bytes(32, "little"), _IDENTITY_ENCODING),
        ("non-canonical order-4 key (y = p)", _ED25519_P.to_bytes(32, "little"), _IDENTITY_ENCODING),
    ],
)
def test_small_order_and_non_canonical_keys_are_rejected_by_both(label: str, public_key: bytes, r_value: bytes) -> None:
    """With a public key of small order the verification equation holds for R = identity
    and S = 0 whatever the message, so no private key is needed. OpenSSL accepts such
    keys; the SDK and the tool both reject them (as libsodium does), and they agree."""
    manifest = _forged_manifest(public_key, r_value)
    assert matrixscroll.verify_manifest(manifest) is False, label
    assert iv.verify_ed25519_block(manifest)[0] is False, label
    assert crypto_backend.ed25519_verify(public_key, b"any message", r_value + bytes(32)) is False, label


def test_small_order_r_is_rejected_by_both(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    provider = EmulatedProvider.load_or_create(tmp_path)
    signed = sign_manifest({"schema": "matrixscroll.test.v0", "payload": "r"}, provider)
    public_key = base64.b64decode(signed["signature"]["public_key"])
    for r_value in (_IDENTITY_ENCODING, bytes(32), (_ED25519_P - 1).to_bytes(32, "little")):
        forged = copy.deepcopy(signed)
        forged["signature"]["value"] = base64.b64encode(r_value + bytes(32)).decode("ascii")
        assert matrixscroll.verify_manifest(forged) is False
        assert iv.verify_ed25519_block(forged)[0] is False
        assert crypto_backend.ed25519_verify(public_key, iv.canonical_bytes(forged), r_value + bytes(32)) is False


def test_malformed_pqc_blocks_are_invalid_without_liboqs(monkeypatch: pytest.MonkeyPatch) -> None:
    """The structural rules of SPEC.md section 11 do not need the backend, so a malformed
    block is 'invalid' even when liboqs is absent; only the signature check itself can
    be 'not-checked'."""
    monkeypatch.setitem(sys.modules, "oqs", None)  # makes `import oqs` raise ImportError
    base = {"schema": "matrixscroll.test.v0", "payload": "pqc"}
    good_block = {"schema": "matrixscroll.pqc_signature.v1", "algorithm": "ml-dsa-87", "public_key": "AA==", "value": "AA=="}
    assert iv.verify_pqc_blocks({**base, "pqc_signatures": [good_block]})[0] == "not-checked"
    assert iv.verify_pqc_blocks({**base, "pqc_signatures": []})[0] == "invalid"
    assert iv.verify_pqc_blocks({**base, "pqc_signatures": [{**good_block, "schema": "other"}]})[0] == "invalid"
    assert iv.verify_pqc_blocks({**base, "pqc_signatures": [{**good_block, "algorithm": "rsa"}]})[0] == "invalid"
    assert iv.verify_pqc_blocks({**base, "pqc_signatures": [{**good_block, "value": "not base64!"}]})[0] == "invalid"
    assert iv.verify_pqc_blocks({**base, "pqc_signatures": [{**good_block, "public_key": 7}]})[0] == "invalid"
    status, detail = iv.verify_pqc_blocks({**base, "payload": math.inf, "pqc_signatures": [good_block]})
    assert status == "invalid" and "canonical encoding failed" in detail


def test_command_line_fails_on_an_unnamed_invalid_file(tmp_path) -> None:
    unnamed = tmp_path / "manifest.json"
    unnamed.write_text(json.dumps({"schema": "matrixscroll.test.v0", "payload": "unsigned"}), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(TOOL), "--json", str(unnamed)], capture_output=True, text=True, check=False)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)["results"][0]
    assert result["valid"] is False and result["expected"] is None and result["agrees"] is None
    unreadable = tmp_path / "broken.json"
    unreadable.write_text("{not json", encoding="utf-8")
    proc = subprocess.run([sys.executable, str(TOOL), str(unreadable)], capture_output=True, text=True, check=False)
    assert proc.returncode == 1 and "unreadable" in proc.stdout
    valid = next(f for f in _fixture_files() if f.name.startswith("valid_"))
    proc = subprocess.run([sys.executable, str(TOOL), str(valid)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.skipif(not pqc_available(), reason="liboqs PQC backend not installed")
def test_pqc_overlay_is_checked_by_both(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from matrixscroll.pqc import attach_pqc_overlay

    monkeypatch.setenv("MATRIXSCROLL_HOME", str(tmp_path))
    provider = EmulatedProvider.load_or_create(tmp_path)
    signed = attach_pqc_overlay(sign_manifest({"schema": "matrixscroll.test.v0", "payload": "pqc"}, provider), "ml-dsa-87")
    assert verify_manifest_full(signed)
    status, detail = iv.verify_pqc_blocks(signed)
    assert status == "valid", detail
    broken = copy.deepcopy(signed)
    broken["pqc_signatures"][0]["value"] = broken["pqc_signatures"][0]["value"][:-4] + "AAAA"
    assert not verify_manifest_full(broken)
    assert iv.verify_pqc_blocks(broken)[0] == "invalid"
