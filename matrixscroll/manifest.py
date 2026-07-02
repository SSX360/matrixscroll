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


def _provider_algorithm(provider) -> str:
    return getattr(provider, "algorithm", ALGORITHM)


def sign_manifest(
    manifest: dict[str, Any], provider=None
) -> dict[str, Any]:
    provider = provider or get_provider()
    algorithm = _provider_algorithm(provider)
    if algorithm != ALGORITHM:
        raise IdentityError(
            "Matrix Scroll v1 signs canonical manifest bytes with Ed25519 only. "
            f"Provider {provider.mode!r} reports unsupported algorithm {algorithm!r}."
        )
    info = identity_info(provider)
    signed = copy.deepcopy(manifest)
    signed.pop("signature", None)
    canonical = canonical_bytes(signed)
    signing_input = provider.signing_input(canonical) if hasattr(provider, "signing_input") else canonical
    signature_value = base64.b64encode(provider.sign(signing_input)).decode("ascii")
    block: dict[str, Any] = {
        "schema": SIGNATURE_SCHEMA,
        "algorithm": algorithm,
        "device_id": info["device_id"],
        "public_key": info["public_key"],
        "mode": info["mode"],
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "value": signature_value,
    }
    signed["signature"] = block
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
    if algorithm != ALGORITHM:
        return False
    return verify(public_key_bytes, signing_input, signature_bytes)


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
    """Sign Ed25519 (required) then attach optional PQC overlay."""
    signed = sign_manifest(manifest, provider)
    from .pqc import attach_pqc_overlay, configured_pqc_algorithm

    algo = pqc_algorithm or configured_pqc_algorithm()
    if not algo:
        return signed
    return attach_pqc_overlay(signed, algo)


def verify_manifest_full(manifest: dict[str, Any]) -> bool:
    """Verify Ed25519 and optional PQC overlay."""
    return verify_manifest(manifest) and verify_manifest_pqc(manifest)
