# Scroll Gate v2 — hosted verification

Scroll Gate **v2** calls the SSX360 hosted API. Local-only verification remains in the Matrix Scroll SDK and MCP (`verify_envelope`, offline `source=local|notes|bundle`).

## Requirements

- **`SSX360_API_KEY`** — required for CI and hosted MCP Scroll Gate
- Community tier includes **100 CI verifications/day**
- Get a key at [ssx360.com/signup](https://ssx360.com/signup)

## GitHub Actions

Add repository secret `SSX360_API_KEY` (Settings → Secrets → Actions).

The workflow in `.github/workflows/provenance-gate.yml` posts to:

```text
POST https://ssx360.com/api/v1/verify
Authorization: Bearer $SSX360_API_KEY
```

Example body:

```json
{
  "base": "<base-sha>",
  "head": "<head-sha>",
  "commits": []
}
```

## Migration from v1

| v1 (local) | v2 (hosted) |
|------------|-------------|
| `matrixscroll-verify-action@v1` | `curl` or `@v2` action against ssx360.com |
| Local git notes only | Network audit + usage metering |
| No API key | `SSX360_API_KEY` required |

## MCP

Set `SSX360_API_KEY` in your MCP server environment. The default `verify_pr_range` source is `hosted`. Use `source=notes` for offline git-notes verification without a key.

## Docs

- Platform docs: [ssx360.com/docs](https://ssx360.com/docs)
- Migration guide: [PLATFORM_PIVOT.md](./PLATFORM_PIVOT.md)
