# Where Matrix Scroll fits

Matrix Scroll signs a declared authorization record at commit or action time.
It complements, rather than replaces, identity systems, source-control policy,
build provenance, artifact signing, and runtime security controls.

## Control boundaries

| Control area | Primary question | Matrix Scroll role |
| --- | --- | --- |
| Identity and access management | Who may access or change a system? | Consumes trusted-key and authorization policy; does not issue access |
| Source-control policy | Which changes may merge? | Supplies a signed record and range-verification result for policy checks |
| Build provenance | What process produced an artifact? | Supplies optional source-history evidence; does not attest the build |
| Artifact signing | Which key signed a release or image? | Separate control; Matrix Scroll records can be referenced by the release process |
| Runtime security | What code or process is executing now? | Outside protocol scope |
| Compliance assessment | Which evidence supports a control review? | Exports signed records and verification results for scoped review |

## Commit-time and artifact-time evidence

Matrix Scroll binds an envelope to a Git commit before or around push. Build
provenance and artifact-signing systems operate later, after CI has produced an
artifact. A complete software supply-chain review may use both:

1. Matrix Scroll records the declared actor class, tool, scope, and commit SHA.
2. Scroll Gate checks the selected commit range against key and policy inputs.
3. CI produces build provenance and signs the resulting artifact.
4. Reviewers compare the source-history and artifact evidence as separate
   control records.

## Signer choices

The file-backed provider is included for local use, tests, and CI. The completed
SSX360 USB signer keeps the Ed25519 private key inside an NXP SE050 secure
element and is supplied through [SSX360 contact](https://ssx360.com/contact).
Both paths produce the same public envelope format.

## Limits

- A valid envelope proves integrity and key possession, not authorization to
  use the key.
- Scroll Gate does not replace branch protection or reviewer approval.
- Matrix Scroll does not establish a SLSA level or certify compliance.
- Hardware custody, trusted-key registration, revocation, and offboarding are
  deployment responsibilities.

For protocol details, read [`SPEC.md`](../SPEC.md). For an implementation path,
start with [`FIVE_MINUTES.md`](FIVE_MINUTES.md).
