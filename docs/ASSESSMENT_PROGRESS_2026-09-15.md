# Assessment progress - 15 September 2026

Tracks work against `matrixscroll-assessment-2026-09-15.md` (rated 5/10 at
commit `ebcb60d`). Post-release tree: **matrixscroll 0.10.0** on PyPI.
Evidence mapping only; not a certification claim.

| Package | Status in tree | Notes |
| --- | --- | --- |
| WP12 Claims hygiene | Done | README Shipping/Bar; COMPARISON repaired; SECURITY_PROPERTIES v0.10.0 |
| WP1 `matrixscroll.ledger` | Done | SPEC §12, schemas, CLI, tests, `LedgerChain.tla` |
| WP3 Crypto | Done (opt-in) | Primary ML-DSA-87 via `MATRIXSCROLL_PRIMARY_ALG`; composite mode; Ed25519 default; `MATRIXSCROLL_FIPS` stub; CAVP/CMVP route doc |
| WP4 Trusted time / Rekor | Partial | RFC 3161-shaped field + structure verify; live TSA/Rekor gated |
| WP5 Assurance | Partial | LedgerChain TLA+; Tamarin stub; Rust verifier + Kani stubs; audit RFP drafted (not engaged); Lean/F\* still the bar |
| WP6 Supply chain | Partial | SBOM script, SSDF map, Scorecard workflow, SHA-pinned actions, pre-0.9 statement; Scorecard score not yet published |
| WP7 Controls | Done | NIST 800-53/171 JSON maps; key lifecycle; OCSF/OTel export |
| WP2 Encoding / I-D | Partial | JCS alias; SCITT mapping; I-D scaffold; not on datatracker |
| WP8 Agent capture | Partial | MCP intercept helper + delegation/policy schemas |
| WP9 Interop | Partial | JS stub + Rust CLI; no WASM on matrixscroll.com |
| WP10 Benchmarks | Partial | `scripts/evidence_benchmark.py` + `docs/EVIDENCE_BENCHMARK.md` |
| WP11 Adoption | Partial | RFP, OpenSSF draft, SCITT playbook, pilot template, briefing claim sheet; live submissions need owner action |

**Release:** https://pypi.org/project/matrixscroll/0.10.0/ ·
https://github.com/SSX360/matrixscroll/releases/tag/v0.10.0

Projected score after 0.10.0: roughly **6.5-7.0** on the assessment rubric,
pending a METHOD.md re-score. Remaining path to 10 is engaged audit, live
SCITT/I-D, automatic capture parity, multi-language vector parity, and
transition partners.

## Briefing

Corrected speaker-notes sheet:
[`docs/briefings/ERA_OF_STRUCTURAL_TRUST_CORRECTED.md`](briefings/ERA_OF_STRUCTURAL_TRUST_CORRECTED.md).
PDF rebuild still outstanding (source deck is image-only).
