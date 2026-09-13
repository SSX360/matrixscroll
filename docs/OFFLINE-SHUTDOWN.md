# matrixscroll.com site shutdown record

**Date:** 2026-08-23  
**Status:** Tombstone deployed (static landing page; marketing retired)

See also the site repository copy at
[`SSX360/Matrix_Scroll/OFFLINE-SHUTDOWN.md`](https://github.com/SSX360/Matrix_Scroll/blob/main/OFFLINE-SHUTDOWN.md).

## Rationale

Matrix Scroll is used in sensitive deployments. The public marketing site, browser
verifier, and docs mirror added attack surface without strengthening offline
verification. The PyPI package and this repository remain canonical.

## What changed

| Surface | Before | After |
|---------|--------|-------|
| Homepage | Full marketing site | Static tombstone |
| `/docs/*`, `/verify/*`, `/scan/*` | Interactive pages | Redirects to GitHub or tombstone |
| `/schemas/*` | JSON schemas | **Unchanged** |
| PyPI `matrixscroll` | Published | **Still published** |

## Offline verification boundary

Core verify paths (`verify_manifest`, `verify_envelope`, `verify_envelope_range`)
do **not** fetch `matrixscroll.com`. Schemas load from the installed package via
`matrixscroll._schemas`. Hosted SSX360 API calls require `SSX360_API_KEY` and
reach `ssx360.com` only.

Regression test: `tests/test_offline_verify_network.py`.

## Credential rotation

Completed per [`docs/OPERATOR_RUNBOOK.md`](./OPERATOR_RUNBOOK.md). Rotate, do not
chase deleted copies across mirrors.

## Operational data retention

`data/envelopes/` and `workbench.sqlite3` are audit evidence. **Retained** unless
a separate policy says otherwise.

## PyPI and signing

- Trusted Publishing (OIDC) via `.github/workflows/publish.yml`; maintainers must use 2FA
- Defensive typosquat package names documented in `OPERATOR_RUNBOOK.md`
- Production signing keys must not live on developer laptops; see `SECURITY.md`
