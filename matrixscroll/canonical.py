"""Deterministic canonical JSON encoding for Matrix Scroll manifests."""

from __future__ import annotations

import json
from typing import Any


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    """Return deterministic signing bytes per SPEC.md section 4."""
    body = {k: v for k, v in payload.items() if k != "signature"}
    return json.dumps(
        body,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
