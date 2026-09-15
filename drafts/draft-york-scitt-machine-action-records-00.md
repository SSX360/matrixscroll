# Individual Internet-Draft scaffold (not submitted)

```text
Internet-Draft
Network Working Group                                         R. York
Internet-Draft                                                 SSX360
Intended status: Informational                         15 September 2026
Expires: 19 March 2027

       SCITT Profile for Machine-Action Records (Matrix Scroll)
              draft-york-scitt-machine-action-records-00
```

## Abstract

This document describes how signed machine-action records, as implemented by
the Matrix Scroll open protocol, relate to SCITT statement and receipt
concepts (RFC 9943, RFC 9942). It defines record types for commit provenance,
non-git actions, optional timestamps, and hash-linked ledger epochs. The
profile is informational. It does not register media types or claim that any
deployment is a conformant SCITT Transparency Service.

**Status of this memo:** Individual draft scaffold. Not submitted to the IETF
datatracker. Do not cite as other than work in progress.

## Notational conventions

The key words "MUST", "MUST NOT", "SHOULD", and "MAY" in this document are to
be interpreted as described in RFC 2119 and RFC 8174 when, and only when, they
appear in all capitals.

JSON field names use the Matrix Scroll schemas published with the reference
implementation. CBOR COSE encodings are out of scope for this -00 scaffold.

## 1. Introduction

Software supply-chain and agentic tooling produce machine actions that need
offline-verifiable attribution. Matrix Scroll binds actor, tool, and scope to
a subject (for example a git commit SHA or an API call digest) under an
Ed25519 signature, with an optional post-quantum overlay.

## 2. Record types

| Record | Schema string | Subject |
| --- | --- | --- |
| Commit envelope | `matrixscroll.commit_envelope.v1` | Git commit id |
| Action envelope | `matrixscroll.action_envelope.v1` | Action-type payload |
| Ledger record | `matrixscroll.ledger_record.v1` | Prior record hash link |
| Ledger epoch | `matrixscroll.ledger_epoch.v1` | Tip hash + Merkle root |
| Delegation chain | `matrixscroll.delegation_chain.v1` | Mandate to action digest |
| Policy decision | `matrixscroll.policy_decision.v1` | Policy version that allowed/denied |

## 3. Mapping to SCITT

A Matrix Scroll envelope corresponds to a signed statement about a subject.
An optional receipt field or Rekor-shaped artifact may carry inclusion
evidence when an operator configures a transparency log. See
`docs/SCITT_MAPPING.md` in the reference repository.

## 4. Post-quantum profile pointer

Primary signatures remain Ed25519 in v1. Software signers MAY attach FIPS 204
ML-DSA / FIPS 205 SLH-DSA overlays (`pqc_signatures`). Parameter selection and
CNSA 2.0 Category 5 readiness notes live in `docs/CRYPTO_ROADMAP.md`. Naming
ML-DSA-87 is parameter-set readiness, not CNSA certification.

## 5. Security considerations

- Verifiers MUST fail closed on missing or invalid signatures (CONSISTENT /
  INCONSISTENT / INDETERMINATE).
- Timestamps without a verified TSA path are informational.
- Proxy interception of MCP `tools/call` proves observation by the proxy, not
  agent-authored intent.
- This draft makes no certification claim against NIST, SSDF, or SCITT
  conformance test suites. Evidence mapping only.

## 6. IANA considerations

None in this -00 scaffold.

## 7. Post-quantum (PQC) profile

Primary signatures in Matrix Scroll v1 remain Ed25519. Software signers MAY
attach FIPS 204 ML-DSA overlays (`pqc_signatures`) as described in the
reference implementation roadmap. This profile intends alignment with the
direction of RFC 9964 (PQC algorithm identifiers and related COSE/JOSE
guidance) for naming ML-DSA parameter sets when a future CBOR COSE encoding is
defined. Naming ML-DSA-87 is Category 5 / CNSA 2.0 signature parameter-set
readiness only. It is not CNSA certification, FIPS CMVP validation, or NSA
approval. Evidence mapping only; not a certification claim against NIST or the
SSDF.

Verifiers that require a PQC overlay MUST fail closed (INCONSISTENT) when the
overlay is missing or invalid under policy, and MUST return INDETERMINATE when
the PQC backend cannot run.

## 8. Ledger epoch as SCITT statement subject

A `matrixscroll.ledger_epoch.v1` checkpoint MAY be registered as a SCITT
statement subject. The subject material SHOULD bind at least:

- `tip_hash` (hash of the last included ledger record)
- `root_hash` (Merkle root over the epoch range)
- `epoch_id`, `start_index`, `end_index`, and `record_count`

Operators MUST verify the hash-linked chain (`verify_chain` / equivalent) before
submission. The epoch statement attests to the checkpoint contents the signer
bound; it does not by itself prove that every underlying business event was
complete or honest before signing (tamper-evident, not tamper-proof).

## Status of This Memo

Individual Submission scaffold - not yet posted to the IETF datatracker. Do not
cite as other than work in progress. This file is a repository draft only.

## Authors' addresses

Ryan York  
SSX360  
Email: security@matrixscroll.com
