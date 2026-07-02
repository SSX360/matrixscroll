# Agent Attestation for Git Commits

**Signed provenance for agent-assisted code changes — verify offline, one command.**

## Executive summary

Agentic coding tools can commit and push code without a durable record of *who* acted (human, agent, or CI) or *which tool* produced the change. Review fatigue and credential theft make software-only gates insufficient. Matrix Scroll adds a cryptographic **commit envelope** — Ed25519-signed metadata bound to each Git commit — that anyone can verify offline or in CI.

This document distills the public product story. The full enterprise architecture lives in internal strategy materials; this whitepaper is scoped to developers, DevSecOps, and auditors adopting the open protocol today.

## Scope and audience

**Audience:** Software engineers using AI-assisted IDEs, platform teams wiring CI gates, security auditors.

**Covers:** Why Git commits are the Day-1 beachhead, protocol overview, install path, honest roadmap.

**Does not cover:** IAM replacement, prompt-injection mitigation, financial transaction gating, or hardware manufacturing details.

**Prerequisites:** Git, Python 3.10+, basic CI familiarity.

## What Matrix Scroll is — and is not

Matrix Scroll is **not** an agent runtime, sandbox, IAM system, or prompt filter. It is a **cryptographic evidence layer**: it signs what an agent (or human) attested at commit time and lets verifiers check that record without trusting the IDE or Matrix Scroll servers.

## Why Git commits first

| Vector | Risk | Why Matrix Scroll fits |
|--------|------|------------------------|
| **Git commits** | Rogue agent code, LLM filibustering in review, stolen tokens | Standardized hooks; high-consequence; maps to supply-chain guidance |
| Financial APIs | Fragmented rails, liability | Defer — integration cost too high for Day 1 |
| Database writes | Latency, engine sprawl | Defer — per-query hardware signing impractical |

Supply-chain incidents involving agent-assisted merges illustrate the gap: audit logs show *that* a commit landed, not *which actor class and tool* produced it with verifiable scope.

## Regulatory context (verified links)

Five Eyes agencies published joint guidance on careful adoption of agentic AI services:

- [CISA — Careful Adoption of Agentic AI Services](https://www.cisa.gov/resources-tools/resources/careful-adoption-agentic-ai-services)
- [ACSC — Careful adoption of agentic AI services](https://www.cyber.gov.au/business-government/secure-design/artificial-intelligence/careful-adoption-of-agentic-ai-services)
- [Canadian Centre for Cyber Security](https://www.cyber.gc.ca/en/news-events/joint-guidance-careful-adoption-agentic-artificial-intelligence-services)
- [NCSC-UK — Thinking carefully before adopting agentic AI](https://www.ncsc.gov.uk/blogs/thinking-carefully-before-adopting-agentic-ai)

Matrix Scroll maps these controls in [`docs/AGENTIC_AI_SECURITY.md`](AGENTIC_AI_SECURITY.md), including commit-envelope audit trails for monitoring (AAI-07) and supply-chain evidence (AAI-09).

## Protocol overview

Three layers:

1. **Identity** (`matrixscroll.identity.v1`) — Ed25519 key pair; device id `MS-XXXX-XXXX`
2. **Commit envelope** (`matrixscroll.commit_envelope.v1`) — commit object fields + provenance (`actor_type`, `tool`, optional scope manifest)
3. **Verification** — canonical JSON bytes, signature excluded; offline check with embedded public key

Full wire format: [`SPEC.md`](../SPEC.md). Schema: [`schemas/commit-envelope.v1.json`](../schemas/commit-envelope.v1.json).

```
  agent / IDE / CI
        │
        ▼
  git commit  ──►  post-commit hook signs envelope
        │
        ▼
  .git/matrixscroll/envelopes/<sha>.json
        │
        ▼
  matrixscroll envelope-verify <sha>   (local or CI)
```

## Step-by-step implementation

### 1. Install

```bash
pip install "matrixscroll==0.5.0"
matrixscroll hook-install
matrixscroll hook-status
```

### 2. Agent provenance

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-runner
git commit -m "feat: agent-assisted change"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

Hooks default to **warn mode**; set `"enforce": true` in `.git/matrixscroll/config.json` to block commits when signing fails. See [`docs/quickstart-git.md`](quickstart-git.md).

**Windows:** support landed in matrixscroll **0.2.1**; pin **0.5.0** in pilot environments.

### 3. CI gate

```yaml
- uses: SSX360/matrixscroll-verify-action@v1
  with:
    manifest: path/to/signed-manifest.json
    matrixscroll-version: "0.5.0"
    require-mode: emulated
    trusted-keys: trusted-keys.json
```

Policy flags (`--require-mode`, `--trusted-keys`) ship in the current release; this whitepaper pins `0.5.0` for copy-and-paste examples.

### 4. Optional scope manifest

Bind agent operations to a signed evidence manifest:

```bash
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

## Trust levels (honest roadmap)

| Level | Provider | Status |
|-------|----------|--------|
| **L1 Emulated** | Software key (`~/.matrixscroll/`) | Shipping |
| **L2 Hardware** | SSX360 / NXP SE050 secure element | In progress |
| **L3 Attested** | L2 + remote attestation | Roadmap |

External hardware key backend criteria are documented in
[`docs/yubikey-bridge.md`](yubikey-bridge.md). Non-Ed25519 bridge experiments
remain outside the public rollout.

## Common pitfalls

- **Expecting IAM replacement** — Matrix Scroll proves evidence; you still need least privilege and sandboxing.
- **Pre-commit expected_id** — v0.2.x signs **post-commit** with the actual SHA; do not bind envelopes before the commit exists.
- **Skipping enforce mode in production** — warn mode is for adoption; CI should fail closed on verify exit `2`.

## Conclusion and next steps

1. Install hooks in a pilot repo with `MATRIXSCROLL_ACTOR_TYPE=agent`.
2. Add verify-action to CI on protected branches.
3. Read the control mapping in [`docs/AGENTIC_AI_SECURITY.md`](AGENTIC_AI_SECURITY.md).
4. Follow protocol changes via [`CHANGELOG.md`](../CHANGELOG.md) and GitHub releases.

Questions: [GitHub Discussions](https://github.com/SSX360/matrixscroll/discussions) or security@matrixscroll.com for vulnerabilities.

## References

- Matrix Scroll spec: [`SPEC.md`](../SPEC.md)
- Agentic AI mapping: [`docs/AGENTIC_AI_SECURITY.md`](AGENTIC_AI_SECURITY.md)
- Git design spec: [`docs/superpowers/specs/2026-06-19-matrixscroll-git-design.md`](superpowers/specs/2026-06-19-matrixscroll-git-design.md)
- CISA agentic AI guidance (link above)
- Conformance vectors: [`vectors/`](../vectors/)
