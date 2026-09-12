"""The second implementation of the verifier must agree with the SDK.

``tools/independent_verify.py`` re-implements SPEC.md sections 3 to 6 (and the
section 11 overlay when liboqs is present) from the specification text, with a
pure-Python RFC 8032 Ed25519 and its own canonical serializer, and imports
nothing from ``matrixscroll``. These tests hold the two implementations against
each other on the committed vectors and on freshly generated manifests, so that a
divergence in canonical bytes or in a verdict fails CI.
"""

from __future__ import annotations

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
from matrixscroll.canonical import canonical_bytes
from matrixscroll.crypto_backend import pqc_available
from matrixscroll.manifest import sign_manifest, verify_manifest_full
from matrixscroll.providers.emulated import EmulatedProvider

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "independent_verify.py"
VECTORS = ROOT / "vectors"


def _load_tool():
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
    assert "matrixscroll" not in [line.split()[1] for line in source.splitlines() if line.startswith(("import ", "from "))]
    assert "from matrixscroll" not in source and "import matrixscroll" not in source


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.name)
def test_verdicts_and_canonical_bytes_agree_on_committed_vectors(path: Path) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    sdk_verdict = matrixscroll.verify_manifest(manifest)
    tool_verdict, reason = iv.verify_ed25519_block(manifest)
    assert tool_verdict == sdk_verdict, f"{path.name}: SDK {sdk_verdict}, tool {tool_verdict} ({reason})"
    expected = iv.expected_from_name(path)
    assert expected is not None and tool_verdict == expected
    assert iv.canonical_bytes(manifest) == canonical_bytes(manifest)


def test_command_line_run_over_vectors_exits_zero() -> None:
    proc = subprocess.run([sys.executable, str(TOOL), "--json", str(VECTORS)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    results = json.loads(proc.stdout)["results"]
    assert len(results) == len(_fixture_files())
    assert all(r["agrees"] is True for r in results)


_ALPHABET = "abc xyz 0123 \"quote\" back\\slash tab\t newline\n é ü 汉字 🎉   \x01 \x7f ﷺ"


def _random_value(rng: random.Random, depth: int = 0):
    kind = rng.choice(["str", "int", "float", "bool", "none", "list", "dict"]) if depth < 3 else rng.choice(["str", "int", "float", "bool", "none"])
    if kind == "str":
        return "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(0, 12)))
    if kind == "int":
        return rng.randint(-(10**18), 10**18)
    if kind == "float":
        return rng.choice([0.0, -0.0, 1.0, 1e16, 1e-7, 123456.789, 2.5e300, -1.5, 0.1 + 0.2, float(rng.randint(-1000, 1000)) / 7])
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
