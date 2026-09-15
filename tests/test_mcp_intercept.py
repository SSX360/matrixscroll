"""Tests for MCP tools/call interception without agent cooperation."""

from __future__ import annotations

from matrixscroll.mcp_intercept import (
    build_intercept_action_envelope,
    digest_tool_exchange,
    wrap_tools_call,
)


def test_digest_tool_exchange_stable():
    params = {"path": "/tmp/x", "mode": "r"}
    result = {"ok": True, "bytes": 12}
    a = digest_tool_exchange(params, result)
    b = digest_tool_exchange(params, result)
    assert a == b
    assert len(a) == 64


def test_build_intercept_action_envelope_unsigned():
    env = build_intercept_action_envelope(
        tool_name="read_file",
        params={"path": "README.md"},
        result={"content": "hello"},
        sign=False,
    )
    assert env["schema"] == "matrixscroll.action_envelope.v1"
    assert env["action_type"] == "api_call"
    assert env["payload"]["endpoint"] == "read_file"
    assert env["payload"]["method"] == "tools/call"
    assert env["intercept"]["cooperation"] is False
    assert "digest" in env["payload"]
    assert "signature" not in env


def test_wrap_tools_call_fake_handler():
    seen: list[dict] = []

    def fake_tool(*, query: str) -> dict:
        return {"hits": [query]}

    wrapped = wrap_tools_call(
        fake_tool,
        tool_name="search",
        sign=False,
        on_envelope=seen.append,
    )
    out = wrapped(query="matrixscroll")
    assert out == {"hits": ["matrixscroll"]}
    assert len(seen) == 1
    assert seen[0]["payload"]["endpoint"] == "search"
    assert seen[0]["intercept"]["mode"] == "proxy"
