# Assessment progress - 15 September 2026

Tracks work against `matrixscroll-assessment-2026-09-15.md` (rated 5/10).
Evidence mapping only; not a certification claim.

| Package | Status in tree | Notes |
| --- | --- | --- |
| WP12 Claims hygiene | Done | README Shipping/Bar; COMPARISON repaired; SECURITY_PROPERTIES v0.10.0; SPEC hardware text softened |
| WP1 `matrixscroll.ledger` | Done | SPEC §12, schemas, CLI, tests, `LedgerChain.tla` |
| WP3 Crypto | Partial (primary path started) | Opt-in primary mode helper; Ed25519 still default; ML-DSA primary raises until overlay path; `MATRIXSCROLL_FIPS` fail-closed stub (`fips_mode.py`); CRYPTO_ROADMAP + `CAVP_CMVP_ROUTE.md` |
| WP4 Trusted time / Rekor | Partial | RFC 3161-shaped field + structure verify; live TSA/Rekor gated; policy knobs |
| WP5 Assurance | Partial (Rust start) | LedgerChain TLA+; Tamarin stub; Rust `matrixscroll-verify` + optional Kani proofs; audit RFP drafted (not engaged); no Lean/F\* yet |
| WP6 Supply chain | Partial | SBOM script, SSDF map, Scorecard workflow, SHA-pinned actions, pre-0.9 statement template |
| WP7 Controls | Done (docs+code) | NIST 800-53/171 JSON maps; key lifecycle; OCSF/OTel export |
| WP2 Encoding / I-D | Partial | JCS alias; SCITT mapping; I-D scaffold expanded (PQC profile + ledger epoch subject); not on datatracker |
| WP8 Agent capture | Partial | MCP intercept helper + delegation/policy schemas; not a full network proxy |
| WP9 Interop | Partial | JS verifier stub; Rust verifier CLI start; no WASM browser drop-zone on matrixscroll.com (site remains tombstone) |
| WP10 Benchmarks | Partial | `scripts/evidence_benchmark.py` + `docs/EVIDENCE_BENCHMARK.md` |
| WP11 Adoption | Partial (materials) | `AUDIT_RFP.md`, OpenSSF sandbox draft (not submitted), SCITT/DataTrails playbook, pilot evidence pack template, briefing corrected claim sheet; named pilots and live submissions still need owner action |

Projected score after this tree: roughly **6.5-7.0** on the assessment rubric (Days 0-30 band), pending re-score with METHOD.md. Remaining path to 10 is WP5 audit/proofs (Lean/F\*, engaged third-party audit), live SCITT/I-D on datatracker, automatic capture parity, multi-language verifier parity with vectors, and transition partners.

## Briefing

Corrected speaker-notes sheet:
[`docs/briefings/ERA_OF_STRUCTURAL_TRUST_CORRECTED.md`](briefings/ERA_OF_STRUCTURAL_TRUST_CORRECTED.md)
(tamper-evident; insider limits; simulator N; IPTO HR001126S0011 $1.41M requested not awarded; anonymized pilots; FIPS 204 software not FIPS 140-3; keep three-valued verdict and Independence Firewall). PDF rebuild still outstanding.
