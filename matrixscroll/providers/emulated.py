"""Software-emulated Matrix Scroll identity provider."""

from __future__ import annotations

import base64
import binascii
import json
import os
import time
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ..constants import DEVICE_FILE, DIR_MODE, FILE_MODE, SCHEMA, SEED_LEN
from ..crypto_backend import (
    ed25519_private_seed,
    ed25519_public_key_bytes,
    ed25519_sign,
    generate_ed25519_private_key,
    load_ed25519_private_key,
    sha256_hex,
)
from ..errors import IdentityError
from .base import IdentityProvider

def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _write_secret(path: Path, text: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(str(path), flags, FILE_MODE)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)
    try:
        os.chmod(path, FILE_MODE)
    except OSError:
        pass


def device_id(public_key: bytes) -> str:
    digest = sha256_hex(public_key).upper()
    return f"MS-{digest[:4]}-{digest[4:8]}"


def store_dir() -> Path:
    env = os.environ.get("MATRIXSCROLL_HOME", "").strip()
    return Path(env).expanduser() if env else (Path.home() / ".matrixscroll")


class EmulatedProvider(IdentityProvider):
    mode = "emulated"

    def __init__(self, private_key: Ed25519PrivateKey, created_at: str) -> None:
        self._key = private_key
        self._created_at = created_at

    @classmethod
    def load_or_create(cls, directory: Path | None = None) -> "EmulatedProvider":
        directory = directory or store_dir()
        path = directory / DEVICE_FILE
        if path.is_file():
            return cls._load(path)

        key = generate_ed25519_private_key()
        created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pub = ed25519_public_key_bytes(key)
        doc = {
            "schema": SCHEMA,
            "mode": cls.mode,
            "created_at": created,
            "device_id": device_id(pub),
            "public_key": _b64(pub),
            "private_key": _b64(ed25519_private_seed(key)),
        }
        directory.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(directory, DIR_MODE)
        except OSError:
            pass
        _write_secret(path, json.dumps(doc, indent=2) + "\n")
        return cls(key, created)

    @classmethod
    def _load(cls, path: Path) -> "EmulatedProvider":
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            seed = _unb64(doc["private_key"])
        except (OSError, ValueError, KeyError, AttributeError, binascii.Error) as exc:
            raise IdentityError(f"device key store at {path} is unreadable: {exc}")
        if len(seed) != SEED_LEN:
            raise IdentityError(
                f"device key store at {path} has an invalid {len(seed)}-byte seed"
            )
        try:
            key = load_ed25519_private_key(seed)
        except ValueError as exc:
            raise IdentityError(f"device key store at {path} is corrupt: {exc}")
        return cls(key, doc.get("created_at", ""))

    def public_key_bytes(self) -> bytes:
        return ed25519_public_key_bytes(self._key)

    def sign(self, data: bytes) -> bytes:
        return ed25519_sign(self._key, data)

    @property
    def created_at(self) -> str:
        return self._created_at
