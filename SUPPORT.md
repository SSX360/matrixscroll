# Support

Matrix Scroll is an open protocol with a reference SDK. This page explains how to get help and what to expect.

## Quick links

| Need | Go to |
|------|--------|
| Install hooks and verify commits | [`docs/quickstart-git.md`](docs/quickstart-git.md) |
| Protocol wire format | [`SPEC.md`](SPEC.md) |
| Threat model and design | [`docs/WHITEPAPER.md`](docs/WHITEPAPER.md) |
| Compare to Sigstore, agentmark, etc. | [`docs/COMPARISON.md`](docs/COMPARISON.md) |
| Browser verify (no install) | [matrixscroll.com/verify](https://matrixscroll.com/verify/) |
| CI verification | [matrixscroll-verify-action](https://github.com/SSX360/matrixscroll-verify-action) |
| Security vulnerability | **security@matrixscroll.com** (see [`SECURITY.md`](SECURITY.md)) |

## GitHub

- **Bugs and feature requests:** [open an issue](https://github.com/SSX360/matrixscroll/issues/new/choose)
- **Questions and ideas:** [GitHub Discussions](https://github.com/SSX360/matrixscroll/discussions)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)

Please include your OS, Python version, `matrixscroll --version`, and the output of `matrixscroll hook-status` when reporting hook or verify problems.

## Response expectations

This is a small open-source project maintained by SSX360. We aim to:

- Acknowledge security reports within **48 hours**
- Triage bugs within **1 week**
- Respond to Discussions when we can; no SLA for community Q&A

Commercial support for teams (policy design, hardware rollout, CI integration) is not offered through this repo today. Contact **hello@matrixscroll.com** for partnership inquiries.

## What we cannot help with in issues

- IDE or agent configuration (Cursor, Copilot, Claude Code) beyond hook env vars
- Git hosting or org policy outside the Matrix Scroll envelope format
- Legal or regulatory compliance interpretation — see [`docs/AGENTIC_AI_SECURITY.md`](docs/AGENTIC_AI_SECURITY.md) as a starting map only

## Status

- **Shipping now:** L1 emulated Ed25519 key, Git post-commit hooks, PyPI `matrixscroll` **0.2.5**, Scroll Gate, delegation schema, GUAC/Rekor CLI MVP
- **In progress:** SSX360 / NXP SE050 hardware provider, YubiKey PKCS#11 bridge
- **Not in scope:** IAM, sandbox, prompt-injection filter, or agent runtime
