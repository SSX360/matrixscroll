"""YubiKey PIV bridge provider (prototype boundary).

Set MATRIXSCROLL_MODE=yubikey to select this provider. The prototype defines the
interface and availability checks; PKCS#11 signing is wired when the optional
``matrixscroll[yubikey]`` extra is installed or when ``MATRIXSCROLL_YKCS11_MOCK=1``.

See docs/yubikey-bridge.md for the full research and rollout plan.
"""

from __future__ import annotations

import hashlib
import os
import sys
from typing import Any

from ..errors import IdentityError
from .base import IdentityProvider

DEFAULT_PIV_SLOT = "9c"
_MOCK_PRIVATE_KEY: Any | None = None


def _mock_private_key():
    global _MOCK_PRIVATE_KEY
    if _MOCK_PRIVATE_KEY is None:
        from cryptography.hazmat.primitives.asymmetric import ec

        _MOCK_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
    return _MOCK_PRIVATE_KEY


def _mock_sign(digest: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import Prehashed

    key = _mock_private_key()
    return key.sign(digest, ec.ECDSA(Prehashed(hashes.SHA256())))


def _default_pkcs11_module() -> str | None:
    if sys.platform == "win32":
        return r"C:\Program Files\Yubico\Yubico PIV Tool\bin\ykcs11.dll"
    if sys.platform == "darwin":
        return "/usr/local/lib/libykcs11.dylib"
    return "/usr/lib/x86_64-linux-gnu/libykcs11.so"


def _pkcs11_module_path() -> str | None:
    if os.environ.get("MATRIXSCROLL_YKCS11_MOCK", "").strip().lower() in {"1", "true", "yes"}:
        return "mock"
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
    algorithm = "ecdsa-p256"
    digest = "sha256"

    def __init__(self) -> None:
        self._module = _pkcs11_module_path()
        self._slot = _piv_slot()
        self._public_key: bytes | None = None
        self._created_at = ""
        self._mock = self._module == "mock"

    def signing_input(self, canonical: bytes) -> bytes:
        return hashlib.sha256(canonical).digest()

    def is_available(self) -> tuple[bool, str | None]:
        if self._mock:
            return True, None
        if self._module is None:
            return False, "PKCS#11 module not found (set MATRIXSCROLL_YKCS11_MODULE)"
        if not os.path.isfile(self._module):
            return False, f"PKCS#11 module missing: {self._module}"
        try:
            import pkcs11  # type: ignore[import-not-found]
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
        if self._mock:
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

            key = _mock_private_key()
            self._public_key = key.public_key().public_bytes(
                Encoding.DER,
                PublicFormat.SubjectPublicKeyInfo,
            )
            return self._public_key
        return self._pkcs11_public_key_bytes()

    def _pkcs11_public_key_bytes(self) -> bytes:
        import pkcs11  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from cryptography.hazmat.primitives.serialization import load_der_public_key

        lib = pkcs11.lib(self._module)
        tokens = lib.get_tokens()
        if not tokens:
            raise IdentityError("no YubiKey token present")
        token = tokens[0]
        pin = os.environ.get("MATRIXSCROLL_PIV_PIN", "")
        with token.open(user_pin=pin or None) as session:
            public = session.get_key(
                object_class=pkcs11.ObjectClass.PUBLIC_KEY,
                key_type=pkcs11.KeyType.EC,
            )
            if public is None:
                private = session.get_key(
                    object_class=pkcs11.ObjectClass.PRIVATE_KEY,
                    key_type=pkcs11.KeyType.EC,
                )
                if private is None:
                    raise IdentityError(f"no EC key in PIV slot {self._slot}")
                # Some tokens expose public key via private key attributes.
                pub_bytes = getattr(private, "EC_POINT", None)
                if pub_bytes is None:
                    raise IdentityError(
                        "YubiKey EC public key not found; set MATRIXSCROLL_YKCS11_MOCK=1 for dev"
                    )
                self._public_key = bytes(pub_bytes)
                return self._public_key
            der = bytes(public[pkcs11.Attribute.VALUE])
            key = load_der_public_key(der)
            self._public_key = key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
            return self._public_key

    def _sign_pkcs11(self, digest: bytes) -> bytes:
        import pkcs11  # type: ignore[import-not-found]

        lib = pkcs11.lib(self._module)
        tokens = lib.get_tokens()
        token = tokens[0]
        pin = os.environ.get("MATRIXSCROLL_PIV_PIN", "")
        with token.open(user_pin=pin or None) as session:
            private = session.get_key(
                object_class=pkcs11.ObjectClass.PRIVATE_KEY,
                key_type=pkcs11.KeyType.EC,
            )
            if private is None:
                raise IdentityError(f"no key in PIV slot {self._slot}")
            return bytes(private.sign(digest, mechanism=pkcs11.Mechanism.ECDSA))

    def sign(self, data: bytes) -> bytes:
        self._require_available()
        if self._mock:
            return _mock_sign(data)
        try:
            return self._sign_pkcs11(data)
        except IdentityError:
            raise
        except Exception as exc:  # pragma: no cover - hardware path
            raise IdentityError(f"YubiKey PIV signing failed: {exc}") from exc

    def status_detail(self) -> dict[str, Any]:
        available, reason = self.is_available()
        return {
            "mode": self.mode,
            "available": available,
            "reason": reason,
            "pkcs11_module": self._module,
            "piv_slot": self._slot,
            "mock": self._mock,
            "algorithm": self.algorithm,
            "digest": self.digest,
        }
