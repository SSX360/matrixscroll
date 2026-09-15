"""Primary signing mode helpers (Ed25519 default; ML-DSA-87 opt-in).

``schema`` and ``algorithm`` live inside the ``signature`` block for every
primary mode. Set ``MATRIXSCROLL_PRIMARY_ALG=ml-dsa-87`` (requires
``matrixscroll[pqc]``) to sign and verify ML-DSA-87 as the primary block.
``composite-ml-dsa-65-ed25519`` signs Ed25519 as primary and attaches an
ML-DSA-65 overlay in one call.
"""

from __future__ import annotations

import os
from typing import Any

from .constants import ALGORITHM, DEFAULT_PQC_ALGORITHM
from .errors import IdentityError

PRIMARY_MODES: tuple[str, ...] = (
    "ed25519",
    "ml-dsa-87",
    "composite-ml-dsa-65-ed25519",
)

PRIMARY_ALG_ENV = "MATRIXSCROLL_PRIMARY_ALG"
DEFAULT_PRIMARY_MODE = "ed25519"

# Algorithms accepted on the primary signature.algorithm field.
PRIMARY_ALGORITHMS: frozenset[str] = frozenset(
    {
        ALGORITHM,
        "ml-dsa-87",
        "ml-dsa-65",
        "ml-dsa-44",
    }
)


def resolve_primary_mode(env: dict[str, str] | None = None) -> str:
    """Return the configured primary signing mode (default ``ed25519``)."""
    source = env if env is not None else os.environ
    raw = str(source.get(PRIMARY_ALG_ENV, DEFAULT_PRIMARY_MODE) or DEFAULT_PRIMARY_MODE)
    mode = raw.strip().lower()
    if mode not in PRIMARY_MODES:
        return DEFAULT_PRIMARY_MODE
    return mode


def algorithm_covered_by_signature(block: dict[str, Any] | None) -> bool:
    """True when schema and algorithm are present inside the signature block."""
    if not isinstance(block, dict):
        return False
    schema = block.get("schema")
    algorithm = block.get("algorithm")
    return isinstance(schema, str) and bool(schema) and isinstance(algorithm, str) and bool(algorithm)


def assert_primary_signing_supported(mode: str | None = None) -> str:
    """Validate that the selected primary mode can run on this install."""
    resolved = mode if mode is not None else resolve_primary_mode()
    if resolved == DEFAULT_PRIMARY_MODE:
        return resolved
    from .crypto_backend import pqc_available

    if not pqc_available():
        raise IdentityError(
            "ML-DSA primary signing requires matrixscroll[pqc] (liboqs-python). "
            f"MATRIXSCROLL_PRIMARY_ALG={resolved!r} cannot run without it."
        )
    return resolved


def primary_algorithm_for_mode(mode: str | None = None) -> str:
    """Map a primary mode name to the algorithm string stamped on signature."""
    resolved = mode if mode is not None else resolve_primary_mode()
    if resolved == "ml-dsa-87":
        return "ml-dsa-87"
    if resolved == "composite-ml-dsa-65-ed25519":
        return ALGORITHM
    return ALGORITHM


def overlay_algorithm_for_mode(mode: str | None = None) -> str | None:
    """Return overlay algorithm for composite mode, else None."""
    resolved = mode if mode is not None else resolve_primary_mode()
    if resolved == "composite-ml-dsa-65-ed25519":
        return "ml-dsa-65"
    return None


def accepts_primary_algorithm(algorithm: str | None) -> bool:
    if not algorithm:
        return False
    return algorithm.strip().lower() in PRIMARY_ALGORITHMS


# Keep DEFAULT_PQC_ALGORITHM imported for callers that want the Category 5 default.
_ = DEFAULT_PQC_ALGORITHM
