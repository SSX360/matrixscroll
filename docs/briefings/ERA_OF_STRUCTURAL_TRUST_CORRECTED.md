# Era of Structural Trust - corrected claim sheet

**Role:** Speaker-notes replacement for the 13-slide corporate briefing until
the PDF is rebuilt. Aligns with assessment §6 claim hygiene.

**Rule:** Prefer under-claim. Every NIST / SSDF mention is evidence mapping, not
a certification claim.

## Keep

| Claim | Correct wording |
| --- | --- |
| Three-valued verdict | Every verify path returns CONSISTENT, INCONSISTENT, or INDETERMINATE (exit `0` / `2` / `1`). No silent pass on missing evidence. |
| Independence Firewall | Offline reconstruction from raw records without a Matrix Scroll account; second implementation `tools/independent_verify.py`; hosted services are optional and never required for a CONSISTENT verdict. |
| Tamper-evident ledger | Hash-linked records detect post-sign mutation, reorder, fork, and omit-with-gap. |
| Ed25519 + optional ML-DSA | Primary Ed25519; optional FIPS 204 ML-DSA overlay is software parameter readiness through liboqs, not FIPS 140-3 module validation. |
| Shipping vs bar | TLA+ / independent verifier / Rust start ship or start in-tree. Lean 4 / F\* extraction is the bar, not a shipping claim. |

## Corrected wording (use these lines)

### Tamper-evident, not tamper-proof

Say **tamper-evident**. Do not say tamper-proof. A signer who controls the
signing key can omit or alter an event before signing. The protocol detects
changes made after the signature binds the canonical bytes.

### Insider threat limits

Signed envelopes attribute actor class and tool under the key that signed.
They do not stop a malicious insider with a valid key from signing a false
but well-formed statement. Detection of insider abuse needs organizational
controls outside the envelope (key custody, dual control, out-of-band review).

### Simulator N for detection rates

If a slide shows detection rates from a simulator, label the sample size **N**
explicitly and call the result a simulation outcome, not a field measurement.
Do not extrapolate simulator N to production false-negative rates.

### DARPA abstract

- Solicitation: IPTO office-wide BAA **HR001126S0011**.
- Amount: **$1.41M requested** (ROM), **not awarded**.
- Not QuANET. Do not place the abstract under QuANET or imply award.
- Domain I for this routing is **IPTO**, not MXO.

### Customer anonymization

Until written consent exists, use placeholders only:

- Hawaiʻi commercial bank
- utility operator
- PacSec divided-ledger
- payment-integration assessment

Do not name Bank of Hawaii or other identifiable customers in the deck.

### FIPS language

- FIPS 204 names the ML-DSA standard. Shipping an ML-DSA overlay is **software
  parameter readiness**, not a FIPS 140-3 validated module claim.
- Do not say "FIPS validated" or "CMVP certified" for Matrix Scroll or liboqs.

### Watermark / Notebook instruction

Remove any instruction to add a Gemini Notebook (or similar) watermark to
slides or evidence. Provenance is digest-pinned envelopes and git history, not
notebook chrome.

### Layers and canaries

Do not invent a SecGateway layer list or canary deployment narrative that is
not in the public repository. Stick to SPEC.md surfaces: envelopes, ledger,
Scroll Gate, optional receipts.

## Slide-by-slide guardrails (13 slides)

1. Title: product name + "offline-verifiable machine-action records".
2. Problem: unsigned agent/CI actions; fail-closed need.
3. What ships: envelopes, gate, ledger, independent verify.
4. Verdict contract: three values + Independence Firewall.
5. Crypto: Ed25519 now; ML-DSA overlay readiness (not CMVP).
6. Evidence: vectors, second verifier, TLA+.
7. Limits: tamper-evident; insider with key; simulator N.
8. Landscape: complements gittuf / Sigstore (see COMPARISON.md).
9. Pilots: anonymized placeholders only.
10. Funding/research: IPTO HR001126S0011, $1.41M requested, not awarded.
11. Roadmap: Rust verifier start; audit RFP; OpenSSF draft; CAVP/CMVP route.
12. Ask: pilot evidence pack, not certification language.
13. Contact: security@matrixscroll.com / SSX360 contact.

## Related

- [`docs/explanation/gold-standard.md`](../explanation/gold-standard.md)
- [`docs/ASSESSMENT_PROGRESS_2026-09-15.md`](../ASSESSMENT_PROGRESS_2026-09-15.md)
- [`docs/PILOT_EVIDENCE_PACK_TEMPLATE.md`](../PILOT_EVIDENCE_PACK_TEMPLATE.md)
