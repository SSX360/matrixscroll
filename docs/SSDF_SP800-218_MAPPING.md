# SSDF (NIST SP 800-218) practice mapping

This document maps Matrix Scroll SDK surfaces to NIST SP 800-218
(Secure Software Development Framework) practices. It is an **evidence
mapping, not a certification claim**. Naming an SSDF practice ID does not
assert that a deployment is SSDF-assessed or that SSX360 is SSDF certified.

| Practice | Title (short) | Matrix Scroll evidence surface | Notes |
| --- | --- | --- | --- |
| PO.1 | Define security requirements | `SPEC.md`, schemas under `schemas/` | Protocol requirements are machine-readable |
| PO.3 | Implement roles | `provenance.actor_type`, delegation schemas | human / agent / ci roles on envelopes |
| PO.5 | Implement and maintain secure environments | Offline verify, no network required for core path | Hosted Scroll Gate is separate |
| PS.1 | Protect all forms of code from unauthorized access and tampering | Commit envelopes, Scroll Gate range verify | Completeness vs commit range, not an append-only log claim |
| PS.2 | Provide a mechanism to verify software release integrity | `matrixscroll verify`, release manifests, PEP 740 provenance | Wheel digests in `docs/EVIDENCE.md` |
| PS.3 | Archive and protect each software release | Evidence packs, sealed packs, ledger epochs | Optional; operator chooses retention |
| PW.4 | Reuse existing, well-secured software | `cryptography`, optional `liboqs-python` | Dependency SBOM via `scripts/generate_sbom.py` |
| PW.6 | Configure tools for secure defaults | Ed25519 default; PQC overlay opt-in | `MATRIXSCROLL_PRIMARY_ALG` stays Ed25519 by default |
| PW.9 | Add executable code only after review | Action envelopes for CI / IaC / deploy | Policy decision schema records allow/deny |
| RV.1 | Identify and confirm vulnerabilities | CodeQL workflow, OpenSSF Scorecard workflow | Process evidence, not a vuln warranty |
| RV.3 | Analyse vulnerabilities | Independent verifier + vector suite | Second implementation under `tools/` |

## Shipping now / In progress / Not

| Item | Status |
| --- | --- |
| Offline Ed25519 verify + commit/action envelopes | Shipping now (0.9.0) |
| SSDF practice table in this file | Shipping now (0.9.x docs) |
| Third-party SSDF assessment of SSX360 or Matrix Scroll | Not |

## References

- NIST SP 800-218, Secure Software Development Framework (SSDF) Version 1.1
- [`docs/EVIDENCE.md`](EVIDENCE.md)
- [`controls/nist-800-53-r5.2.json`](../controls/nist-800-53-r5.2.json)
