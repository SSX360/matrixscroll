"""RFC 3161-shaped timestamp tokens (informational until cryptographically verified).

Offline structure checks run without a TSA. Live FreeTSA (or other RFC 3161)
fetch is optional and belongs behind a publish path (``--publish`` / Rekor),
not the default offline verifier.
"""

from __future__ import annotations

import copy
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .verdict import Verdict

TIMESTAMP_SCHEMA = "matrixscroll.timestamp_token.v1"
DEFAULT_POLICY_OID = "1.2.3.4.1.9"  # placeholder policy OID for structure tests


@dataclass
class TimestampToken:
    """RFC 3161-shaped fields carried as JSON for Matrix Scroll envelopes."""

    version: int
    policy_oid: str
    message_imprint: str
    serial: str
    gen_time: str
    tsa_name: str
    status: str
    schema: str = TIMESTAMP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimestampToken":
        return cls(
            version=int(data["version"]),
            policy_oid=str(data["policy_oid"]),
            message_imprint=str(data["message_imprint"]),
            serial=str(data["serial"]),
            gen_time=str(data["gen_time"]),
            tsa_name=str(data["tsa_name"]),
            status=str(data["status"]),
            schema=str(data.get("schema", TIMESTAMP_SCHEMA)),
        )


def build_timestamp_request(message_digest_hex: str) -> dict[str, Any]:
    """Build a TimeStampReq-shaped dict for a SHA-256 message imprint."""
    digest = message_digest_hex.strip().lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("message_digest_hex must be a 64-char lowercase hex SHA-256")
    return {
        "schema": "matrixscroll.timestamp_request.v1",
        "version": 1,
        "messageImprint": {
            "hashAlgorithm": "sha256",
            "hashedMessage": digest,
        },
        "certReq": True,
        "nonce": f"{int(time.time() * 1000):x}",
    }


def attach_timestamp(envelope: dict[str, Any], token_dict: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *envelope* with a top-level ``timestamp`` field.

    The field is informational until ``verify_timestamp_with_root`` (or a live
    TSA path) confirms the token cryptographically.
    """
    out = copy.deepcopy(envelope)
    out["timestamp"] = copy.deepcopy(token_dict)
    return out


def _parse_gen_time(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def verify_timestamp_structure(token: TimestampToken | dict[str, Any]) -> Verdict:
    """Structural check only (no TSA certificate path)."""
    try:
        tok = token if isinstance(token, TimestampToken) else TimestampToken.from_dict(token)
    except (KeyError, TypeError, ValueError):
        return Verdict.INCONSISTENT

    if tok.version < 1:
        return Verdict.INCONSISTENT
    if not tok.policy_oid or not tok.serial or not tok.tsa_name:
        return Verdict.INCONSISTENT
    imprint = tok.message_imprint.strip().lower()
    if len(imprint) != 64 or any(c not in "0123456789abcdef" for c in imprint):
        return Verdict.INCONSISTENT
    if _parse_gen_time(tok.gen_time) is None:
        return Verdict.INCONSISTENT
    if tok.status.lower() not in {"granted", "granted_with_mods", "ok"}:
        return Verdict.INDETERMINATE
    return Verdict.CONSISTENT


def verify_timestamp_with_root(
    token: TimestampToken | dict[str, Any],
    tsa_root_pem: str | None,
) -> Verdict:
    """Offline verify stub against an optional TSA root PEM.

    When *tsa_root_pem* is provided, returns ``INDETERMINATE`` because the
    crypto path (CMS/PKCS#7 over the TSTInfo) is not implemented in this
    module yet. When *tsa_root_pem* is ``None`` (dev / structure-only),
    returns the structural verdict if ``gen_time`` parses.
    """
    structure = verify_timestamp_structure(token)
    if structure is not Verdict.CONSISTENT:
        return structure
    if tsa_root_pem:
        return Verdict.INDETERMINATE
    return Verdict.CONSISTENT


def make_dev_token(
    message_digest_hex: str,
    *,
    tsa_name: str = "dev-tsa.local",
    serial: str | None = None,
) -> dict[str, Any]:
    """Build a structure-valid token for tests (not a real TSA response)."""
    digest = message_digest_hex.strip().lower()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    token = TimestampToken(
        version=1,
        policy_oid=DEFAULT_POLICY_OID,
        message_imprint=digest,
        serial=serial or f"dev-{int(time.time())}",
        gen_time=now,
        tsa_name=tsa_name,
        status="granted",
    )
    return token.to_dict()
