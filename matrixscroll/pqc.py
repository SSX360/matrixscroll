"""Post-quantum (ML-DSA / SLH-DSA) overlay for Matrix Scroll v1.1."""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any

from .canonical import canonical_bytes_pqc
from .constants import (
    DEFAULT_PQC_ALGORITHM,
    PQC_ALGORITHMS,
    PQC_DIR_NAME,
    PQC_ENV_VAR,
    PQC_IDENTITY_SCHEMA,
    PQC_SIGNATURE_SCHEMA,
)
from .crypto_backend import pqc_available, pqc_backend_info, pqc_sign, pqc_verify
from .errors import IdentityError
from .providers.emulated import store_dir

_OQS_NAME: dict[str, str] = {
    "ml-dsa-44": "ML-DSA-44",
    "ml-dsa-65": "ML-DSA-65",
    "ml-dsa-87": "ML-DSA-87",
    "slh-dsa-sha2-128s": "SLH-DSA-SHA2-128s",
    "slh-dsa-sha2-128f": "SLH-DSA-SHA2-128f",
}


def normalize_pqc_algorithm(value: str | None) -> str:
    if not value:
        return DEFAULT_PQC_ALGORITHM
    algo = value.strip().lower()
    if algo not in PQC_ALGORITHMS:
        raise IdentityError(
            f"Unsupported PQC algorithm {value!r}. "
            f"Choose one of: {', '.join(PQC_ALGORITHMS)}"
        )
    return algo


def configured_pqc_algorithm() -> str | None:
    raw = os.environ.get(PQC_ENV_VAR, "").strip()
    if not raw or raw.lower() in {"0", "false", "off", "no"}:
        return None
    return normalize_pqc_algorithm(raw)


def pqc_store_dir() -> Path:
    path = store_dir() / PQC_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass
    return path


def pqc_key_path(algorithm: str) -> Path:
    return pqc_store_dir() / f"{algorithm}.json"


def load_pqc_keypair(algorithm: str | None = None) -> tuple[str, bytes, bytes]:
    """Return (algorithm, public_key_bytes, secret_key_bytes)."""
    if not pqc_available():
        raise IdentityError(
            "Post-quantum signing is not available on this platform. "
            "Install matrixscroll[pqc] (liboqs-python) or use a cryptography build with ML-DSA support."
        )
    algo = normalize_pqc_algorithm(algorithm or configured_pqc_algorithm())
    path = pqc_key_path(algo)
    if path.is_file():
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != PQC_IDENTITY_SCHEMA:
            raise IdentityError(f"invalid PQC key store schema in {path}")
        if doc.get("algorithm") != algo:
            raise IdentityError(f"PQC key file algorithm mismatch: expected {algo!r}")
        pub = base64.b64decode(doc["public_key"].encode("ascii"), validate=True)
        sec = base64.b64decode(doc["private_key"].encode("ascii"), validate=True)
        return algo, pub, sec
    pub, sec = _generate_keypair(algo)
    path.write_text(
        json.dumps(
            {
                "schema": PQC_IDENTITY_SCHEMA,
                "algorithm": algo,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "public_key": base64.b64encode(pub).decode("ascii"),
                "private_key": base64.b64encode(sec).decode("ascii"),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return algo, pub, sec


def _generate_keypair(algorithm: str) -> tuple[bytes, bytes]:
    import oqs  # type: ignore[import-untyped]

    oqs_name = _OQS_NAME[algorithm]
    with oqs.Signature(oqs_name) as sig:
        public_key = sig.generate_keypair()
        secret_key = sig.export_secret_key()
        return public_key, secret_key


def sign_pqc_block(
    manifest: dict[str, Any],
    algorithm: str | None = None,
) -> dict[str, Any]:
    algo, pub, sec = load_pqc_keypair(algorithm)
    message = canonical_bytes_pqc(manifest)
    signature = pqc_sign(algo, sec, message)
    return {
        "schema": PQC_SIGNATURE_SCHEMA,
        "algorithm": algo,
        "public_key": base64.b64encode(pub).decode("ascii"),
        "value": base64.b64encode(signature).decode("ascii"),
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def verify_pqc_block(manifest: dict[str, Any], block: dict[str, Any]) -> bool:
    if block.get("schema") != PQC_SIGNATURE_SCHEMA:
        return False
    algo = block.get("algorithm")
    if algo not in PQC_ALGORITHMS:
        return False
    public_key = block.get("public_key")
    value = block.get("value")
    if not isinstance(public_key, str) or not isinstance(value, str):
        return False
    if not pqc_available():
        return False
    try:
        pub_bytes = base64.b64decode(public_key.encode("ascii"), validate=True)
        sig_bytes = base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, TypeError):
        return False
    message = canonical_bytes_pqc(manifest)
    return pqc_verify(str(algo), pub_bytes, message, sig_bytes)


def verify_pqc_signatures(manifest: dict[str, Any]) -> bool:
    blocks = manifest.get("pqc_signatures")
    if blocks is None:
        return True
    if not isinstance(blocks, list) or not blocks:
        return False
    return all(isinstance(b, dict) and verify_pqc_block(manifest, b) for b in blocks)


def attach_pqc_overlay(
    signed_manifest: dict[str, Any],
    algorithm: str | None = None,
) -> dict[str, Any]:
    """Attach PQC signature(s) to an Ed25519-signed manifest."""
    block = signed_manifest.get("signature") or {}
    mode = block.get("mode")
    if mode == "hardware":
        raise IdentityError(
            "PQC overlay cannot be attached to hardware-signed envelopes. "
            "USB/NFC/SE050 devices sign Ed25519 only."
        )
    if not verify_pqc_signatures(signed_manifest):
        # manifest should not have invalid pqc before attach
        if signed_manifest.get("pqc_signatures"):
            raise IdentityError("manifest already contains invalid pqc_signatures")
    algo = normalize_pqc_algorithm(algorithm or configured_pqc_algorithm())
    out = dict(signed_manifest)
    existing = out.get("pqc_signatures")
    if isinstance(existing, list):
        filtered = [b for b in existing if isinstance(b, dict) and b.get("algorithm") != algo]
        out["pqc_signatures"] = [*filtered, sign_pqc_block(out, algo)]
    else:
        out["pqc_signatures"] = [sign_pqc_block(out, algo)]
    return out


def pqc_status() -> dict[str, Any]:
    info = pqc_backend_info()
    info["configured_algorithm"] = configured_pqc_algorithm()
    return info


__all__ = [
    "attach_pqc_overlay",
    "configured_pqc_algorithm",
    "load_pqc_keypair",
    "normalize_pqc_algorithm",
    "pqc_key_path",
    "pqc_status",
    "pqc_store_dir",
    "sign_pqc_block",
    "verify_pqc_block",
    "verify_pqc_signatures",
]
