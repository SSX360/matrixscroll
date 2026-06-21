# Commit-Time Proof vs Artifact-Time Proof

Matrix Scroll is easiest to understand when compared to the supply-chain tools
developers already know.

## The short version

- **Matrix Scroll:** "Who signed this commit before push?"
- **Sigstore / GitHub attestations / SLSA:** "What was built in CI?"

These answers are different, and mature teams usually want both.

## Side-by-side

| Question | Matrix Scroll | Sigstore / GitHub attestations / SLSA |
|----------|---------------|----------------------------------------|
| Primary layer | Git commit | Build artifact |
| Timing | Before push | After build |
| Main unit | Commit envelope | Package, container, or predicate |
| Actor / tool in record | Yes | Usually no |
| Offline verify | Yes | Varies by workflow |
| Hardware path | In progress | External to the standard flow |

## Where Matrix Scroll fits

Use Matrix Scroll when you need:

- evidence that an agent, CI job, or human produced a commit
- a verifier that works on any clone
- a commit-native gate before merge

Use artifact-layer tools when you need:

- release signing
- container provenance
- SBOM / predicate chains
- deployment and registry policy

## How to use them together

1. Sign agent-assisted commits with Matrix Scroll.
2. Verify commit ranges in PRs with `SSX360/matrixscroll-verify-action@v1`.
3. Keep Sigstore, GitHub attestations, or SLSA on the release path.

That gives teams both commit-time attribution and artifact-time provenance.

## Public proof links

- [Compare page](https://matrixscroll.com/compare/)
- [Browser verifier](https://matrixscroll.com/verify/)
- [SPEC.md](../SPEC.md)
