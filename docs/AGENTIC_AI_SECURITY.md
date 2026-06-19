# Agentic AI Security Mapping

This document maps Matrix Scroll to the joint guidance **Careful Adoption of
Agentic AI Services** published by ASD's ACSC, CISA, NSA, the Canadian Centre
for Cyber Security, NCSC-NZ, and NCSC-UK.

Official public sources verified for traceability:

- <https://www.cyber.gov.au/business-government/secure-design/artificial-intelligence/careful-adoption-of-agentic-ai-services>
- <https://www.cisa.gov/resources-tools/resources/careful-adoption-agentic-ai-services>
- <https://www.nsa.gov/aisc/>
- <https://www.cyber.gc.ca/en/news-events/joint-guidance-careful-adoption-agentic-artificial-intelligence-services>
- <https://www.ncsc.govt.nz/protect-your-organisation/careful-adoption-of-agentic-ai-services/>
- <https://www.ncsc.gov.uk/blogs/thinking-carefully-before-adopting-agentic-ai>

## What Matrix Scroll is — and is not

Matrix Scroll is **not** an agent runtime, model sandbox, IAM system, network
policy engine, or prompt-injection filter. It is a cryptographic evidence layer:
it signs what an agent was allowed to do, what it produced, who approved it,
and which root of trust attested to it. The SDK therefore complements, rather
than replaces, least-privilege IAM, sandboxing, monitoring, and incident
response.

## Guidance coverage summary

The machine-readable control matrix lives at
[`controls/agentic_ai_controls.json`](../controls/agentic_ai_controls.json).
`tests/test_agentic_guidance.py` fails if any claimed control lacks evidence.

| Control | Guidance theme | Matrix Scroll proof |
| --- | --- | --- |
| AAI-01 | Start small / bounded low-risk pilots | Signed evidence manifests constrain task, environment, and allowed/denied operations. |
| AAI-02 | Least privilege and explicit scope | Manifest fields capture resources, operations, expiry, and revocation. |
| AAI-03 | Avoid long-lived credentials | Evidence records temporary scoped credentials without embedding secrets. |
| AAI-04 | Human accountability | Owner, approver, reviewer, break-glass contact, and kill-switch fields are signed. |
| AAI-05 | Threat modeling | Threats are mapped to strict verification and tamper vectors. |
| AAI-06 | Secure defaults / validation | Wrong schema, algorithm, device id, malformed key, NaN, and unsigned manifests fail closed. |
| AAI-07 | Monitoring and auditability | Signed manifests are portable audit records verifiable offline. |
| AAI-08 | Incident response / kill switch | CI/CLI verification exits non-zero; manifests include escalation and shutdown metadata. |
| AAI-09 | Supply-chain management | Minimal deps, Dependabot, CI build verification, and conformance vectors. |
| AAI-10 | Strong authentication / non-repudiation | Ed25519 identity; the planned SSX360 hardware mode keeps private keys out of agent runtimes. |
| AAI-11 | Governance and change control | CODEOWNERS + CI protect spec/core/vectors/security files. |
| AAI-12 | Deception / prompt-injection resilience | Trust is verified after agent action; model text cannot forge signatures. |

## How this goes beyond the guidance

The guidance recommends established cybersecurity controls around agentic AI.
Matrix Scroll adds a stronger evidence layer on top:

1. **Offline verification** — auditors can verify a manifest without trusting
   Matrix Scroll servers, the original CI system, or the agent runtime.
2. **Hardware-rooted provenance path** — the SSX360 L2 design moves the signing
   key into a secure element so the agent cannot exfiltrate it as a normal
   credential. In v0.1.x, this is a typed provider path awaiting SE050 transport.
3. **Fail-closed policy gates** — the CLI returns exit `2` for tampered,
   unsigned, malformed, wrong-schema, wrong-algorithm, or wrong-device-id input.
4. **Executable conformance** — `vectors/` lets third-party implementations
   prove they match the protocol rather than merely claiming compatibility.
5. **Tamper-evident human accountability** — owners, approvers, reviewers, and
   break-glass contacts can be bound to the exact manifest an agent acted under.

## Recommended deployment pattern

1. Define the agent task as a low-risk, bounded pilot.
2. Create an evidence manifest like
   [`examples/agentic_ai_evidence_manifest.json`](../examples/agentic_ai_evidence_manifest.json).
3. Have a human owner approve the resource/operation/timeframe scope.
4. Sign the manifest with `matrixscroll sign`.
5. Require `matrixscroll verify` in CI before the agent can act or before its
   output can be accepted.
6. Retain the signed manifest with logs, SBOM, model/provider metadata, and
   incident-response records.

## Residual risks outside SDK scope

Matrix Scroll does not itself enforce IAM, sandboxing, egress rules, rate
limits, model safety, or data-loss prevention. Those controls must be supplied
by the host environment. Matrix Scroll proves that such controls were declared,
approved, signed, and not tampered with after signing.
