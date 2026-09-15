"""MCP proxy hook: intercept ``tools/call`` and sign a digest of params+result.

When this module sits in front of an MCP server as a proxy, it records machine
actions without requiring agent cooperation. The agent issues a normal
``tools/call``; the proxy computes a digest over params and result, then builds
a ``sign_action``-shaped envelope (``api_call`` action type by default).

This is interception, not agent-attested intent. The envelope proves that the
proxy observed the call; it does not prove the agent authored a mandate.
"""

from __future__ import annotations

import copy
import json
from typing import Any, Callable, Awaitable

from .canonical import canonical_bytes
from .crypto_backend import sha256_hex
from .provenance.actions import build_action_envelope, sign_action_envelope

ToolHandler = Callable[..., Any] | Callable[..., Awaitable[Any]]


def digest_tool_exchange(params: dict[str, Any], result: Any) -> str:
    """SHA-256 hex over canonical JSON of params and a JSON-safe result view."""
    payload = {
        "params": params,
        "result": _json_safe(result),
    }
    return sha256_hex(canonical_bytes(payload))


def build_intercept_action_envelope(
    *,
    tool_name: str,
    params: dict[str, Any],
    result: Any,
    actor_type: str = "agent",
    tool: str = "mcp-proxy",
    sign: bool = False,
    provider: Any = None,
) -> dict[str, Any]:
    """Build (and optionally sign) an action envelope for an intercepted call."""
    digest = digest_tool_exchange(params, result)
    envelope = build_action_envelope(
        "api_call",
        {
            "method": "tools/call",
            "endpoint": tool_name,
            "status_code": "200",
            "digest": digest,
            "params_digest": sha256_hex(canonical_bytes({"params": params})),
        },
        actor_type=actor_type,  # type: ignore[arg-type]
        tool=tool,
        agent_scope=f"mcp:tools/call:{tool_name}",
    )
    envelope["intercept"] = {
        "mode": "proxy",
        "cooperation": False,
        "note": "Recorded by MCP proxy without agent cooperation",
    }
    if sign:
        return sign_action_envelope(envelope, provider=provider)
    return envelope


def wrap_tools_call(
    handler: ToolHandler,
    *,
    tool_name: str,
    sign: bool = False,
    on_envelope: Callable[[dict[str, Any]], None] | None = None,
    actor_type: str = "agent",
    tool: str = "mcp-proxy",
    provider: Any = None,
) -> Callable[..., Any]:
    """Return a wrapper that invokes *handler* then builds an intercept envelope.

    Synchronous handlers only. Async callers should await the original handler
    and call ``build_intercept_action_envelope`` themselves.
    """

    def wrapped(**params: Any) -> Any:
        result = handler(**params)
        envelope = build_intercept_action_envelope(
            tool_name=tool_name,
            params=dict(params),
            result=result,
            actor_type=actor_type,
            tool=tool,
            sign=sign,
            provider=provider,
        )
        if on_envelope is not None:
            on_envelope(envelope)
        return result

    return wrapped


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, allow_nan=False)
        return copy.deepcopy(value)
    except (TypeError, ValueError):
        return {"repr": repr(value)}
