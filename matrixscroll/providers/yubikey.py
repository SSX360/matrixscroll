"""YubiKey PIV bridge provider (prototype boundary).

Set MATRIXSCROLL_MODE=yubikey to select this provider. The prototype defines the
interface and availability checks; PKCS#11 signing is not wired until the optional
``matrixscroll[yubikey]`` extra ships.

See docs/yubikey-bridge.md for the full research and rollout plan.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from ..errors import IdentityError
from .base import IdentityProvider

DEFAULT_PIV_SLOT = "9c"


def _default_pkcs11_module() -> str | None:
    if sys.platform == "win32":
        return r"C:\Program Files\Yubico\Yubico PIV Tool\bin\ykcs11.dll"
    if sys.platform == "darwin":
        return "/usr/local/lib/libykcs11.dylib"
    return "/usr/lib/x86_64-linux-gnu/libykcs11.so"


def _pkcs11_module_path() -> str | None:
    env = os.environ.get("MATRIXSCROLL_YKCS11_MODULE", "").strip()
    if env:
        return env
    default = _default_pkcs11_module()
    if default and os.path.isfile(default):
        return default
    return None


def _piv_slot() -> str:
    return os.environ.get("MATRIXSCROLL_PIV_SLOT", DEFAULT_PIV_SLOT).strip() or DEFAULT_PIV_SLOT


class YubiKeyProvider(IdentityProvider):
    """Sign manifest digests via YubiKey PIV + PKCS#11 (prototype)."""

    mode = "yubikey"

    def __init__(self) -> None:
        self._module = _pkcs11_module_path()
        self._slot = _piv_slot()
        self._public_key: bytes | None = None
        self._created_at = ""

    def is_available(self) -> tuple[bool, str | None]:
        if self._module is None:
            return False, "PKCS#11 module not found (set MATRIXSCROLL_YKCS11_MODULE)"
        if not os.path.isfile(self._module):
            return False, f"PKCS#11 module missing: {self._module}"
        try:
            import pkcs11  # type: ignore[import-not-found]  # optional extra
        except ImportError:
            return False, (
                "python-pkcs11 not installed; install matrixscroll[yubikey] when available"
            )
        try:
            lib = pkcs11.lib(self._module)
            tokens = lib.get_tokens()
            if not tokens:
                return False, "no YubiKey token present"
        except Exception as exc:  # pragma: no cover - hardware path
            return False, f"PKCS#11 initialization failed: {exc}"
        return True, None

    def _require_available(self) -> None:
        available, reason = self.is_available()
        if not available:
            raise IdentityError(reason or "YubiKey provider unavailable")

    def public_key_bytes(self) -> bytes:
        self._require_available()
        if self._public_key is not None:
            return self._public_key
        raise IdentityError(
            "YubiKey public key export not implemented in prototype; "
            "use emulated mode or complete PKCS#11 slot read in v0.2.x"
        )

    def sign(self, data: bytes) -> bytes:
        self._require_available()
        raise IdentityError(
            "YubiKey PIV signing not implemented in prototype. "
            "See docs/yubikey-bridge.md for the planned PKCS#11 integration."
        )

    def status_detail(self) -> dict[str, Any]:
        available, reason = self.is_available()
        return {
            "mode": self.mode,
            "available": available,
            "reason": reason,
            "pkcs11_module": self._module,
            "piv_slot": self._slot,
        }
