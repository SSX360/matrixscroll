#!/usr/bin/env python3
"""Minimal stdio MCP handshake smoke test (Glama introspection path)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading


def _default_cmd() -> list[str]:
    if shutil.which("matrixscroll-mcp"):
        return ["matrixscroll-mcp"]
    return [sys.executable, "-m", "matrixscroll.mcp"]


def _drain_stderr(proc: subprocess.Popen[str]) -> None:
    if proc.stderr is None:
        return
    for line in proc.stderr:
        sys.stderr.write(f"[stderr] {line}")


def main() -> int:
    cmd = sys.argv[1:] or _default_cmd()
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin and proc.stdout
    threading.Thread(target=_drain_stderr, args=(proc,), daemon=True).start()

    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "glama-smoke", "version": "1.0"},
        },
    }
    proc.stdin.write(json.dumps(init) + "\n")
    proc.stdin.flush()

    line = proc.stdout.readline()
    if not line:
        proc.terminate()
        print("FAIL: no initialize response", file=sys.stderr)
        return 1
    resp = json.loads(line)
    if "error" in resp:
        print(f"FAIL: initialize error: {resp['error']}", file=sys.stderr)
        return 1

    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()

    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    proc.stdin.write(json.dumps(tools_req) + "\n")
    proc.stdin.flush()

    line = proc.stdout.readline()
    proc.terminate()
    if not line:
        print("FAIL: no tools/list response", file=sys.stderr)
        return 1
    tools_resp = json.loads(line)
    if "error" in tools_resp:
        print(f"FAIL: tools/list error: {tools_resp['error']}", file=sys.stderr)
        return 1

    tools = tools_resp.get("result", {}).get("tools") or []
    print(f"ok: {len(tools)} tools via stdio MCP")
    if len(tools) < 10:
        print("FAIL: expected at least 10 tools", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
