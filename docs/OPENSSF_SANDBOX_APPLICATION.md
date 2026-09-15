# OpenSSF Sandbox application draft (Matrix Scroll)

**Status: draft, not submitted.** Do not treat this text as an official OpenSSF
application or as membership confirmation.

Compliance language here is evidence mapping, not a certification claim against
NIST, the SSDF, or OpenSSF scorecard thresholds as certification.

## Working title

Matrix Scroll: offline-verifiable signed machine-action and commit provenance

## Mission

Matrix Scroll records who acted (human, agent, or CI), with which tool, over
which subject (commit SHA, action digest, MCP tool surface, or ledger epoch),
as Ed25519-signed JSON envelopes that verify offline. Optional post-quantum
overlays and a hash-linked ledger extend the same fail-closed
CONSISTENT / INCONSISTENT / INDETERMINATE contract. The project exists so that
reviewers can reconstruct provenance without a Matrix Scroll account.

## Differentiation

| Project | Overlap | Matrix Scroll difference |
| --- | --- | --- |
| [gittuf](https://gittuf.dev/) | Git policy and reference-state integrity | Matrix Scroll signs actor/tool/scope envelopes and MCP surfaces; gittuf focuses on repository policy and RSL-style logs |
| [Sigstore](https://www.sigstore.dev/) / cosign / Rekor | Artifact signing and transparency | Matrix Scroll defaults to offline verify of envelopes; Sigstore centers keyless OIDC identities and public logs. Rekor-shaped fields are optional and informational until configured |
| Git commit signatures (GPG/SSH) | Commit authenticity | Matrix Scroll adds structured agent attribution and a CI range gate that fails closed on empty unsigned ranges |

Matrix Scroll complements these tools. It does not replace identity providers,
build provenance (SLSA attestations), or artifact signing.

## Maintainers

- Primary: Ryan York / SSX360 (public repository `SSX360/matrixscroll`)
- Security contact: security@matrixscroll.com
- Additional maintainers: to be listed at submission time with CLA / DCO status

## License

- Implementation: Apache-2.0
- Specification and conformance vectors: CC0 1.0 (as published in the repository)

## Security contacts and process

See [`SECURITY.md`](../SECURITY.md): private reporting via email or GitHub
Security Advisories; aim to acknowledge within 3 business days.

## Evidence already in tree (for reviewers)

- Conformance vectors and `tools/independent_verify.py` second implementation
- TLA+ models under `formal/tla/` with CI TLC where configured
- Optional Rust verifier start under `rust/matrixscroll-verify/`
- Scorecard and CodeQL workflows under `.github/workflows/`
- Published PyPI package `matrixscroll` (pin **0.10.0** in examples)

## What this draft does not claim

- OpenSSF Sandbox acceptance
- Passing any OpenSSF Best Practices badge level as a certification
- Third-party audit completion (see [`AUDIT_RFP.md`](AUDIT_RFP.md))
- FIPS CMVP, CAVP certificate, CNSA 2.0 certification, or NSA approval
