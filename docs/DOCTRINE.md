# Master Doctrine — SSX360 / Matrix Scroll

Codebase-level direction. Audience: anyone touching this system — internal, contract, or partner. Independent of any deal, signature, or person. If a decision isn't covered here, derive it from the doctrine.

## The one thesis

AI agents now write code and move money at machine speed. Nobody can prove who authorized what. We own the proof layer: signed at the moment of action, verified before merge, exported as evidence an assessor can read without us in the room.

Everything in this codebase either strengthens that sentence or doesn't belong in it.

## Doctrine — the five rules every commit answers to

### 1. We are the trust layer, never the platform.

We do not build version control. We do not build a forge. We do not build payment rails. Those categories monetize at zero (DVCS), require a decade and a billion dollars (forge), or are owned by card networks and FIDO working groups (rails). We are the provenance layer that rides on all of them — git, GitHub, GitLab, Forgejo, Gitea, any Actions-syntax CI, any payment protocol that emits signed mandates. Forge-agnostic and rail-agnostic is the moat. Any code that couples us to one platform is technical debt on arrival.

### 2. The assessor is the user.

The buyer is a security or platform team, but the user who decides if we win is the auditor who receives the Evidence Pack. Every schema, export, log line, and doc is written for a person who will read it cold, without a founder on the call. Stable schema versions, changelogs, field glossaries, verify instructions that stand alone. If an artifact needs us to explain it, the artifact is unfinished.

### 3. Every claim must be falsifiable — in marketing, in code, in README.

The Honest Limits section is the brand. Emulated signing is called emulated. Hardware in firmware validation is not "hardware-backed signing." Illustrative deployment profiles carry their disclaimer. "Aligned to SSDF / EU AI Act," never "certified" until a third party says so. The site, the PyPI page, the action README, and the sales deck must say the identical thing — the buyer we want is trained to find the gap, and finding one costs us the category. Unfalsifiable copy ("100% of AI writes") is a bug; file it and fix it like one.

### 4. Dogfood the provenance or don't ship it.

Our own releases carry signed provenance, pinned versions, checksums, and attestations — the pipeline is the demo. One supported release line, stated support policy, org-owned maintainer accounts, no personal tokens in the release path. A provenance company with a sloppy supply chain is a contradiction the market will not forgive. The release train is a product surface, not plumbing.

### 5. Meet buyers at the migration, sell them the evidence.

The market's live pain: unattributed machine-speed writes are breaking platforms, and security-conscious teams are re-platforming to self-hosted and sovereign forges — where they lose native attestation and must bring their own trust layer. That is our insertion point. Distribution is the open protocol (spec, conformance vectors, verifier, integrations — aggressively boring, zero commercial copy); revenue is the control plane (policy, evidence, SSO, hardware-bound identity, support). The spear stays sharp and free; the handle is what we sell.

## Double down — where all optimization effort goes

- **Evidence Pack** as the flagship artifact. Signed, versioned, downloadable, self-verifying, mapped field-by-field to the frameworks we name. Optimize its legibility before optimizing anything else.
- **Verification everywhere git goes.** CI gate hardening, server-side enforcement for self-hosters, offline verify, browser verify. Verification speed, determinism, and zero-false-positive behavior are the performance metrics that matter.
- **Forge-agnostic integrations** as first-class citizens: the same install, the same gate, the same export on GitHub, GitLab, and Forgejo/Gitea. Treat every integration doc as a landing page.
- **Hardware as device-bound identity** — activation, custody, revocation, offboarding. One clear story. The secure-element signing path graduates from preview only when firmware validation passes, and not one sentence sooner.
- **Crawlability and machine-readability** of everything public. Specs, docs, llms.txt, sitemaps, plain-markdown paths. When a buyer's AI assistant is asked "what is Matrix Scroll," our own text must be the answer.

## Hold — maintained, not grown

- **Agent-commerce (AP2/mandates):** the envelope format already fits signed mandates; keep the mapping document current and the demo honest. It graduates to product only on a written pull from a payments buyer or a certifiable third-party role in the standards output. Until then it is a narrative, clearly badged, and it never leads the homepage story to a security buyer.
- **Digital Rain / studio:** the live demo of "agent builds with provenance." It exists to make the proof layer visible, not to become a second product line.

## Killed — do not resurrect without a scored memo

Building a DVCS. Building or hosting a forge. Competing on scanning/analysis (partner narrative only). Payment-rail infrastructure. Silicon beyond the validated path until revenue demands it. Any second go-to-market motion that splits focus from the security buyer.

## The test

Before merging, shipping, or publishing, ask in order:

1. Does this make the proof stronger, the verify faster, or the evidence more legible?
2. Would it survive an adversarial reader — an assessor, a CISO's counsel, a competitor — with zero explanation from us?
3. Does it work on every forge and rail, or does it marry us to one?
4. Are we running the same provenance on ourselves that we sell?
5. Is every word of it falsifiable?

Five yeses: ship. Any no: it's not done.
