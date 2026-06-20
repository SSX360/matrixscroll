#!/usr/bin/env python3
"""Generate signed example manifests for docs and CI."""

from __future__ import annotations

import json
from pathlib import Path

import matrixscroll

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"


def sign_file(name: str) -> None:
    src = EXAMPLES / name
    dst = EXAMPLES / name.replace(".json", ".signed.json")
    data = json.loads(src.read_text(encoding="utf-8"))
    signed = matrixscroll.sign_manifest(data)
    dst.write_text(json.dumps(signed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert matrixscroll.verify_manifest(signed)
    print(f"signed {dst.name}")


def main() -> None:
    sign_file("commit-envelope.json")
    sign_file("release-manifest.json")
    sign_file("agentic_ai_evidence_manifest.json")


if __name__ == "__main__":
    main()
