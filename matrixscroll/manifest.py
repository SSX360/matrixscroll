"""Manifest signing and verification."""

from __future__ import annotations

import base64
import binascii
import copy
import time
from typing import Any

from .canonical import canonical_bytes
from .constants import ALGORITHM, SIGNATURE_SCHEMA
from .errors import IdentityError
from .providers.emulated import device_id
from .providers.registry import get_provider, identity_info, verify
from .signing_modes import (
    accepts_primary_algorithm,
    assert_primary_signing_supported,
    overlay_algorithm_for_mode,
    primary_algorithm_for_mode,
    resolve_primary_mode,
)


def _provider_algorithm(provider) -> str:
    return getattr(provider, "algorithm", ALGORITHM)


def _sign_ed25519_block(
    signed: dict[str, Any],
    provider,
) -> dict[str, Any]:
    info = identity_info(provider)
    algorithm = _provider_algorithm(provider)
    if algorithm != ALGORITHM:
        raise IdentityError(
            "Matrix Scroll Ed25519 primary path requires an Ed25519 provider. "
            f"Provider {provider.mode!r} reports unsupported algorithm {algorithm!r}."
        )
    canonical = canonical_bytes(signed)
    signing_input = provider.signing_input(canonical) if hasattr(provider, "signing_input") else canonical
    signature_value = base64.b64encode(provider.sign(signing_input)).decode("ascii")
    return {
        "schema": SIGNATURE_SCHEMA,
        "algorithm": algorithm,
        "device_id": info["device_id"],
        "public_key": info["public_key"],
        "mode": info["mode"],
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "value": signature_value,
    }


def _sign_mldsa_primary_block(
    signed: dict[str, Any],
    *,
    algorithm: str = "ml-dsa-87",
) -> dict[str, Any]:
    from .crypto_backend import pqc_sign
    from .pqc import load_pqc_keypair

    algo, pub, sec = load_pqc_keypair(algorithm)
    message = canonical_bytes(signed)
    signature = pqc_sign(algo, sec, message)
    # Device id is SHA-256 of the primary public key bytes (SPEC §3), algorithm-agnostic.
    did = device_id(pub)
    return {
        "schema": SIGNATURE_SCHEMA,
        "algorithm": algo,
        "device_id": did,
        "public_key": base64.b64encode(pub).decode("ascii"),
        "mode": "emulated",
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "value": base64.b64encode(signature).decode("ascii"),
    }


def sign_manifest(
    manifest: dict[str, Any], provider=None
) -> dict[str, Any]:
    """Sign a manifest under the active primary mode.

    Default: Ed25519 (v1). With ``MATRIXSCROLL_PRIMARY_ALG=ml-dsa-87``, the
    primary ``signature`` block is ML-DSA-87 (requires ``matrixscroll[pqc]``).
    Composite mode keeps Ed25519 primary and attaches ML-DSA-65 as overlay.
    """
    mode = assert_primary_signing_supported()
    provider = provider or get_provider()
    signed = copy.deepcopy(manifest)
    signed.pop("signature", None)
    signed.pop("pqc_signatures", None)

    if mode == "ml-dsa-87":
        primary_alg = primary_algorithm_for_mode(mode)
        signed["signature"] = _sign_mldsa_primary_block(signed, algorithm=primary_alg)
        return signed

    signed["signature"] = _sign_ed25519_block(signed, provider)
    overlay = overlay_algorithm_for_mode(mode)
    if overlay:
        from .pqc import attach_pqc_overlay

        return attach_pqc_overlay(signed, overlay)
    return signed


def verify_manifest(manifest: dict[str, Any]) -> bool:
    if not isinstance(manifest, dict):
        return False
    block = manifest.get("signature")
    if not isinstance(block, dict):
        return False
    if block.get("schema") != SIGNATURE_SCHEMA:
        return False
    algorithm = block.get("algorithm", ALGORITHM)
    if not accepts_primary_algorithm(algorithm if isinstance(algorithm, str) else None):
        return False
    public_key = block.get("public_key")
    signature = block.get("value")
    if not isinstance(public_key, str) or not isinstance(signature, str):
        return False
    try:
        public_key_bytes = base64.b64decode(public_key.encode("ascii"), validate=True)
        signature_bytes = base64.b64decode(signature.encode("ascii"), validate=True)
    except (ValueError, binascii.Error):
        return False
    if block.get("device_id") != device_id(public_key_bytes):
        return False
    try:
        signing_input = canonical_bytes(manifest)
    except (TypeError, ValueError):
        return False

    if algorithm == ALGORITHM:
        return verify(public_key_bytes, signing_input, signature_bytes)

    # Primary ML-DSA / other PQC algorithm on the signature block.
    from .crypto_backend import pqc_available, pqc_verify

    if not pqc_available():
        return False
    try:
        return pqc_verify(str(algorithm), public_key_bytes, signing_input, signature_bytes)
    except Exception:  # noqa: BLE001 - verify must never raise to callers
        return False


def verify_manifest_pqc(manifest: dict[str, Any]) -> bool:
    """Verify optional PQC overlay blocks (§11). Returns True if absent or all valid."""
    from .pqc import verify_pqc_signatures

    return verify_pqc_signatures(manifest)


def sign_manifest_with_pqc(
    manifest: dict[str, Any],
    provider=None,
    *,
    pqc_algorithm: str | None = None,
) -> dict[str, Any]:
    """Sign under the active primary mode, then attach an optional PQC overlay.

    When the primary mode is already ``ml-dsa-87``, the overlay is skipped unless
    ``pqc_algorithm`` is set explicitly to a different algorithm.
    """
    signed = sign_manifest(manifest, provider)
    mode = resolve_primary_mode()
    if mode == "ml-dsa-87" and not pqc_algorithm:
        return signed
    from .pqc import attach_pqc_overlay, configured_pqc_algorithm

    algo = pqc_algorithm or configured_pqc_algorithm()
    if not algo:
        return signed
    # Do not double-attach the same algorithm already used as primary.
    primary = (signed.get("signature") or {}).get("algorithm")
    if primary == algo:
        return signed
    return attach_pqc_overlay(signed, algo)


def verify_manifest_full(manifest: dict[str, Any]) -> bool:
    """Verify primary signature and optional PQC overlay."""
    return verify_manifest(manifest) and verify_manifest_pqc(manifest)
