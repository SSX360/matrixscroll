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

    @classmethod
    def from_json_file(cls, path: str | Path) -> "VerifyPolicy":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        keys = data.get("trusted_public_keys")
        schemas = data.get("allowed_schemas")
        return cls(
            require_mode=data.get("require_mode"),
            trusted_public_keys=set(keys) if keys else None,
            allowed_schemas=set(schemas) if schemas else None,
        )


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
