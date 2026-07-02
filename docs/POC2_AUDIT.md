# POC 2 audit readiness checklist

**Target:** External security / design review · June 2026  
**Repos:** [SSX360/matrixscroll](https://github.com/SSX360/matrixscroll), [SSX360/digital-rain](https://github.com/SSX360/digital-rain)

## 1. Cryptography

- [x] Ed25519 sign–verify roundtrip (Hypothesis P1–P4, `tests/test_security_properties.py`)
- [x] PQC overlay additive; `canonical_bytes` excludes `pqc_signatures` (commit `b4d743e`)
- [x] `docs/CRYPTO_ROADMAP.md` — Q-Day 2028–2033 disclosure, ML-DSA/SLH-DSA path
- [x] Hardware signers Ed25519-only; software optional `[pqc]`
- [ ] Third-party crypto audit (scheduled post-POC 2)

## 2. Formal methods

- [x] TLA+ models: `formal/tla/*.tla` (Scroll Gate, CanonicalBytes, AuthorityFive, OrgPlanSync)
- [x] CI: `.github/workflows/formal-verify.yml` (TLC on push)
- [x] Property registry: `formal/PROPERTIES.md`, `matrixscroll/formal.py`

## 3. Scroll Gate & CI

- [x] `ssx360 check` CLI + hosted verify (`matrixscroll/ssx360_cli.py`)
- [x] `provenance-gate.yml` uses `ssx360 check --hosted` (not empty commits curl)
- [x] Community tier: 100 hosted verifications/day

## 4. SSX360 control plane

- [x] Browser verifier `/verify` — Ed25519 + PQC metadata
- [x] Org plan sync after Stripe webhook (`syncOrganizationFromEntitlement`)
- [x] Team checkout + API key scopes (`defaultScopesForPlan`)
- [x] Evidence export + compliance framework mappings

## 5. Documentation honesty

- [x] No “signs every line in IDE” — commit-envelope language
- [x] Trust page: `/trust` — local vs hosted boundary
- [x] TLA+ claimed only where models exist

## 6. Live deployments

| Surface | URL | Last verified |
| ------- | --- | ------------- |
| SSX360 | https://ssx360.com | Vercel production |
| Matrix Scroll | https://matrixscroll.com | Vercel production |
| PyPI | https://pypi.org/project/matrixscroll/0.5.1/ | v0.5.1 (ssx360 CLIs on PyPI) |

## 7. Reviewer artifacts

| Artifact | Path |
| -------- | ---- |
| Security properties | `docs/SECURITY_PROPERTIES.md` |
| Crypto roadmap | `docs/CRYPTO_ROADMAP.md` |
| Whitepaper | `docs/WHITEPAPER.md` |
| Sample envelope | `public/samples/valid_commit_envelope.json` (SSX360) |
| Conformance vectors | `vectors/` |

## 8. Known gaps (disclosed)

- `matrixscroll mandate` CLI documented in AP2 pipeline but not yet in SDK
- Browser verifier: Ed25519 full verify; PQC verify requires local `[pqc]` CLI
- npm `@ssx360/verify` package not published
