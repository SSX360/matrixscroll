"""MCP tool-surface fingerprinting, manifest signing, and drift detection.

Implements ``ssx360.mcp-manifest.v1`` — Ed25519-signed snapshots of an MCP
server's tool surface (name, description, input schema hash) for offline
verify and rug-pull detection.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .manifest import sign_manifest, verify_manifest

MCP_MANIFEST_SCHEMA = "ssx360.mcp-manifest.v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def schema_hash(schema: Any) -> str:
    """Return sha256 digest of canonical input schema JSON."""
    body = _canonical_json(schema if schema is not None else None)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def fingerprint_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Fingerprint one MCP tool definition."""
    name = str(tool.get("name") or "")
    description = str(tool.get("description") or "")
    input_schema = tool.get("inputSchema")
    if input_schema is None:
        input_schema = tool.get("input_schema")
    return {
        "name": name,
        "description": description,
        "input_schema_hash": schema_hash(input_schema),
    }


def surface_hash(fingerprints: list[dict[str, Any]]) -> str:
    """Aggregate hash over sorted tool fingerprints."""
    body = _canonical_json(fingerprints)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_mcp_manifest(
    tools: list[dict[str, Any]],
    *,
    server_name: str = "",
    server_version: str = "",
    server_url: str = "",
    package: str = "",
) -> dict[str, Any]:
    """Build an unsigned ``ssx360.mcp-manifest.v1`` document."""
    fingerprints = sorted(
        (fingerprint_tool(t) for t in tools),
        key=lambda item: item["name"],
    )
    server: dict[str, str] = {}
    if server_name:
        server["name"] = server_name
    if server_version:
        server["version"] = server_version
    if server_url:
        server["url"] = server_url
    if package:
        server["package"] = package
    manifest: dict[str, Any] = {
        "schema": MCP_MANIFEST_SCHEMA,
        "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tools": fingerprints,
        "surface_hash": surface_hash(fingerprints),
    }
    if server:
        manifest["server"] = server
    return manifest


def scan_mcp_server(
    tools: list[dict[str, Any]],
    *,
    server_name: str = "",
    server_version: str = "",
    server_url: str = "",
    package: str = "",
) -> dict[str, Any]:
    """Fingerprint an MCP server's tool surface and return a trust scan report."""
    manifest = build_mcp_manifest(
        tools,
        server_name=server_name,
        server_version=server_version,
        server_url=server_url,
        package=package,
    )
    return {
        "ok": True,
        "tool_count": len(manifest["tools"]),
        "surface_hash": manifest["surface_hash"],
        "manifest": manifest,
    }


def sign_mcp_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Ed25519-sign an MCP manifest (adds ``signature`` block)."""
    if manifest.get("schema") != MCP_MANIFEST_SCHEMA:
        raise ValueError(f"expected schema {MCP_MANIFEST_SCHEMA!r}")
    unsigned = {k: v for k, v in manifest.items() if k != "signature"}
    return sign_manifest(unsigned)


def verify_mcp_manifest(
    manifest: dict[str, Any],
    *,
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify signature and optionally diff against a baseline manifest."""
    if manifest.get("schema") != MCP_MANIFEST_SCHEMA:
        return {"ok": False, "error": "invalid_schema", "expected": MCP_MANIFEST_SCHEMA}
    crypto_ok = verify_manifest(manifest)
    if not crypto_ok:
        return {"ok": False, "error": "signature_invalid"}
    block = manifest.get("signature") or {}
    result: dict[str, Any] = {
        "ok": True,
        "surface_hash": manifest.get("surface_hash"),
        "tool_count": len(manifest.get("tools") or []),
        "device_id": block.get("device_id"),
        "signed_at": block.get("signed_at"),
    }
    if baseline is not None:
        drift = diff_mcp_manifests(baseline, manifest)
        result["drift"] = drift
        if drift.get("changed"):
            result["ok"] = False
            result["error"] = "surface_drift"
    return result


def diff_mcp_manifests(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare two manifests and report rug-pull style drift."""
    base_tools = {t["name"]: t for t in (baseline.get("tools") or []) if t.get("name")}
    cur_tools = {t["name"]: t for t in (current.get("tools") or []) if t.get("name")}
    added = sorted(set(cur_tools) - set(base_tools))
    removed = sorted(set(base_tools) - set(cur_tools))
    mutated: list[dict[str, Any]] = []
    for name in sorted(set(base_tools) & set(cur_tools)):
        base = base_tools[name]
        cur = cur_tools[name]
        fields: list[str] = []
        if base.get("description") != cur.get("description"):
            fields.append("description")
        if base.get("input_schema_hash") != cur.get("input_schema_hash"):
            fields.append("input_schema_hash")
        if fields:
            mutated.append({"name": name, "fields": fields})
    surface_changed = baseline.get("surface_hash") != current.get("surface_hash")
    return {
        "changed": bool(added or removed or mutated or surface_changed),
        "surface_hash_baseline": baseline.get("surface_hash"),
        "surface_hash_current": current.get("surface_hash"),
        "added": added,
        "removed": removed,
        "mutated": mutated,
    }


async def _fetch_tools_live(
    transport: str,
    *,
    command: list[str] | None = None,
    url: str = "",
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Connect to a live MCP server and list its tools (requires ``matrixscroll[mcp]``)."""
    try:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
    except ImportError as exc:
        raise RuntimeError(
            "live MCP connect requires optional dependency: pip install 'matrixscroll[mcp]'"
        ) from exc

    server_info: dict[str, str] = {}
    if transport == "stdio":
        if not command:
            raise ValueError("--server-command required when --connect stdio")
        params = StdioServerParameters(command=command[0], args=command[1:])
        client_ctx = stdio_client(params)
    elif transport == "sse":
        from mcp.client.sse import sse_client

        if not url:
            raise ValueError("--url required when --connect sse")
        client_ctx = sse_client(url)
    else:
        raise ValueError(f"unsupported transport {transport!r}; use stdio or sse")

    async with client_ctx as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await session.initialize()
            info = init_result.serverInfo
            if info is not None:
                if info.name:
                    server_info["name"] = info.name
                if info.version:
                    server_info["version"] = info.version
            tools_result = await session.list_tools()
            tools: list[dict[str, Any]] = []
            for tool in tools_result.tools:
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "inputSchema": tool.inputSchema,
                    }
                )
            return tools, server_info


def fetch_mcp_tools_live(
    transport: str,
    *,
    command: list[str] | None = None,
    url: str = "",
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Synchronous wrapper for live MCP tool listing."""
    import anyio

    return anyio.run(
        lambda: _fetch_tools_live(transport, command=command, url=url)
    )


def load_tools_json(path: str) -> list[dict[str, Any]]:
    """Load MCP tool definitions from a JSON file (array or {tools: [...]})."""
    from pathlib import Path

    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("tools"), list):
        return raw["tools"]
    raise ValueError("tools file must be a JSON array or object with a tools array")
