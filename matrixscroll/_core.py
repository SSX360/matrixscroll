"""Compatibility shim — prefer importing from matrixscroll submodules directly.

This module re-exports the v0.1.x public surface. It will be removed in v0.3.0.
"""

from __future__ import annotations

from .canonical import canonical_bytes as _canonical
from .constants import ALGORITHM, DEVICE_FILE, SCHEMA, SIGNATURE_SCHEMA
from .errors import IdentityError
from .manifest import sign_manifest, verify_manifest
from .providers.base import IdentityProvider
from .providers.emulated import EmulatedProvider, device_id, store_dir
from .providers.hardware import HardwareProvider
from .providers.registry import (
    get_provider,
    identity_info,
    public_key_b64,
    sign,
    status,
    verify,
)

__all__ = [
    "ALGORITHM",
    "DEVICE_FILE",
    "EmulatedProvider",
    "HardwareProvider",
    "IdentityError",
    "IdentityProvider",
    "SCHEMA",
    "SIGNATURE_SCHEMA",
    "device_id",
    "get_provider",
    "identity_info",
    "public_key_b64",
    "sign",
    "sign_manifest",
    "status",
    "store_dir",
    "verify",
    "verify_manifest",
]
