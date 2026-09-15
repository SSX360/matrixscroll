# Matrix Scroll software products

Hardware is optional. These products ship Ed25519 over canonical manifest bytes
today, with optional ML-DSA/SLH-DSA overlays and a hash-linked ledger.

| Product | Status | Access | Notes |
|---------|--------|--------|-------|
| **Matrix Scroll SDK** | GA | PyPI `matrixscroll==0.10.0` | Hooks, envelopes, Scroll Gate, ledger, policy CLI |
| **Hash-linked ledger** | GA | `matrixscroll ledger` / `matrixscroll.ledger` | SPEC §12 domain tags + epoch checkpoints |
| **Scroll Gate CI** | GA | [`matrixscroll/.github/actions/verify@action-v1`](https://github.com/SSX360/matrixscroll/tree/main/.github/actions/verify) | PR range + manifest verify |
| **Browser verifier** | Retired (2026-08) | CLI / MCP offline | Site UI removed; use `matrixscroll verify` |
| **Protocol docs** | GA | [GitHub docs](https://github.com/SSX360/matrixscroll/tree/main/docs) | Tombstone at matrixscroll.com |
| **GUAC export CLI** | MVP | `matrixscroll envelope-export-guac` | Same manifest contract |
| **Rekor publish CLI** | Dry-run / gated live | `matrixscroll envelope-publish-rekor` | Live only with `MATRIXSCROLL_REKOR_PUBLISH=1` |
| **MCP intercept** | Preview | `matrixscroll.mcp_intercept` | Proxy-side tools/call signing helper |
| **JS verifier stub** | Preview | `js/matrixscroll-verify` | Structural / vector checks; Ed25519 parity in progress |
| **SSX360 USB signer** | Direct contact | [Contact SSX360](https://ssx360.com/contact) | RP2350 USB bridge and NXP SE050 secure element |
| **External key backends** | In progress | provider research | Only graduates when the backend preserves Ed25519 over canonical bytes |
| **TypeScript verifier** | In progress | npm package stub | `js/matrixscroll-verify` |

## Developer install

```bash
pip install "matrixscroll==0.10.0"
matrixscroll hook-install
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-runner
git commit -m "feat: agent change"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

## CI

```yaml
- uses: SSX360/matrixscroll/.github/actions/verify@action-v1
  with:
    head-ref: ${{ github.event.pull_request.head.sha }}
    base-ref: ${{ github.event.pull_request.base.sha }}
    source: notes
    matrixscroll-version: "0.10.0"
    summary-output: provenance-summary.json
```

## Honest limits

- The file-backed provider remains the default until a deployment selects an
  `IdentityProvider` and registers the expected signer key.
- The SSX360 signer changes key custody. Matrix Scroll adoption does not require it.
- Existing security keys are complementary today and become first-class Matrix
  Scroll backends only when they preserve the same Ed25519 contract.
- Marketing pages on matrixscroll.com stay retired; schemas and PyPI are the
  public trust surface.

## Links

- Product site: [matrixscroll.com](https://matrixscroll.com)
- SDK repo: [github.com/SSX360/matrixscroll](https://github.com/SSX360/matrixscroll)
- Whitepaper: [docs/WHITEPAPER.md](WHITEPAPER.md)
- Assessment progress: [docs/ASSESSMENT_PROGRESS_2026-09-15.md](ASSESSMENT_PROGRESS_2026-09-15.md)
