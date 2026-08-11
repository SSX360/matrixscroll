# Scroll Gate hosted verification

Scroll Gate is the hosted verification path. It posts a commit range to the
SSX360 API and returns a pass or fail for the merge gate. Local verification
covers the same range with the same Ed25519 check: `verify_envelope`,
`matrixscroll envelope-verify-range --source local|notes|bundle`, and the MCP
`verify_pr_range` tool with `source=notes` all run offline, on your machine,
against git notes or on-disk envelopes.

## What each path needs

| Path | Requirement |
|------|-------------|
| `matrixscroll envelope-verify-range --source notes` | The repository and `matrixscroll`. |
| MCP `verify_pr_range` with `source=local`, `notes`, or `bundle` | The repository and `matrixscroll[mcp]`. |
| Hosted verify in CI, MCP `source=hosted`, `list_envelopes`, `audit_export` | `SSX360_API_KEY`. |

## GitHub Actions

Add the repository secret `SSX360_API_KEY` under Settings, Secrets, Actions.

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

## Moving from the local action to the hosted API

| Local action | Hosted API |
|------------|-------------|
| `matrixscroll/.github/actions/verify@action-v1` | `curl` or the `@v2` action against the SSX360 API |
| Reads git notes on the runner | Records each verification on the SSX360 API |
| No API key | `SSX360_API_KEY` required |

Both paths run the same signature check. The hosted path adds a server-side
record of the result.

## MCP

Set `SSX360_API_KEY` in your MCP server environment to use the hosted path. The
default `verify_pr_range` source is `hosted`. Pass `source=notes` for offline
git-notes verification.

## SLSA mapping, partial today

Scroll Gate checks commit-time provenance against
[SLSA](https://slsa.dev/) Build Level 1 and 2 concepts. SSX360 does not claim
SLSA Build Level 3 and holds no SLSA certification. This is evidence mapping,
not a certification claim.

| SLSA concept | Scroll Gate today | Gap |
|--------------|----------------------------|-----|
| **Version control** | Git plus signed commit envelopes on every governed commit | Scroll client MVP still rolling out |
| **Retained history** | Git immutable objects, plus server-side envelope storage on the hosted path | The offline path retains history in git notes only |
| **Authenticated source** | Ed25519 commit envelopes bind actor, tool, scope | Default **emulated** keys; SE050 hardware is a bench prototype |
| **Hosted build platform** | Partial: `ci_step` action envelopes plus the hosted verify API | Does not replace GitHub Actions or Cloud Build |
| **Non-falsifiable provenance** | Not claimed at L3 or above | Requires hardware-backed signing plus builder attestations |

### What hosted verify proves today

When Scroll Gate passes for a pull request range:

1. Each commit in range carries a cryptographically valid envelope, or policy
   allows the gap in warn mode.
2. Signatures verify against trusted keys and team policy when configured.
3. The hosted path records each verification server-side so an audit export can
   replay it. The offline path records nothing off your machine.

That covers SLSA Source L1 and L2 style controls, meaning a versioned and
authenticated change history, for **commit** provenance. Build artifact
provenance is a separate track this gate does not cover.

### Roadmap toward stronger SLSA alignment

| Phase | Deliverable | SLSA relevance |
|-------|-------------|----------------|
| Phase 1 (now) | `sign-action --type ci_step`, hosted verify | CI step attestation alongside commits |
| Phase 2 | Scroll `push` plus mandatory notes | Stronger retained provenance chain |
| Phase 3 | Builder attestations | Toward L3 build provenance, uncommitted |

## Related

- [Universal action envelopes and `scroll commit`](./SSX360_SCROLL.md)
- [SLSA Source Track mapping](../SLSA_SOURCE_TRACK_MAPPING.md)
