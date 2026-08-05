# Matrix Scroll MCP quickstart

Install the provenance MCP server so agents can sign and verify commit envelopes in-loop.

## Install

```bash
pip install "matrixscroll[mcp]==0.6.2"
```

The console script `matrixscroll-mcp` is the preferred entry point. `python -m matrixscroll.mcp` also works.

## Register in your editor

Add this to `.cursor/mcp.json` (project) or your global MCP config:

```json
{
  "mcpServers": {
    "matrixscroll-mcp": {
      "type": "stdio",
      "command": "matrixscroll-mcp",
      "args": [],
      "env": {
        "SSX360_API_KEY": "sk_live_..."
      }
    }
  }
}
```

On Windows, if `matrixscroll-mcp` is not on PATH, use the full path to the script inside your virtual environment.

Signing and verification run locally and need no account. `SSX360_API_KEY` is
only for the tools that call the hosted SSX360 API.

## Verify the connection

1. Enable the server in your editor's MCP settings.
2. Invoke the `status` tool. It reads local hook state and needs no network.
3. Invoke `verify_pr_range` with `source=notes` to check a range offline.

## Which tools reach the network

| Tool | Network |
|------|---------|
| `create_envelope`, `verify_envelope`, `status`, `sign_action` | None. Local key store and Git only. |
| `verify_pr_range` with `source=local`, `notes`, or `bundle` | None. |
| `verify_pr_range` with `source=hosted`, `list_envelopes`, `audit_export` | Calls ssx360.com. Needs `SSX360_API_KEY`. |

## CLI and hooks (repos without MCP)

For Git hook and CI workflows without MCP, use:

```bash
pip install "matrixscroll==0.6.2"
matrixscroll hook-install
```

Hosted Scroll Gate CI calls `https://ssx360.com/api/v1/verify`. See
[SCROLL_GATE_V2.md](./commercial/SCROLL_GATE_V2.md).

See [FIVE_MINUTES.md](./FIVE_MINUTES.md) for the hook path.
