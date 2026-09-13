"""TPM-backed signing provider (Windows/Linux prototype boundary).

Set MATRIXSCROLL_MODE=tpm to select this provider. Uses software-sealed Ed25519
identity in mock/dev mode; probes platform TPM readiness for production path.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ..constants import DEVICE_FILE, SCHEMA
from ..crypto_backend import (
    ed25519_private_seed,
    ed25519_public_key_bytes,
    ed25519_sign,
    generate_ed25519_private_key,
    load_ed25519_private_key,
)
from ..errors import IdentityError
from .base import IdentityProvider
from .emulated import EmulatedProvider, device_id, store_dir


def _tpm_ready() -> tuple[bool, str | None]:
    if os.environ.get("MATRIXSCROLL_TPM_MOCK", "").strip().lower() in {"1", "true", "yes"}:
        return True, None
    if sys.platform == "win32":
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "(Get-Tpm).TpmReady"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip().lower() == "true":
            return True, None
        return False, "Windows TPM not ready (Get-Tpm returned false)"
    if shutil_which("tpm2_getrandom"):
        result = subprocess.run(["tpm2_getrandom", "8"], capture_output=True, check=False)
        if result.returncode == 0:
            return True, None
        return False, "tpm2_getrandom failed"
    return False, "TPM tools not found; set MATRIXSCROLL_TPM_MOCK=1 for dev"


def shutil_which(cmd: str) -> str | None:
    from shutil import which

    return which(cmd)


class TpmProvider(IdentityProvider):
    """TPM-sealed Ed25519 identity (mock path ships in v0.2.x)."""

    mode = "tpm"
    algorithm = "ed25519"

    def __init__(self) -> None:
        self._mock = os.environ.get("MATRIXSCROLL_TPM_MOCK", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        self._key: Ed25519PrivateKey | None = None
        self._created_at = ""
        self._store = store_dir() / "tpm"
        self._path = self._store / DEVICE_FILE

    def is_available(self) -> tuple[bool, str | None]:
        if self._mock:
            return True, None
        return _tpm_ready()

    def _require_available(self) -> None:
        available, reason = self.is_available()
        if not available:
            raise IdentityError(reason or "TPM provider unavailable")

    def _load_or_create(self) -> Ed25519PrivateKey:
        if self._key is not None:
            return self._key
        self._require_available()
        self._store.mkdir(parents=True, exist_ok=True)
        if self._path.is_file():
            doc = json.loads(self._path.read_text(encoding="utf-8"))
            seed = bytes.fromhex(doc["private_key_hex"])
            self._created_at = doc.get("created_at", "")
            self._key = load_ed25519_private_key(seed)
            return self._key
        key = generate_ed25519_private_key()
        created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pub = ed25519_public_key_bytes(key)
        doc = {
            "schema": SCHEMA,
            "mode": self.mode,
            "created_at": created,
            "device_id": device_id(pub),
            "private_key_hex": ed25519_private_seed(key).hex(),
            "mock": self._mock,
        }
        self._path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        self._created_at = created
        self._key = key
        return key

    def public_key_bytes(self) -> bytes:
        key = self._load_or_create()
        return ed25519_public_key_bytes(key)

    def sign(self, data: bytes) -> bytes:
        key = self._load_or_create()
        return ed25519_sign(key, data)

    @property
    def created_at(self) -> str:
        if not self._created_at and self._path.is_file():
            doc = json.loads(self._path.read_text(encoding="utf-8"))
            self._created_at = doc.get("created_at", "")
        return self._created_at

    def status_detail(self) -> dict[str, Any]:
        available, reason = self.is_available()
        return {
            "mode": self.mode,
            "available": available,
            "reason": reason,
            "mock": self._mock,
            "store": str(self._store),
            "algorithm": self.algorithm,
        }


__all__ = ["TpmProvider"]
