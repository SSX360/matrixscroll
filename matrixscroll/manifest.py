"""Manifest signing and verification."""

from __future__ import annotations

import base64
import binascii
import copy
import time
from typing import Any

from .canonical import canonical_bytes
from .constants import ALGORITHM, SIGNATURE_SCHEMA
from .providers.emulated import device_id
from .providers.registry import get_provider, identity_info, verify


def sign_manifest(
    manifest: dict[str, Any], provider=None
) -> dict[str, Any]:
    provider = provider or get_provider()
    info = identity_info(provider)
    signed = copy.deepcopy(manifest)
    signed.pop("signature", None)
    signature_value = base64.b64encode(provider.sign(canonical_bytes(signed))).decode("ascii")
    signed["signature"] = {
        "schema": SIGNATURE_SCHEMA,
        "algorithm": ALGORITHM,
        "device_id": info["device_id"],
        "public_key": info["public_key"],
        "mode": info["mode"],
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "value": signature_value,
    }
    return signed


def verify_manifest(manifest: dict[str, Any]) -> bool:
    if not isinstance(manifest, dict):
        return False
    block = manifest.get("signature")
    if not isinstance(block, dict):
        return False
    if block.get("schema") != SIGNATURE_SCHEMA or block.get("algorithm") != ALGORITHM:
        return False
    public_key = block.get("public_key")
    signature = block.get("value")
    if not isinstance(public_key, str) or not isinstance(signature, str):
        return False
    try:
        public_key_bytes = base64.b64decode(public_key.encode("ascii"), validate=True)
    except (ValueError, binascii.Error):
        return False
    if block.get("device_id") != device_id(public_key_bytes):
        return False
    try:
        signing_input = canonical_bytes(manifest)
    except (TypeError, ValueError):
        return False
    return verify(public_key_bytes, signing_input, signature)
