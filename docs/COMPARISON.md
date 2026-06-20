# How Matrix Scroll Compares

Matrix Scroll signs **Git commit envelopes** — cryptographic evidence of who (human, agent, CI) produced a change, attached inside the commit. This page is an honest map of adjacent tools. Most are **complementary**, not replacements.

**Positioning in one line:** Sigstore and SLSA answer “what was built in CI?” Matrix Scroll answers “who signed this commit before push?”

## At a glance

| Tool | Layer | Signs commits? | Agent identity | Hardware root of trust | Open source |
|------|-------|----------------|----------------|------------------------|-------------|
| **Matrix Scroll** | Commit | Yes (envelope in commit) | Yes | Yes (SSX360 / SE050 path; emulated L1 today) | Protocol + SDK |
| [agentmark](https://github.com/karta-oss/karta) | Commit + CI gate | Yes (manifest in message) | Yes (pipeline key) | No | Apache 2.0 |
| [Alien Agent ID](https://github.com/alien-id) | Commit (git notes) | Yes | Yes (owner-bound via OIDC) | No | SDK on GitHub |
| [ForgeProof](https://github.com/forgeproof/forgeproof) | File-level | No | Partial (model/provider) | No | Apache 2.0 |
| [Sigstore / cosign](https://docs.sigstore.dev/) | Artifact / container | No | No | No (keyless OIDC) | Yes |
| [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) | CI artifact | No | No | No | Partial |
| [SLSA](https://slsa.dev/) | Build provenance framework | No | No | N/A | Yes |
| [in-toto](https://in-toto.io/) | Pipeline layout | No | No | Functionary keys | Yes |
| [OpenSSF GUAC](https://github.com/guacsec/guac) | Aggregation graph | No | No | N/A | Yes |

Runtime audit tools (Provedex, ProvenanceOne, etc.) log **what agents do at runtime** — useful, but they do not bind authorship to Git history.

## Closest commit-level competitors

### agentmark

- **Similar:** Commit-time Ed25519 manifest, CI verification gate, EU AI Act Article 50 cited as a use case.
- **Different:** Software pipeline keys (exfiltration risk). Matrix Scroll targets **hardware-sealed** Ed25519 (SSX360) with offline verify; emulated L1 ships today.
- **Takeaway:** Strongest software-only peer. Matrix Scroll differentiates on tamper-resistant keys and commit-embedded envelopes.

### Alien Agent ID

- **Similar:** Ed25519 commit signing, public verification story.
- **Different:** Owner binding via cloud OIDC/DPoP; proof bundles in git notes. Matrix Scroll emphasizes **offline verification** and dedicated hardware, not a hosted identity network.
- **Takeaway:** Alien leads on human→agent delegation chains; Matrix Scroll leads on hardware non-repudiation without cloud dependency.

### ForgeProof

- **Similar:** Ed25519 + SHA-256 provenance for AI-assisted code.
- **Different:** **Per-file receipts** before build, not commit envelopes. Provenance is a separate artifact; Matrix Scroll embeds evidence in every clone of the repo.
- **Takeaway:** Complementary granularity (file vs commit); potential interop, not a fork in the road.

## Established supply chain (CI / artifact)

Sigstore, GitHub attestations, SLSA, in-toto, and GUAC secure **build outputs and pipeline steps**. They do not record which AI tool authored a line at commit time.

Matrix Scroll envelopes can **feed** these systems (e.g., as in-toto link metadata or GUAC evidence) rather than compete with them.

## What Matrix Scroll adds that others don’t combine

1. **Commit-time** signing (not post-build artifact attestation)
2. **Agent/human actor** in the envelope schema
3. **Hardware root of trust** path (SSX360 / NXP SE050) plus emulated dev mode today
4. **Offline verify** — `matrixscroll verify` or [matrixscroll.com/verify](https://matrixscroll.com/verify)

No single competitor listed above combines all four today.

## Honest gaps (what we’re still building)

- **CI gate:** Scroll Gate ships in **0.2.3+** — PR commit-range verification via `envelope-verify-range`, git notes transport (`refs/notes/matrixscroll`), and filesystem bundles. [`matrixscroll-verify-action`](https://github.com/SSX360/matrixscroll-verify-action) supports `head-ref`/`base-ref` range mode with agent/human counts.
- **Owner/delegation attestation:** Optional `delegation` block in commit envelope schema (**0.2.4+**); see [`delegation-attestation-rfc.md`](delegation-attestation-rfc.md). Alien still leads on OIDC/DPoP owner binding.
- **Multi-agent commits:** Multiple actors in one envelope — on the roadmap.
- **Rekor / GUAC export:** Dry-run CLI ships in **0.2.5** (`envelope-publish-rekor`, `envelope-export-guac`); full Rekor upload integration still in progress.
- **Hardware:** SSX360 reference device and Scroll Key retail are **in progress**; L1 emulated key is what you can use now.

## When to use what

| You need… | Reach for… |
|-----------|------------|
| Container/image signatures, Rekor log | Sigstore / cosign |
| SLSA Level 3 build provenance on GitHub Actions | `slsa-github-generator` + artifact attestations |
| Supply chain graph / SBOM aggregation | GUAC |
| Prove an AI pipeline wrote code with no human edit path (software keys) | agentmark |
| Bind agent commits to a hosted human identity chain | Alien Agent ID |
| Per-file “which model wrote this file” receipts | ForgeProof |
| **Hardware-backed, commit-embedded agent provenance with offline verify** | **Matrix Scroll** |

## Further reading

- Full research brief (internal): `research/competitive-landscape-2026-06.md` in the SSX360 launch kit
- [Whitepaper](WHITEPAPER.md) — threat model and envelope design
- [SPEC.md](../SPEC.md) — wire format and verification rules

*Last updated: June 2026. Comparisons reflect public docs and OSS repos; contact security@matrixscroll.com for corrections.*
