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

---

## SLSA mapping (honest — partial today)

Scroll Gate provides **governance-as-a-service** aligned with [SLSA](https://slsa.dev/) Build Level 1–2 concepts. SSX360 does **not** claim full SLSA Build Level 3 or certification.

| SLSA concept | SSX360 / Scroll Gate today | Gap |
|--------------|----------------------------|-----|
| **Version control** | Git + signed commit envelopes on every governed commit | Scroll client MVP still rolling out |
| **Retained history** | Git immutable objects + optional hosted envelope storage (Team+) | Community: local/git-notes only |
| **Authenticated source** | Ed25519 commit envelopes bind actor, tool, scope | Default **emulated** keys; SE050 hardware is pilot |
| **Hosted build platform** | ⚠️ Partial — `ci_step` action envelopes + hosted verify API | Not a replacement for GitHub Actions / Cloud Build |
| **Non-falsifiable provenance** | ❌ Not claimed at L3+ | Requires hardware-backed signing + builder attestations (Layer 4) |

### What hosted verify proves today

When Scroll Gate passes for a PR range:

1. Each commit in range has a **cryptographically valid** envelope (or policy allows warn-mode gaps).
2. Signatures verify against trusted keys / team policy when configured.
3. Verification is **logged** on ssx360.com for Team+ audit export (usage-metered on Community).

This maps to **SLSA Source L1–L2** style controls (versioned, authenticated change history) for **commit provenance**, not full **build artifact** provenance.

### Roadmap toward stronger SLSA alignment

| Phase | Deliverable | SLSA relevance |
|-------|-------------|----------------|
| Phase 1 (now) | `sign-action --type ci_step`, hosted verify | CI step attestation alongside commits |
| Phase 2 | Scroll `push` + mandatory notes | Stronger retained provenance chain |
| Phase 3 | Builder attestations (Layer 4 doc) | Toward L3 build provenance — not committed |

Portal reference: [ssx360.com/docs/slsa](https://ssx360.com/docs/slsa)

## Docs

- Platform docs: [ssx360.com/docs](https://ssx360.com/docs)
- Migration guide: [PLATFORM_PIVOT.md](./PLATFORM_PIVOT.md)
- Layer 3 roadmap: [LAYER3 governance (digital-rain)](https://github.com/SSX360/digital-rain/blob/main/docs/commercial/LAYER3_GOVERNANCE_ROADMAP.md)
