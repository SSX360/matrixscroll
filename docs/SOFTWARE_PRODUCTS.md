# Matrix Scroll — software products (D0–365, no hardware required)

Hardware (Matrix Key, SE050) is optional. These products ship on **L1 emulated Ed25519** today.

| Product | Status | Access | Notes |
|---------|--------|--------|-------|
| **Matrix Scroll SDK** | ✅ GA | PyPI `matrixscroll==0.2.5` | Hooks, envelopes, Scroll Gate, policy CLI |
| **Scroll Gate CI** | ✅ GA | [`matrixscroll-verify-action@v1`](https://github.com/SSX360/matrixscroll-verify-action) | PR range + manifest verify |
| **Browser verifier** | ✅ GA | [matrixscroll.com/verify](https://matrixscroll.com/verify/) | Offline paste-and-verify |
| **Protocol docs** | ✅ GA | [matrixscroll.com/docs](https://matrixscroll.com/docs/) | SPEC mirror, whitepaper, quickstarts |
| **Mission Control (local)** | ✅ Beta | `launch/runtime-console/` in SSX360 workspace | Agent registry, demo mode; not hosted SaaS yet |
| **Mission Control (hosted preview)** | 🛠 Deploy | Vercel demo (`DEPLOY_MODE=demo`) | Read-only UI; Paperclip sign stays local |
| **GUAC export CLI** | ✅ MVP | `matrixscroll envelope-export-guac` | v0.2.5 |
| **Rekor publish CLI** | ✅ Dry-run | `matrixscroll envelope-publish-rekor --dry-run` | v0.2.5 |
| **YubiKey bridge** | 🛠 Beta | `MATRIXSCROLL_MODE=yubikey` | PKCS#11 pubkey path; device validation ongoing |
| **TypeScript verifier** | 📋 Planned | npm package | Phase 3 |
| **Mission Control SaaS** | 📋 Planned | Stripe tiers (software-only) | Org registry + policy; no hardware gate |
| **Paperclip companion** | 📋 Planned | Desktop app | Personal agent approval surface |

## Developer install (today)

```bash
pip install "matrixscroll==0.2.5"
matrixscroll hook-install
export MATRIXSCROLL_ACTOR_TYPE=agent MATRIXSCROLL_TOOL=cursor
git commit -m "feat: agent change"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

## CI (Scroll Gate)

```yaml
- uses: SSX360/matrixscroll-verify-action@v1
  with:
    head-ref: ${{ github.event.pull_request.head.sha }}
    base-ref: ${{ github.event.pull_request.base.sha }}
    source: notes
    matrixscroll-version: "0.2.5"
    summary-output: provenance-summary.json
```

## Honest limits (software-only)

- **L1 emulated** signing is the default root of trust until hardware PoC sign-off.
- Mission Control **hosted** paywall can gate org features (registry, exports, team keys) without requiring Matrix Key.
- Matrix Key / SE050 unlock **L2 hardware** mode — roadmap, not required for adoption.

## Links

- Company: [ssx360.com](https://ssx360.com)
- SDK repo: [github.com/SSX360/matrixscroll](https://github.com/SSX360/matrixscroll)
- Whitepaper: [ssx360.com/docs/SSX-360-Hardware-Attested-Authorization-for-Autonomous-Agents.pdf](https://ssx360.com/docs/SSX-360-Hardware-Attested-Authorization-for-Autonomous-Agents.pdf)
