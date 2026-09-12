"""Shared helpers for the liboqs-dependent test modules."""

from __future__ import annotations


def liboqs_family_enabled(family: str) -> bool:
    """True when this liboqs build ships the family ("ML-DSA" or "SLH-DSA") at all.

    Used to decide between a skip (the build has no such mechanisms) and a failure
    (the build has the family but a Matrix Scroll identifier does not resolve).
    """
    import oqs  # type: ignore[import-untyped]

    enabled = {name.upper().replace("_", "-") for name in oqs.get_enabled_sig_mechanisms()}
    return any(name.startswith(family) for name in enabled)
