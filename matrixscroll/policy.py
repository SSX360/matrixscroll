"""Policy-aware manifest verification."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .manifest import verify_manifest


@dataclass
class VerifyPolicy:
    require_mode: str | None = None
    trusted_public_keys: set[str] | None = None
    allowed_schemas: set[str] | None = None
    require_actor_types: set[str] | None = None
    deny_actor_types: set[str] | None = None
    require_delegation_for_actor_types: set[str] | None = None
    verify_agent_scope: bool = False

    @classmethod
    def from_json_file(cls, path: str | Path) -> "VerifyPolicy":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        keys = data.get("trusted_public_keys")
        schemas = data.get("allowed_schemas")
        req_actors = data.get("require_actor_types")
        deny_actors = data.get("deny_actor_types")
        req_deleg = data.get("require_delegation_for_actor_types")
        return cls(
            require_mode=data.get("require_mode"),
            trusted_public_keys=set(keys) if keys else None,
            allowed_schemas=set(schemas) if schemas else None,
            require_actor_types=set(req_actors) if req_actors else None,
            deny_actor_types=set(deny_actors) if deny_actors else None,
            require_delegation_for_actor_types=set(req_deleg) if req_deleg else None,
            verify_agent_scope=bool(data.get("verify_agent_scope", False)),
        )

    def is_empty(self) -> bool:
        return (
            self.require_mode is None
            and self.trusted_public_keys is None
            and self.allowed_schemas is None
            and self.require_actor_types is None
            and self.deny_actor_types is None
            and self.require_delegation_for_actor_types is None
            and not self.verify_agent_scope
        )


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

    if policy.allowed_schemas is not None:
        schema = manifest.get("schema")
        if schema not in policy.allowed_schemas:
            return False, f"schema {schema!r} not allowed"

    return True, None
