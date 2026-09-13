# Matrix Scroll release evidence

This checklist records the public evidence for Matrix Scroll **0.9.0**. It is a
release-readiness record, not a third-party audit or certification. Use it when
assembling NIST, DARPA, or similar packages that need a citable software
baseline.

## Release surfaces

| Surface | Current reference |
| --- | --- |
| Python package | `matrixscroll==0.9.0` (supported floor also: `0.7.0` on PyPI) |
| MCP server | `matrixscroll-mcp`, **13** tools |
| GitHub Action | `SSX360/matrixscroll/.github/actions/verify@action-v1` |
| Protocol source | [`SPEC.md`](../SPEC.md) and [`schemas/`](../schemas/) |
| Security policy | [`SECURITY.md`](../SECURITY.md) — supported versions **0.7.x–0.9.x** |
| Public git history | Begins at the supported 0.9.0 line; earlier history is not published |

## Verification behavior

- Ed25519 signatures are checked over deterministic canonical JSON bytes.
- Optional PQC overlay (ML-DSA / SLH-DSA) and sealed evidence packs (ML-KEM-1024
  hybrid) require `matrixscroll[pqc]`. Parameter-set readiness through liboqs;
  not a FIPS or CNSA certification claim.
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

## Release chain

- GitHub Actions builds the wheel and source distribution from the release
  repository state.
- PyPI Trusted Publishing supplies provenance attestations for both artifacts.
- `python scripts/release-readiness.py` checks package, README, and registry
  consistency when present in the tree.

## What this is not

- Not a third-party security audit report.
- Not evidence that any deployment is certified under CNSA 2.0, FIPS 140, or
  Common Criteria.
- Not a substitute for your organisation's own verification of digests and
  signatures against this release.
