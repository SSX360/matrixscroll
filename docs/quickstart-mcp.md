# Matrix Scroll MCP quickstart

Install the provenance-only MCP server so agents can sign and verify commit envelopes in-loop.

## Install

```bash
pip install "matrixscroll[mcp]==0.3.0"
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
      "args": []
    }
  }
}
```

On Windows, if `matrixscroll-mcp` is not on PATH, use the full path to the script inside your virtual environment.

## Verify the connection

1. Enable the server in your editor's MCP settings.
2. Invoke the `status` tool.
3. Expect emulated signing mode until hardware backends are configured.

## Provenance verbs only

The MCP server exposes commit-time provenance tools: create envelope, verify envelope, verify PR range, publish notes, status, and audit export. It does not scan repos or install packages silently.

## CLI and hooks (repos without MCP)

For Git hook and CI workflows without MCP, use:

```bash
pip install "matrixscroll==0.3.0"
matrixscroll hook-install
```

See [FIVE_MINUTES.md](./FIVE_MINUTES.md) for the hook path.
