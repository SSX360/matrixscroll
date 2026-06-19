"""Regenerate the Matrix Scroll conformance vectors.

Run from the repo root: ``python vectors/_generate.py``.

The vectors are signed by a deterministic fixture key (stored alongside this
script as ``_fixture_key.json``) so the regenerated files are byte-identical
across machines. The fixture key is a **test-only** Ed25519 keypair — never
reuse it for any real signing.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Make the local package importable when running from source checkout.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey,
)

from matrixscroll._core import (  # noqa: E402
    EmulatedProvider,
    _b64,
    sign_manifest,
)

VECTORS_DIR = Path(__file__).resolve().parent
FIXTURE_KEY = VECTORS_DIR / "_fixture_key.json"

# A fixed RFC 3339 timestamp so regenerations are reproducible.
FIXED_TIME = "2026-06-19T12:00:00Z"


def _load_or_create_fixture_key() -> Ed25519PrivateKey:
    if FIXTURE_KEY.exists():
        doc = json.loads(FIXTURE_KEY.read_text(encoding="utf-8"))
        seed = base64.b64decode(doc["private_key"])
        return Ed25519PrivateKey.from_private_bytes(seed)
    key = Ed25519PrivateKey.generate()
    seed = key.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    pub = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    FIXTURE_KEY.write_text(
        json.dumps(
            {
                "_warning": "TEST-ONLY KEY. Do not use for real signing.",
                "private_key": _b64(seed),
                "public_key": _b64(pub),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return key


def _provider_with_fixture_key(directory: Path) -> EmulatedProvider:
    key = _load_or_create_fixture_key()
    return EmulatedProvider(key, FIXED_TIME)


def _sign(manifest: dict, provider: EmulatedProvider) -> dict:
    """Wrap sign_manifest with a frozen ``signed_at`` so output is stable."""
    original = time.strftime
    try:
        time.strftime = lambda *_args, **_kw: FIXED_TIME  # type: ignore[assignment]
        return sign_manifest(manifest, provider)
    finally:
        time.strftime = original  # type: ignore[assignment]


def _write(name: str, data: dict) -> None:
    (VECTORS_DIR / name).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        provider = _provider_with_fixture_key(Path(tmp))

        simple = _sign({"release": "v0.1.0", "artifact": "matrixscroll-0.1.0.whl"}, provider)
        _write("valid_simple.json", simple)

        nested = _sign(
            {
                "run_id": "r-001",
                "meta": {"z": 1, "a": {"deep": [3, 2, 1]}},
                "kpis": [{"label": "rate", "actual": 66.7}],
            },
            provider,
        )
        _write("valid_nested.json", nested)

        unicode_doc = _sign(
            {"author": "café", "note": "naïve résumé", "emoji": "🔐"}, provider
        )
        _write("valid_unicode.json", unicode_doc)

        tampered_field = dict(simple)
        tampered_field["release"] = "v9.9.9"
        _write("tampered_field.json", tampered_field)

        tampered_nested = json.loads(json.dumps(nested))
        tampered_nested["meta"]["a"]["deep"][0] = 99
        _write("tampered_nested.json", tampered_nested)

        tampered_signature = json.loads(json.dumps(simple))
        sig = bytearray(base64.b64decode(tampered_signature["signature"]["value"]))
        sig[0] ^= 0x01
        tampered_signature["signature"]["value"] = base64.b64encode(bytes(sig)).decode("ascii")
        _write("tampered_signature.json", tampered_signature)

        _write("unsigned_no_block.json", {"release": "v0.1.0", "artifact": "x.whl"})
        _write(
            "unsigned_empty_block.json",
            {"release": "v0.1.0", "signature": {"schema": "matrixscroll.signature.v1"}},
        )

    print(f"Wrote vectors to {VECTORS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
