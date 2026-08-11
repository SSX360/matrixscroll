# Matrix Scroll software products

Hardware is optional. These products ship on pure Ed25519 over canonical
manifest bytes today.

| Product | Status | Access | Notes |
|---------|--------|--------|-------|
| **Matrix Scroll SDK** | GA | PyPI `matrixscroll==0.6.4` | Hooks, envelopes, Scroll Gate, policy CLI |
| **Scroll Gate CI** | GA | [`matrixscroll/.github/actions/verify@action-v1`](https://github.com/SSX360/matrixscroll/tree/main/.github/actions/verify) | PR range + manifest verify |
| **Browser verifier** | GA | [matrixscroll.com/verify](https://matrixscroll.com/verify/) | Offline paste-and-verify |
| **Protocol docs** | GA | [matrixscroll.com/docs](https://matrixscroll.com/docs/) | SPEC mirror, whitepaper, quickstarts |
| **GUAC export CLI** | MVP | `matrixscroll envelope-export-guac` | Same manifest contract |
| **Rekor publish CLI** | Dry-run | `matrixscroll envelope-publish-rekor --dry-run` | Evidence export, not new signing mode |
| **SSX360 USB signer** | Direct contact | [Contact SSX360](https://ssx360.com/contact) | RP2350 USB bridge and NXP SE050 secure element |
| **External key backends** | In progress | provider research | Only graduates when the backend preserves Ed25519 over canonical bytes |
| **TypeScript verifier** | Planned | npm package | Phase 3 |

## Developer install

```bash
pip install "matrixscroll==0.6.4"
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
    matrixscroll-version: "0.6.4"
    summary-output: provenance-summary.json
```

## Honest limits

- The file-backed provider remains the default until a deployment selects
  `MATRIXSCROLL_MODE=hardware` and registers the expected signer key.
- The SSX360 signer changes key custody. Matrix Scroll adoption does not require it.
- Existing security keys are complementary today and become first-class Matrix
  Scroll backends only when they preserve the same Ed25519 contract.

## Links

- Product site: [matrixscroll.com](https://matrixscroll.com)
- SDK repo: [github.com/SSX360/matrixscroll](https://github.com/SSX360/matrixscroll)
- Whitepaper: [docs/WHITEPAPER.md](WHITEPAPER.md)
