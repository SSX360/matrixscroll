# Matrix Scroll MCP quickstart

Install the provenance MCP server so agents can sign and verify commit envelopes in-loop.

## Install

```bash
pip install "matrixscroll[mcp]==0.5.1"
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

Get a free Community API key (100 hosted verifications/day) at [ssx360.com/signup](https://ssx360.com/signup).

## Verify the connection

1. Enable the server in your editor's MCP settings.
2. Invoke the `status` tool (free, local).
3. Invoke `list_envelopes` to confirm network access with your API key.

## Tool tiers

| Tool | Tier |
|------|------|
| `create_envelope`, `verify_envelope`, `status` | Free (local) |
| `verify_pr_range` (hosted), `list_envelopes`, `audit_export` | Requires `SSX360_API_KEY` |

Use `verify_pr_range` with `source=notes` for offline git-notes verification without a key.

## CLI and hooks (repos without MCP)

For Git hook and CI workflows without MCP, use:

```bash
pip install "matrixscroll==0.5.1"
matrixscroll hook-install
```

Scroll Gate v2 CI calls `https://ssx360.com/api/v1/verify` — see [SCROLL_GATE_V2.md](./commercial/SCROLL_GATE_V2.md).

See [FIVE_MINUTES.md](./FIVE_MINUTES.md) for the hook path.
