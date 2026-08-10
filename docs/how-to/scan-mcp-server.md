# Scan an MCP server for drift

An MCP server can change its tool descriptions after you install it. A tool that
searched the web on Monday can exfiltrate every query on Friday, with no version
bump and no signal in your client. This guide establishes a signed baseline and
fails your build when the surface changes.

!!! note "Stub"
    The offline path and the CI gate are covered. Signing policy for multi-server
    fleets is not yet written.

## 1. Capture and sign a baseline

```bash
matrixscroll mcp scan --connect stdio --server-command "npx -y some-mcp-server" \
  -o manifest.json --pretty
matrixscroll mcp sign manifest.json -o baseline.signed.json
```

Commit `baseline.signed.json`. It is the artifact everything else compares
against.

## 2. Re-scan and diff

```bash
matrixscroll mcp scan --connect stdio --server-command "npx -y some-mcp-server" -o current.json
matrixscroll mcp sign current.json -o current.signed.json
matrixscroll mcp verify current.signed.json --baseline baseline.signed.json --pretty
```

A mutated description or input schema fails loudly and exits `2`.

## 3. Scan without running the server

If you cannot execute the server, paste any `tools/list` response:

```bash
matrixscroll mcp scan --tools ./tools.json
```

The file may be a plain JSON array or an object with a `tools` key.

## 4. Gate it in CI

```yaml
jobs:
  mcp-gate:
    uses: SSX360/matrixscroll/.github/workflows/mcp-manifest-gate.yml@action-v1
    with:
      manifest: mcp/my-server.signed.json
      baseline: mcp/my-server.baseline.json
      matrixscroll_version: "0.6.3"
```

## Related

- [Exit codes](../reference/exit-codes.md)
