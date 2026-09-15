"""Fail-closed FIPS-oriented algorithm policy switch.

When ``MATRIXSCROLL_FIPS=1``, only algorithms routed through the classical
``cryptography`` stack are allowed (today: ``ed25519``). Liboqs-only paths are
rejected with :class:`~matrixscroll.errors.IdentityError`.

This is a deployment policy switch, not CMVP validation and not a claim that
the process is a FIPS 140-3 module. See ``docs/CAVP_CMVP_ROUTE.md``.
Evidence mapping only; not a certification claim.
"""

from __future__ import annotations

import os
from typing import Iterable

from .errors import IdentityError

FIPS_ENV = "MATRIXSCROLL_FIPS"

# Algorithms permitted when FIPS mode is on. Extend only when a path is routed
# through a cryptography (pyca) backend the deployment treats as FIPS-oriented.
_FIPS_ALLOWED: frozenset[str] = frozenset({"ed25519"})

# Identifiers that imply a liboqs-only (or non-cryptography) production path.
_LIBOQS_ONLY: frozenset[str] = frozenset(
    {
        "ml-dsa-44",
        "ml-dsa-65",
        "ml-dsa-87",
        "slh-dsa-sha2-128s",
        "slh-dsa-sha2-128f",
        "slh-dsa-sha2-256s",
        "slh-dsa-sha2-256f",
        "ml-kem-512",
        "ml-kem-768",
        "ml-kem-1024",
        "composite-ml-dsa-65-ed25519",
    }
)


def fips_enabled(env: dict[str, str] | None = None) -> bool:
    """Return True when ``MATRIXSCROLL_FIPS`` is set to ``1``."""
    source: Iterable[tuple[str, str]]
    if env is None:
        raw = os.environ.get(FIPS_ENV, "")
    else:
        raw = env.get(FIPS_ENV, "")
    return str(raw).strip() == "1"


def assert_algorithm_allowed(alg: str, *, env: dict[str, str] | None = None) -> str:
    """Return ``alg`` if allowed under the current FIPS policy.

    When FIPS mode is off, any non-empty algorithm string passes through (callers
    still enforce their own allowlists). When FIPS mode is on, only
    cryptography-routed algorithms in ``_FIPS_ALLOWED`` are accepted; liboqs-only
    names raise ``IdentityError``.
    """
    name = (alg or "").strip().lower()
    if not name:
        raise IdentityError("algorithm must be a non-empty string")

    if not fips_enabled(env):
        return name

    if name in _LIBOQS_ONLY or name not in _FIPS_ALLOWED:
        raise IdentityError(
            f"MATRIXSCROLL_FIPS=1 rejects algorithm {name!r}. "
            "Only cryptography-routed algorithms are allowed "
            f"(currently: {sorted(_FIPS_ALLOWED)}). "
            "This policy switch is not CMVP validation."
        )
    return name


__all__ = [
    "FIPS_ENV",
    "assert_algorithm_allowed",
    "fips_enabled",
]
