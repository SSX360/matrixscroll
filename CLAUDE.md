# CLAUDE.md

Always-on rules for writing prose in this repository. The full style guide is a
separate, on-demand Skill (`ssx360-prose`); this file stays short on purpose,
because it is loaded into every context window.

Run `vale --minAlertLevel=error` before you start and again before you finish.
The linter gets the last word, never you. See
[`docs/explanation/writing-workflow.md`](docs/explanation/writing-workflow.md).

## Voice

- Active voice. "The verifier rejects the envelope", not "the envelope is
  rejected by the verifier".
- Sentence case for every heading. "Exit codes", not "Exit Codes".
- Second person for instructions. "Run the command", not "the user runs".
- Present tense. "The gate blocks the merge", not "will block".

## Name real things

Every paragraph must name something a reader could look up: a command, a file, a
field, an exit code, a version, a date. A paragraph that only names categories is
a paragraph that says nothing. Delete it or replace it with the specific.

## Banned words

seamless, seamlessly, cutting-edge, robust, game-changer, unleash, elevate,
next-gen, revolutionize, delve, tapestry, leverage, harness, empower,
state-of-the-art, best-in-class, world-class, paradigm shift, supercharge,
frictionless, turnkey, holistic, synergy, bleeding-edge, military-grade,
bulletproof, future-proof, "in today's landscape", "the future of", "deep dive",
"rapidly evolving".

Also cut: "it is important to note that", "it should be noted that", "in order
to", "utilize", "prior to", "leverage" as a verb.

## No em-dashes

Zero em-dashes (—). Zero en-dashes used as a separator ( – ). Use a hyphen, a
comma, a period, or parentheses. Use a hyphen for numeric ranges, as in
"2024-2025".

## One negative parallelism maximum

"X is not Y", "not X, but Y", "It's not X, it's Y", "Notary, not watchtower".
One deliberate instance per page, maximum. It is the most recognisable structural
AI tell. Vale flags every occurrence as a warning; you decide which one survives.

Retired AP2 mandate-chain slogans stay retired. Do not reinstate them.

## Gold standard

[`docs/explanation/gold-standard.md`](docs/explanation/gold-standard.md) is the
bar for protocol and claims work. Post-quantum proofs, offline verification,
fail-closed CONSISTENT / INCONSISTENT / INDETERMINATE verdicts, and the Rule of
Refusal bind every public surface. Do not claim a Lean 4 / F\* extracted
verifier until it exists in the tree.

## Evidence mapping, not certification

Wherever DORA, PCI DSS, the EU AI Act, SOC 2, NIST, the SSDF, or the FS-AI RMF is
named, the file must carry "evidence mapping, not a certification claim" or an
equivalent hedge.

Never write that anything is certified, is compliant with a framework, meets a
framework's requirements, is required by a framework, guarantees compliance, or
is audit-proof.

## Claims that must stay true

- **Version.** The published version is `0.9.0`. It is set in `pyproject.toml`
  and confirmed by `https://pypi.org/pypi/matrixscroll/json`. Pin it explicitly
  in every install example. Supported line: 0.7.0–0.9.0. Never assert a version
  you have not checked.
- **Custody.** Device-agnostic `IdentityProvider`; default is emulated
  file-backed keys. Do not describe a USB/SE050 host path as shipping on PyPI.
- **Business structure.** SSX360 is the audit entity and sells assessments.
  Matrix Scroll is the open protocol, free permanently, never monetized.
  Research is the newsletter, index, and incident registry. Selling software to
  an audit client destroys independence and is forbidden; do not write copy that
  does it.

## Preserve verification boundaries

Every surface making a capability claim carries a "Shipping now / In progress /
Not" block. Never delete or soften one. It is the strongest asset in the copy.

## Rule of Refusal

Do not land AI-generated or AI-altered bytes as authority in the verified core
(vectors, ACVP fixtures, TLA+ models, schemas, SPEC). Digest-pin provenance.
No AI system is a decision authority for any technical conclusion.

## Register

Developer surfaces get one concrete declarative sentence, in the class of
"Signed machine-action records with offline verification".
Keep the mystical register off developer surfaces entirely.
