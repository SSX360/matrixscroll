# SSX360 style supplement

The written standard is the
[Google Developer Documentation Style Guide](https://developers.google.com/style).
It is chosen because the primary reader is a developer evaluating a security
library, which is exactly the audience it was written for. The
[Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/)
is the secondary reference for marketing-site tone, where a warmer register is
appropriate.

This page covers only what those guides do not: house terms, house bans, and the
claims discipline that an audit vendor needs.

## House terms

| Term | Definition | Do not write |
| --- | --- | --- |
| **envelope** | A signed JSON record binding an actor, tool, and optional scope to a commit or action. The unit of evidence. | "receipt", "certificate", "token" |
| **actor** | The entity that produced a change: `human`, `agent`, or `ci`. A declared role, not a verified identity. | "user", "author", "identity" |
| **Scroll Gate** | The pull-request verification path that checks every commit in a range. Partial SLSA L1-2. | "the gate", "compliance gate", "security gate" |
| **mandate chain** | The path from a human authorization, through delegation, to a machine action, provable afterward. Shared vocabulary with AP2. | "audit trail", "chain of custody" |
| **emulated mode** | The software signer. The default and the supported evaluation path. L1. | "demo mode", "test mode", "insecure mode" |
| **hardware mode** | The secure-element path. A bench prototype, not generally available. L2 prototype. | "hardware support", "secure mode", anything implying availability |
| **evidence mapping** | The relationship between Matrix Scroll output and a compliance framework. | "compliance", "certification", "coverage" |

Write "Matrix Scroll" with a space for the protocol and the brand. Write
`matrixscroll` lowercase for the package, the CLI, and the module.

## Banned words

Enforced by `SSX360.Slop` at `error`. Not negotiable in user-facing prose.

seamless, seamlessly, cutting-edge, robust, game-changer, game-changing, unleash,
elevate, next-gen, next-generation, revolutionize, delve into, tapestry,
leverage, harness, empower, state-of-the-art, best-in-class, world-class,
paradigm shift, supercharge, unlock new possibilities, in today's landscape, the
future of, ever-evolving, rapidly evolving, deep dive, holistic, synergy,
turnkey, frictionless, bleeding-edge, military-grade, bank-grade, unbreakable,
bulletproof, future-proof, iron-clad.

Every one of these is a word chosen to avoid naming a thing. Name the thing.

## Dashes

Zero em-dashes (—). Zero en-dashes used as a separator ( – ). Use a hyphen, a
comma, a period, or parentheses.

An en-dash between digits is a numeric range and stays legal: "SLSA L1-2",
"2024-2025". The ban is on the dash as a rhetorical pause.

This is a house decision, not a claim about writing quality. Reasonable people
argue the em-dash ban is superstition, and the research generally supports them:
the em-dash is a legitimate punctuation mark that predates language models by
centuries. The ban is adopted anyway because the site copy is already
standardized on it and one consistent rule beats a per-page argument. It is
scoped to user-facing content and does not apply to code, vendored text, or
third-party quotations.

## Negative parallelism

One deliberate instance per page, maximum.

The construction is "X is not Y", "not X, but Y", "It's not X, it's Y", and the
bare appositive "Notary, not watchtower". It is the single most recognisable
structural tell in current AI prose, and it is genuinely effective once, which
is why it proliferates.

`SSX360.NegativeParallelism` flags every occurrence as a `warning` rather than an
error, because the rule cannot count per page and because one instance is
correct. A human decides which one survives.

The approved positioning lines use this construction deliberately and are exempt:

- "Everyone audits the money. Nobody audits the authorization."
- "We prove your mandate chain is complete. Nothing altered, nothing hidden."
- "We hold no keys and sell no platform. That is what makes the signature worth something."

## Register

Developer surfaces get one concrete declarative sentence. The PyPI summary,
"Signed provenance for agent-assisted Git commits with offline verification", is
the right class: compare ruff's "An extremely fast Python linter and code
formatter, written in Rust."

The mystical register belongs on the marketing site or nowhere. "They receipt the
model call. We receipt everything the machine does." is not a description; a
reader cannot tell from it what the software does. `SSX360.Register` flags that
family.

## Claims discipline

This is the section that matters most, because SSX360 sells independent
assessments and a false claim in its own documentation is disqualifying.

**Compliance.** Wherever DORA, PCI DSS, the EU AI Act, SOC 2, NIST, the SSDF, or
the FS-AI RMF is named, the file must carry "evidence mapping, not a
certification claim" or an equivalent hedge. Enforced by
`SSX360.ComplianceHedge` at `error`.

Never write that anything is certified, is compliant with a framework, meets a
framework's requirements, is required by a framework, guarantees compliance, or
is audit-proof. Enforced by `SSX360.Certification` at `error`.

**Hardware.** State the bench-prototype status every time. Never write that
hardware ships, is available, or is validated without "prototype, not generally
available" attached. See
[Trust boundaries and the hardware roadmap](trust-boundaries.md).

**Versions.** The shipping version is whatever `pyproject.toml` and the PyPI JSON
API agree on. Pin it explicitly in every install example. Three properties
asserting three different versions is a credibility failure, not a documentation
bug.

## Honest limits

Every surface that makes a capability claim carries a "Shipping now / In
progress / Not" block. The README's "Honest limits" section is the model. This is
the single strongest asset in the copy and the clearest differentiator against
vendors selling fear, and it belongs on the marketing pages too, not only in the
README.

Deleting or softening an honest-limits section is a regression, whatever it does
to conversion.
