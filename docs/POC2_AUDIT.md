# Matrix Scroll release evidence

This checklist records the public evidence for Matrix Scroll 0.7.0. It is a
release-readiness record, not a third-party audit or certification.

## Release surfaces

| Surface | Current reference |
| --- | --- |
| Python package | `matrixscroll==0.7.0` |
| MCP server | `matrixscroll-mcp`, 14 tools |
| GitHub Action | `SSX360/matrixscroll/.github/actions/verify@action-v1` |
| Browser verifier | <https://matrixscroll.com/verify/> |
| MCP surface scanner | <https://matrixscroll.com/scan/> |
| Protocol source | [`SPEC.md`](../SPEC.md) and [`schemas/`](../schemas/) |

## Verification behavior

- Ed25519 signatures are checked over deterministic canonical JSON bytes.
- Invalid signatures, unsupported schemas, malformed records, and empty commit
  ranges fail closed by default.
- Range checks can read local envelopes, Git notes, or exported bundles without
  a hosted account.
- The wheel includes the public schemas used by the MCP resources and evidence
  exporter.

## Hardware path

- SSX360 produces the RP2350 and NXP SE050 USB signer.
- The SE050 creates and retains the non-exportable Ed25519 private key.
- USB CDC host support ships in `matrixscroll[hardware]==0.7.0`.
- Physical units are supplied by SSX360 through direct contact. PyPI distributes
  the host software only.

## Release chain

- GitHub Actions builds the wheel and source distribution from the release
  repository state.
- PyPI Trusted Publishing supplies provenance attestations for both artifacts.
- `python scripts/release-readiness.py` checks package, README, and registry
  version consistency before publication.
- `python -m twine check --strict dist/*` validates the built metadata.

## Limits

- A valid signature proves integrity and key possession, not authorization to
  use the key.
- The optional ML-DSA and SLH-DSA overlay uses liboqs and has no CMVP validation.
- Matrix Scroll does not replace IAM, sandboxing, build attestations, or review
  policy.
- Compliance references map available evidence to control questions; they do
  not claim certification.
