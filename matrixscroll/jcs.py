"""RFC 8785-oriented canonicalisation wrapper (v1 delegates to SPEC §4).

JSON Canonicalization Scheme (JCS, RFC 8785) is the intended v2 signing input.
Matrix Scroll v1 envelopes use the existing ``canonical_bytes`` rules in
``matrixscroll.canonical`` (sorted keys, compact separators, UTF-8). This
module provides a stable import path and ``canonical_bytes_jcs`` alias so
callers can migrate without chasing internal module moves.

Migration note: when a v2 schema ships, replace the body of
``canonical_bytes_jcs`` with a strict RFC 8785 encoder and keep the v1 path
behind an explicit schema gate.
"""

from __future__ import annotations

from typing import Any

from .canonical import canonical_bytes


def canonical_bytes_jcs(payload: dict[str, Any]) -> bytes:
    """Return canonical signing bytes (v1: delegates to ``canonical_bytes``).

    Alias name documents the RFC 8785 migration target. Behaviour today matches
    SPEC.md section 4 Ed25519 encoding.
    """
    return canonical_bytes(payload)


# Explicit alias for callers that prefer the RFC name.
jcs_bytes = canonical_bytes_jcs
