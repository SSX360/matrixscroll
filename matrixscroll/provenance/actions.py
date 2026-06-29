"""Signed action envelope builders for universal provenance."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Literal

from ..manifest import sign_manifest

ACTION_SCHEMA = "matrixscroll.action_envelope.v1"

ActionType = Literal[
    "git_commit",
    "ci_step",
    "iac_change",
    "db_migration",
    "api_call",
    "contract_deploy",
]

ACTION_TYPES: tuple[ActionType, ...] = (
    "git_commit",
    "ci_step",
    "iac_change",
    "db_migration",
    "api_call",
    "contract_deploy",
)

_REQUIRED_FIELDS: dict[ActionType, tuple[str, ...]] = {
    "git_commit": ("commit_sha",),
    "ci_step": ("pipeline", "step", "run_id"),
    "iac_change": ("tool", "resource_type", "resource_id"),
    "db_migration": ("migration_id", "database", "direction"),
    "api_call": ("method", "endpoint", "status_code"),
    "contract_deploy": ("chain", "contract_address", "tx_hash"),
}


@dataclass
class ProvenanceActor:
    actor_type: Literal["human", "agent", "ci"] = "human"
    tool: str = "matrixscroll"
    tool_version: str | None = None
    agent_scope: str | None = None


@dataclass
class ActionEnvelopeInput:
    action_type: ActionType
    payload: dict[str, Any]
    actor: ProvenanceActor = field(default_factory=ProvenanceActor)
    repository: dict[str, Any] | None = None
    parent_actions: list[str] | None = None


def validate_action_payload(action_type: str, payload: dict[str, Any]) -> tuple[bool, str | None]:
    if action_type not in ACTION_TYPES:
        return False, f"unknown action_type: {action_type!r}"
    if not isinstance(payload, dict):
        return False, "payload must be a JSON object"
    required = _REQUIRED_FIELDS.get(action_type, ())  # type: ignore[arg-type]
    missing = [key for key in required if not payload.get(key)]
    if missing:
        return False, f"missing required payload fields: {', '.join(missing)}"
    return True, None


def build_action_envelope(
    action_type: ActionType,
    payload: dict[str, Any],
    *,
    actor_type: Literal["human", "agent", "ci"] = "human",
    tool: str = "matrixscroll",
    tool_version: str | None = None,
    agent_scope: str | None = None,
    repository: dict[str, Any] | None = None,
    parent_actions: list[str] | None = None,
) -> dict[str, Any]:
    ok, err = validate_action_payload(action_type, payload)
    if not ok:
        raise ValueError(err or "invalid action payload")

    provenance: dict[str, Any] = {
        "actor_type": actor_type,
        "tool": tool,
    }
    if tool_version:
        provenance["tool_version"] = tool_version
    if agent_scope:
        provenance["agent_scope"] = agent_scope

    envelope: dict[str, Any] = {
        "schema": ACTION_SCHEMA,
        "action_type": action_type,
        "payload": copy.deepcopy(payload),
        "provenance": provenance,
    }
    if repository:
        envelope["repository"] = copy.deepcopy(repository)
    if parent_actions:
        envelope["parent_actions"] = list(parent_actions)
    return envelope


def sign_action_envelope(envelope: dict[str, Any], provider=None) -> dict[str, Any]:
    if envelope.get("schema") != ACTION_SCHEMA:
        raise ValueError(f"expected schema {ACTION_SCHEMA!r}")
    return sign_manifest(envelope, provider=provider)
