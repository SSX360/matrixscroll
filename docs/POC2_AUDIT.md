# Matrix Scroll release evidence

This checklist records the public evidence for Matrix Scroll **0.10.0**. It is a
release-readiness record, not a third-party audit or certification. Use it when
assembling NIST, DARPA, or similar packages that need a citable software
baseline.

## Release surfaces

| Surface | Current reference |
| --- | --- |
| Python package | `matrixscroll==0.10.0` (supported floor: `0.7.0` on PyPI) |
| MCP server | `matrixscroll-mcp`, **13** tools |
| GitHub Action | `SSX360/matrixscroll/.github/actions/verify@action-v1` (default pin `0.10.0`) |
| Protocol source | [`SPEC.md`](../SPEC.md) and [`schemas/`](../schemas/) |
| Security policy | [`SECURITY.md`](../SECURITY.md) — supported versions **0.7.x–0.10.x** |
| Release evidence log | [`docs/EVIDENCE.md`](EVIDENCE.md) — digests, PEP 740 provenance, PQC boundary |
| Public git history | Begins at the supported 0.9.0 line; 0.10.0 continues that line |

## Verification behavior

- Ed25519 signatures are checked over deterministic canonical JSON bytes.
- Optional primary ML-DSA-87 (`MATRIXSCROLL_PRIMARY_ALG=ml-dsa-87`), PQC overlay
  (ML-DSA / SLH-DSA), and sealed evidence packs (ML-KEM-1024 hybrid) require
  `matrixscroll[pqc]`. Parameter-set readiness through liboqs; not a FIPS or
  CNSA certification claim.
- Hash-linked ledger records and epoch checkpoints verify under SPEC §12 with
  three-valued verdicts (CONSISTENT / INCONSISTENT / INDETERMINATE).
- Invalid signatures, unsupported schemas, malformed records, and empty commit
  ranges fail closed by default.
- Range checks can read local envelopes, Git notes, or exported bundles without
  a hosted account.
- The wheel includes the public schemas used by the MCP resources and evidence
  exporter.

## Custody

- Default provider is file-backed emulated Ed25519 keys under `~/.matrixscroll/`.
- Production deployments should use a non-exportable key behind an
  `IdentityProvider` (HSM, secure element, or cloud KMS). The public SDK does
  not ship a USB host transport.
- Historical envelopes with `signature.mode` equal to `"hardware"` still verify;
  new hardware signing is not offered through PyPI extras.

## How to re-run

See [`docs/EVIDENCE.md`](EVIDENCE.md) for digests, provenance curl, and offline
commands. Assessment progress vs the 15 Sep funder scorecard is in
[`docs/ASSESSMENT_PROGRESS_2026-09-15.md`](ASSESSMENT_PROGRESS_2026-09-15.md).
