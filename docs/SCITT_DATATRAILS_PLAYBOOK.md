# SCITT / DataTrails playbook

Steps to register one Matrix Scroll statement on a SCITT-oriented transparency
service (DataTrails / scitt-cose style) once credentials exist. This is an
operator playbook, not a claim that Matrix Scroll is a conformant SCITT
Transparency Service.

Evidence mapping only; not a certification claim against RFC 9942 / RFC 9943
conformance suites.

## Prerequisites

- A signed Matrix Scroll envelope (commit or action) from `matrixscroll==0.10.0`
  that verifies offline (`matrixscroll verify` or
  `python tools/independent_verify.py`).
- DataTrails (or equivalent) tenant credentials and a configured SCITT /
  scitt-cose submission endpoint. **Do not commit secrets.** Store them in the
  operator secret manager.
- Read [`SCITT_MAPPING.md`](SCITT_MAPPING.md) and the I-D scaffold
  [`drafts/draft-york-scitt-machine-action-records-00.md`](../drafts/draft-york-scitt-machine-action-records-00.md)
  (individual submission scaffold; not on the datatracker yet).

## Local dry-run checklist (no network)

1. Sign a sample envelope and confirm CONSISTENT offline.
2. Compute the subject identifier you will register (commit SHA or action
   digest) and record it in your run notes.
3. Export a statement-shaped JSON (envelope without private key material) and
   confirm canonical bytes still match the signature.
4. Confirm optional `receipt` / Rekor-shaped fields are absent or marked
   informational so a missing log does not look like a pass.
5. Run `matrixscroll verify` again after any field you plan to send to the
   service; fail closed on INCONSISTENT / INDETERMINATE.

## Live registration (when credentials exist)

1. Authenticate to the DataTrails / SCITT API with the operator credential.
2. Submit one statement whose subject is the Matrix Scroll subject id and whose
   payload references the envelope digest (SHA-256 of canonical signing bytes
   or of the sealed pack, as your profile requires).
3. Store the returned receipt or inclusion proof beside the envelope under a
   digest-pinned path.
4. Re-verify offline: envelope signature first, then receipt structure. Missing
   receipt verification libraries yield INDETERMINATE, not a silent pass.
5. Document the service URL, statement id, and time in the pilot evidence pack
   ([`PILOT_EVIDENCE_PACK_TEMPLATE.md`](PILOT_EVIDENCE_PACK_TEMPLATE.md)).

## Ledger epochs as subjects

When registering a ledger epoch, use the epoch tip hash and Merkle root from
`matrixscroll.ledger_epoch.v1` as the statement subject material, per the I-D
scaffold section on ledger epochs. Verify the chain with `verify_chain` /
`verify_bundle` before submission.

## Related

- IETF SCITT working group drafts and RFCs 9942 / 9943
- Vendor docs for DataTrails scitt-cose submission (follow the vendor's current
  API; do not hard-code expired URLs in automation without a pin review)
