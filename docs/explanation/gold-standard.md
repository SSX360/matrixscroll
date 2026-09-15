# The formal mathematics of accountability

This page is the **gold standard** for Matrix Scroll. Every protocol change,
verifier change, and public claim is judged against it. The diagram is the
compact form; the sections below map each box to what ships in
`matrixscroll==0.10.0` and what remains the bar.

![Matrix Scroll: The Formal Mathematics of Accountability. Pipeline from raw event through domain-separated hash and time-epoch batching to a FIPS 204 ML-DSA signature, three pillars (post-quantum proofs, offline verification, fail-closed architecture), and the Rule of Refusal.](../assets/formal-mathematics-of-accountability.png)

## Pipeline

| Stage | Gold-standard label | Shipping now | Bar |
| --- | --- | --- | --- |
| 1 | Raw event | Commit SHA, action record, MCP tool surface, or agent trace bytes | Keep every verified input reconstructible from raw records |
| 2 | Domain-separated hash | `matrixscroll.ledger` tags (`matrixscroll/v1/record`, `/leaf`, `/node`, `/epoch`) over canonical JSON per `SPEC.md` §4 and §12 | Keep tags stable across languages |
| 3 | Time-epoch batching | Signed ledger epoch checkpoints (`matrixscroll.ledger_epoch.v1`) with Merkle root over the range; Scroll Gate still walks `base..head` for Git | Optional witness cosignatures and live transparency-log receipts |
| 4 | Post-quantum signature | Ed25519 base signature; optional FIPS 204 ML-DSA / FIPS 205 SLH-DSA overlay via `matrixscroll[pqc]` (default ML-DSA-87) | Parameter readiness only; not FIPS CMVP or CNSA certification |

## Three pillars

### Post-quantum proofs

Attestation must survive the quantum computers the programme monitors. Shipping
path: FIPS 204 ML-DSA and FIPS 205 SLH-DSA overlays through liboqs, with NIST
ACVP sample vectors in `vectors/`. Naming those parameter sets is evidence
mapping, not a certification claim.

### Offline verification

An independent auditor reconstructs events from raw records without a Matrix
Scroll account. Shipping path: CLI and CI verify offline; `tools/independent_verify.py`
re-implements SPEC.md sections 3 to 6 and must match the SDK on the conformance vectors;
TLA+ models in `formal/tla/` are checked by TLC.

**Bar:** a machine-checked verifier core in Lean 4 or F\* with an extracted
executable. That extraction is the long-term gold standard. Until it lands, the
independent verifier plus TLC models are the enforceable substitute.

### Fail-closed architecture

Every result is classified as **CONSISTENT**, **INCONSISTENT**, or
**INDETERMINATE**. The verifier never returns a silent pass on missing evidence.

| Verdict | Meaning | Exit code today |
| --- | --- | --- |
| CONSISTENT | Evidence present and verifies | `0` |
| INCONSISTENT | Evidence present and fails (tamper, wrong key, drift, empty enforce range) | `2` |
| INDETERMINATE | The tool could not complete verification (missing module, unresolvable ref, runner fault) | `1` |

Scroll Gate fails closed on an empty `base..head` range unless the caller sets
`--allow-empty-range`. See [exit codes](../reference/exit-codes.md).

## The Rule of Refusal

We refuse to accept AI-generated or AI-altered data into the verified core. The
provenance of every artifact is digest-pinned. No AI system is a decision
authority for any technical conclusion.

Operational consequences:

1. Conformance vectors, ACVP fixtures, TLA+ models, schemas, and SPEC text are
   human-owned artifacts under digest or git history. Do not regenerate them from
   a model and land them as authority.
2. Agents may draft envelopes and pull requests. Humans (or CI policy that a
   human wrote) decide merge, release, and claim language.
3. An LLM output is never a substitute for `matrixscroll verify`,
   `envelope-verify-range`, TLC, or the independent verifier.

## How to use this standard

Before merging a change that touches crypto, verification, gates, or public
copy, ask:

1. Does the change preserve offline reconstruction from raw records?
2. Does every failure path still map to CONSISTENT, INCONSISTENT, or
   INDETERMINATE (no silent pass)?
3. Does any claim about ML-DSA, SLH-DSA, Lean, or F\* stay inside the Shipping
   now / In progress / Not boundary?
4. Does the change keep AI out of the verified core and out of decision
   authority?

If any answer is no, the change fails the gold standard.
