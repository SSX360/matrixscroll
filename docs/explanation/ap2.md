# How Matrix Scroll relates to AP2

AP2 is adjacent to Matrix Scroll, not competitive with it, and not a dependency
of it. This page exists so the relationship is stated once, accurately, in a
place readers reach deliberately. It does not belong on a landing page.

## What AP2 is

The Agent Payments Protocol answers one question: did a human authorize what the
agent did? Google announced it on 16 September 2025 with more than 60 launch
partners, including Mastercard, PayPal, Coinbase, American Express, and
Salesforce. It carries three signed mandates, Intent, Cart, and Payment, as W3C
Verifiable Credentials, so a merchant or network holds a cryptographic record of
what the user consented to rather than an inference drawn from behaviour.

On 28 April 2026 Google published AP2 v0.2 and donated the protocol to the FIDO
Alliance, moving it from vendor-controlled to community-governed. Sixty
organizations joined the donation. The v0.2 release added "Human Not Present"
payments, which let an agent execute a pre-authorized transaction when the owner
is not on the call, and Verifiable Intent, a companion standard co-developed
with Mastercard and also donated to FIDO, which specifies a tamper-proof log of
user-authorized agent actions.

The accurate description today is Google-initiated and FIDO-governed. Describing
AP2 as "Google's protocol" was correct in 2025 and is now out of date.

## Where the overlap actually is

Both AP2 and Matrix Scroll are authorization-evidence systems. Both answer a
question about a mandate rather than a question about an artifact. The mandate
chain is the shared concept: an authorization granted by a human, delegated to a
machine, exercised at some later moment, and provable afterward by someone who
was not there.

They cover different segments of that chain.

| | AP2 | Matrix Scroll |
| --- | --- | --- |
| Question | Did a human authorize this payment? | Who or what signed this commit? |
| Subject | A transaction | A Git commit, a CI step, a tool surface |
| Artifact | Intent, Cart, and Payment mandates | Commit and action envelopes |
| Governance | FIDO Alliance | Open specification, CC0 vectors |
| Verifier | Merchant, network, credential provider | Anyone, offline |

An agent that writes code and an agent that spends money need the same property:
a record of authorization that survives the session and can be checked by a
party who does not trust the session. AP2 built that for money. Matrix Scroll
builds it for code and for the machine actions around code.

## Why they are not merged

AP2 mandates are scoped to a payment context and governed by a payments
standards body. Commit provenance is not a payment, has no merchant, and needs
to verify with no network at all. Binding the two would import a governance
model and a trust model that commit signing does not need.

The honest relationship is interoperability, not integration. An organization
that adopts AP2 for agent payments and Matrix Scroll for agent code changes ends
up with two mandate chains covering two blast radii, and an auditor can read
both.

## What this does not claim

Matrix Scroll does not implement AP2. It is not AP2-certified, and no such
certification exists. The L4 Money layer in the authorization ladder is a demo,
not a shipped capability. This page is evidence mapping between two protocols,
not a certification claim.

## Sources

- [Announcing Agent Payments Protocol (AP2)](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol), Google Cloud, 16 September 2025
- [Google donates Agent Payments Protocol to FIDO Alliance](https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/), Google, 28 April 2026
- [FIDO Alliance to develop standards for trusted AI agent interactions](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/)
- [AP2 specification](https://github.com/google-agentic-commerce/AP2)
