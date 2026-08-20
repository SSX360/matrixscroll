# SLSA source evidence context

SLSA applies requirements to software supply-chain provenance. Matrix Scroll
adds signed commit-time records that can support a reviewer examining source
history, but the protocol does not establish or certify a SLSA level.

## Evidence Matrix Scroll can provide

| Review question | Matrix Scroll evidence | Deployment dependency |
| --- | --- | --- |
| Which commit was assessed? | Commit SHA bound into a signed envelope | Git repository history |
| Which actor class and tool were declared? | `provenance.actor_type` and `provenance.tool` | Accurate declaration by the signer |
| Was the record altered? | Ed25519 signature over canonical bytes | Trusted public-key policy |
| Did every selected commit carry a valid record? | Scroll Gate range result | Correct base and head refs |
| Was protected review enforced? | External branch and review evidence | Forge configuration and organization policy |
| What artifact did CI build? | Not provided by Matrix Scroll | Build provenance such as SLSA or Sigstore |

## Use in an assessment

Treat Matrix Scroll envelopes and range results as source-history evidence. Pair
them with branch-protection records, reviewer approvals, build attestations, and
artifact signatures where those controls are in scope.

Use language such as "provides signed commit-time evidence for SLSA review."
Do not claim a SLSA level, SLSA certification, or complete build provenance from
Matrix Scroll alone.
