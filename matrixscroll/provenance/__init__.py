"""Universal provenance action envelopes for Matrix Scroll.

Extends commit-time Git envelopes with signed action types for CI, IaC,
database migrations, API calls, and smart-contract deploys. All action
types share the same Ed25519 signature block as commit envelopes.
"""

from .actions import (
    ACTION_SCHEMA,
    ACTION_TYPES,
    ActionType,
    build_action_envelope,
    sign_action_envelope,
    validate_action_payload,
)

__all__ = [
    "ACTION_SCHEMA",
    "ACTION_TYPES",
    "ActionType",
    "build_action_envelope",
    "sign_action_envelope",
    "validate_action_payload",
]
