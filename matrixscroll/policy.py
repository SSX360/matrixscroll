"""Policy-aware manifest verification."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .manifest import verify_manifest


@dataclass
class TrustedKeyRecord:
    """One trusted public key with optional validity window and revocation."""

    public_key: str
    not_before: str | None = None
    not_after: str | None = None
    revoked_at: str | None = None
    device_id: str | None = None
    note: str | None = None

    def is_active_at(self, when: str | None) -> tuple[bool, str | None]:
        if self.revoked_at:
            if when is None or _parse_rfc3339(when) is None:
                return False, "trusted key is revoked"
            when_dt = _parse_rfc3339(when)
            revoked_dt = _parse_rfc3339(self.revoked_at)
            if when_dt is not None and revoked_dt is not None and when_dt >= revoked_dt:
                return False, "trusted key is revoked"
            if when_dt is None:
                return False, "trusted key is revoked"
        if when is None:
            # No signed_at: only reject hard revocations (handled above).
            if self.not_before or self.not_after:
                return False, "signed_at required to evaluate key validity window"
            return True, None
        when_dt = _parse_rfc3339(when)
        if when_dt is None:
            return False, "signed_at is not a valid RFC 3339 timestamp"
        if self.not_before:
            nb = _parse_rfc3339(self.not_before)
            if nb is not None and when_dt < nb:
                return False, "public key not yet valid at signed_at"
        if self.not_after:
            na = _parse_rfc3339(self.not_after)
            if na is not None and when_dt > na:
                return False, "public key expired at signed_at"
        return True, None


@dataclass
class VerifyPolicy:
    require_mode: str | None = None
    trusted_public_keys: set[str] | None = None
    trusted_key_records: list[TrustedKeyRecord] | None = None
    allowed_schemas: set[str] | None = None
    require_actor_types: set[str] | None = None
    deny_actor_types: set[str] | None = None
    require_delegation_for_actor_types: set[str] | None = None
    verify_agent_scope: bool = False
    require_pqc: str | bool = False
    require_timestamp: bool = False
    require_receipt: bool = False

    @classmethod
    def from_json_file(cls, path: str | Path) -> "VerifyPolicy":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        keys_raw = data.get("trusted_public_keys")
        key_set: set[str] | None = None
        records: list[TrustedKeyRecord] | None = None
        if keys_raw:
            key_set, records = _parse_trusted_keys(keys_raw)
        schemas = data.get("allowed_schemas")
        req_actors = data.get("require_actor_types")
        deny_actors = data.get("deny_actor_types")
        req_deleg = data.get("require_delegation_for_actor_types")
        require_pqc = data.get("require_pqc", False)
        return cls(
            require_mode=data.get("require_mode") or None,
            trusted_public_keys=key_set,
            trusted_key_records=records,
            allowed_schemas=set(schemas) if schemas else None,
            require_actor_types=set(req_actors) if req_actors else None,
            deny_actor_types=set(deny_actors) if deny_actors else None,
            require_delegation_for_actor_types=set(req_deleg) if req_deleg else None,
            verify_agent_scope=bool(data.get("verify_agent_scope", False)),
            require_pqc=require_pqc,
            require_timestamp=bool(data.get("require_timestamp", False)),
            require_receipt=bool(data.get("require_receipt", False)),
        )

    def is_empty(self) -> bool:
        return (
            self.require_mode is None
            and self.trusted_public_keys is None
            and self.trusted_key_records is None
            and self.allowed_schemas is None
            and self.require_actor_types is None
            and self.deny_actor_types is None
            and self.require_delegation_for_actor_types is None
            and not self.verify_agent_scope
            and not self.require_pqc
            and not self.require_timestamp
            and not self.require_receipt
        )


def _parse_rfc3339(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_trusted_keys(
    keys_raw: Any,
) -> tuple[set[str], list[TrustedKeyRecord] | None]:
    key_set: set[str] = set()
    records: list[TrustedKeyRecord] = []
    rich = False
    if not isinstance(keys_raw, list):
        return set(), None
    for item in keys_raw:
        if isinstance(item, str):
            if item:
                key_set.add(item)
            continue
        if isinstance(item, dict):
            pub = item.get("public_key") or item.get("key")
            if not isinstance(pub, str) or not pub:
                continue
            rich = True
            key_set.add(pub)
            records.append(
                TrustedKeyRecord(
                    public_key=pub,
                    not_before=item.get("not_before"),
                    not_after=item.get("not_after"),
                    revoked_at=item.get("revoked_at"),
                    device_id=item.get("device_id"),
                    note=item.get("note"),
                )
            )
    return key_set, (records if rich else None)


def _normalize_require_pqc(value: str | bool) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    normalized = str(value).strip().lower()
    if normalized in {"false", "0", "off", "no", ""}:
        return "false"
    if normalized in {"true", "1", "on", "yes"}:
        return "true"
    if normalized == "emulated_only":
        return "emulated_only"
    return "false"


def _pqc_required_for_envelope(envelope: dict[str, Any], policy: VerifyPolicy) -> bool:
    mode = _normalize_require_pqc(policy.require_pqc)
    if mode == "false":
        return False
    block = envelope.get("signature") or {}
    signer_mode = block.get("mode")
    if signer_mode == "hardware":
        return False
    if mode == "true":
        return True
    if mode == "emulated_only":
        return signer_mode in {"emulated", "tpm", None}
    return False


def verify_pqc_policy(
    envelope: dict[str, Any],
    policy: VerifyPolicy | None = None,
) -> tuple[bool, str | None]:
    policy = policy or VerifyPolicy()
    if not _pqc_required_for_envelope(envelope, policy):
        return True, None
    from .manifest import verify_manifest_pqc

    blocks = envelope.get("pqc_signatures")
    if not isinstance(blocks, list) or not blocks:
        return False, "policy requires pqc_signatures overlay"
    if not verify_manifest_pqc(envelope):
        return False, "PQC overlay verification failed"
    return True, None


def verify_trusted_key_window(
    envelope: dict[str, Any],
    policy: VerifyPolicy | None = None,
) -> tuple[bool, str | None]:
    """Reject when the signing key is revoked or outside its validity window."""
    policy = policy or VerifyPolicy()
    block = envelope.get("signature") or {}
    pub = block.get("public_key")
    signed_at = block.get("signed_at")
    if not isinstance(pub, str):
        return True, None

    if policy.trusted_key_records:
        matches = [r for r in policy.trusted_key_records if r.public_key == pub]
        if not matches and policy.trusted_public_keys is not None:
            return False, "public key not in trusted set"
        for record in matches:
            ok, reason = record.is_active_at(signed_at if isinstance(signed_at, str) else None)
            if not ok:
                return False, reason
        return True, None

    return True, None


def verify_envelope_attribution_policy(
    envelope: dict[str, Any],
    policy: VerifyPolicy | None = None,
) -> tuple[bool, str | None]:
    """Check actor-type and delegation rules on a commit envelope."""
    policy = policy or VerifyPolicy()
    provenance = envelope.get("provenance") or {}
    actor = provenance.get("actor_type")

    if policy.require_actor_types is not None:
        if actor not in policy.require_actor_types:
            return False, f"required actor_type one of {sorted(policy.require_actor_types)!r}, got {actor!r}"

    if policy.deny_actor_types is not None and actor in policy.deny_actor_types:
        return False, f"actor_type {actor!r} is denied by policy"

    if policy.require_delegation_for_actor_types is not None:
        if actor in policy.require_delegation_for_actor_types:
            delegation = envelope.get("delegation")
            if not isinstance(delegation, dict) or not delegation.get("owner_id"):
                return False, f"actor_type {actor!r} requires delegation attestation"

    return True, None


def verify_manifest_with_policy(
    manifest: dict[str, Any],
    policy: VerifyPolicy | None = None,
) -> tuple[bool, str | None]:
    """Verify manifest cryptographically and against optional policy rules."""
    if not verify_manifest(manifest):
        return False, "cryptographic verification failed"

    policy = policy or VerifyPolicy()
    block = manifest.get("signature") or {}

    if policy.require_mode and block.get("mode") != policy.require_mode:
        return False, f"required mode {policy.require_mode}, got {block.get('mode')}"

    if policy.trusted_public_keys is not None:
        pub = block.get("public_key")
        if pub not in policy.trusted_public_keys:
            return False, "public key not in trusted set"

    ok, reason = verify_trusted_key_window(manifest, policy)
    if not ok:
        return False, reason

    if policy.allowed_schemas is not None:
        schema = manifest.get("schema")
        if schema not in policy.allowed_schemas:
            return False, f"schema {schema!r} not allowed"

    if policy.require_timestamp:
        ts = manifest.get("timestamp")
        if not isinstance(ts, dict):
            return False, "policy requires timestamp"
        from .timestamp import verify_timestamp_structure

        if verify_timestamp_structure(ts).name != "CONSISTENT":
            return False, "timestamp structure invalid"

    if policy.require_receipt:
        receipt = manifest.get("receipt")
        if not isinstance(receipt, dict) or not receipt:
            return False, "policy requires receipt"

    ok, reason = verify_pqc_policy(manifest, policy)
    if not ok:
        return False, reason

    return True, None
