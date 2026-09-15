# Third-party audit engagement brief (RFP)

**Status:** Engagement brief only. This document does not claim that an audit
has been commissioned, started, or completed.

**Audience:** Security vendors evaluating a fixed-scope review of Matrix Scroll
open protocol artifacts (release `0.10.0` and matching tree).

Compliance language on this page is evidence mapping, not a certification claim
against NIST, the SSDF, or any other framework.

## Objective

Produce an independent security assessment of the Matrix Scroll protocol and
its shipping verifiers so that maintainers and pilot operators can cite a
public report when answering assurance questions. The engagement is scoped to
what is in the public repository and published specification, not to hosted
SSX360 commercial services unless separately contracted.

## In scope

| Area | Artifacts |
| --- | --- |
| Protocol | [`SPEC.md`](../SPEC.md), schemas under `schemas/`, conformance `vectors/` |
| Python SDK | `matrixscroll` package (signing, verify, ledger, gate, policy helpers) |
| Independent verifier | [`tools/independent_verify.py`](../tools/independent_verify.py) |
| Rust verifier start | [`rust/matrixscroll-verify/`](../rust/matrixscroll-verify/) |
| Ledger | SPEC §12, `matrixscroll.ledger`, TLA+ `formal/tla/LedgerChain.tla` |
| Crypto boundaries | Ed25519 primary path; optional PQC overlay documentation and fail-closed policy |

## Out of scope (unless added by change order)

- Hosted SSX360 API, billing, or multi-tenant cloud control planes
- Full CMVP lab engagement or CAVP certificate acquisition
- Formal proof of a Lean 4 / F\* extracted verifier (that remains the gold-standard bar)
- Naming or reviewing confidential pilot customer environments

## Preferred vendor classes

Invite bids from firms with published supply-chain, cryptography, and protocol
review experience. Suitable shortlist for outreach (not an endorsement or an
engagement announcement):

- Trail of Bits
- Cure53
- NCC Group

Other vendors may respond if they publish comparable methodology and prior
public reports in adjacent domains.

## Deliverables

1. Written statement of work and rules of engagement (kickoff).
2. Private findings report with severity, reproduction notes, and remediations.
3. Public summary report suitable for linking from `SECURITY.md` and the
   project README (required). The public report may redact exploit detail that
   remains unfixed; it must not assert certifications the project does not hold.
4. Optional: retest letter after maintainers land agreed fixes.

## Funding note

Maintainers may seek NLnet, OpenSSF Alpha-Omega, or similar public-interest
funding to cover or co-fund the engagement. Funding status is separate from
this brief. Do not treat a funding application as an audit in progress.

## Contact

Security reports and vendor questions: **security@matrixscroll.com** (see
[`SECURITY.md`](../SECURITY.md)).
