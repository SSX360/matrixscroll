# SCITT mapping (RFC 9942 / RFC 9943 concepts)

This document maps Matrix Scroll record types to SCITT (Supply Chain Integrity,
Transparency, and Trust) statement and receipt concepts. It is an **evidence
mapping, not a certification claim**. Matrix Scroll does not claim to be a
conformant SCITT Transparency Service implementation.

References: RFC 9943 (SCITT Architecture), RFC 9942 (COSE Receipts), and the
IETF SCITT working group drafts as of September 2026.

| Matrix Scroll surface | SCITT concept (approx.) | Notes |
| --- | --- | --- |
| Commit envelope (`matrixscroll.commit_envelope.v1`) | Signed statement about a subject (commit SHA) | Subject is the git object id; payload is provenance |
| Action envelope (`matrixscroll.action_envelope.v1`) | Signed statement about a machine action | Broader than git; CI / IaC / API / deploy |
| Ed25519 `signature` block | COSE Sign1 analogue (JSON, not CBOR COSE today) | Wire format differs; verification semantics align at a high level |
| Optional `receipt` / Rekor dry-run entry | Receipt / inclusion evidence | Informational until a transparency service is configured |
| Ledger epoch checkpoint | Batch / checkpoint over a statement set | Hash-linked tip + Merkle root; not a SCITT TS API |
| `attach_timestamp` token | Time claim adjacent to a statement | RFC 3161-shaped; optional |
| Delegation chain schema | Authorization context for a statement | Human mandate to agent action |

## Shipping now / In progress / Not

| Item | Status |
| --- | --- |
| Commit and action envelopes with offline Ed25519 verify | Shipping now |
| Conceptual mapping in this document | Shipping now (0.9.x docs) |
| CBOR COSE Sign1 / RFC 9942 receipt bytes on the wire | Not |
| Hosted SCITT Transparency Service | Not |

## Draft pointer

See [`drafts/draft-york-scitt-machine-action-records-00.md`](../drafts/draft-york-scitt-machine-action-records-00.md)
for an individual Internet-Draft scaffold (not submitted).
