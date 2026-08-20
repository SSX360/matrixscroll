# Signed authorization records for Git commits

**Declare who or what authorized a machine action, sign the record, and verify it offline.**

## Executive summary

Automated development tools, CI jobs, and people can all create Git commits. The normal Git record does not carry a portable declaration of the actor class, tool, or authorization scope. Matrix Scroll adds an Ed25519-signed **commit envelope** bound to the commit so reviewers can verify that declaration offline or in CI.

This whitepaper is scoped to developers, platform teams, security reviewers, and auditors evaluating the open protocol.

## Scope and audience

**Audience:** Software engineers, platform teams wiring CI gates, security reviewers, and auditors.

**Covers:** Why Git commits are a useful control point, the protocol, the install path, and current limits.

**Does not cover:** IAM replacement, prompt-injection mitigation, financial transaction gating, or hardware manufacturing details.

**Prerequisites:** Git, Python 3.10+, basic CI familiarity.

## What Matrix Scroll is and is not

Matrix Scroll is a **cryptographic evidence layer**. It signs a declared actor, tool, and optional scope at commit time and lets reviewers check that record without relying on the originating IDE or a Matrix Scroll server. It is not an IAM system, sandbox, prompt filter, or runtime.

## Why Git commits first

| Vector | Risk | Why Matrix Scroll fits |
|--------|------|------------------------|
| **Git commits** | Missing actor and tool context, stolen credentials | Standard hooks, stable object identifiers, and pre-merge policy checks |
| Financial APIs | Authorization, liability, and rail-specific semantics | Requires a separate implementation and policy model |
| Database writes | Latency and engine-specific controls | Requires a separate implementation and policy model |

Repository logs show that a commit landed. A Matrix Scroll envelope adds a signed declaration of the actor class, tool, and optional scope.

## Regulatory context (verified links)

Compliance references in this project are evidence mappings. They help a reviewer identify which Matrix Scroll records may support a control question; they do not claim certification or complete compliance.

Five Eyes agencies published supplementary joint guidance on careful adoption of agentic AI services (maps to controls; not a forcing function):

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
pip install "matrixscroll==0.7.0"
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

**Windows:** support landed in matrixscroll **0.2.1**; pin **0.7.0** in pilot environments.

### 3. CI gate

```yaml
- uses: SSX360/matrixscroll/.github/actions/verify@action-v1
  with:
    manifest: path/to/signed-manifest.json
    matrixscroll-version: "0.7.0"
    require-mode: emulated
    trusted-keys: trusted-keys.json
```

Policy flags (`--require-mode`, `--trusted-keys`) ship in the current release; this whitepaper pins `0.7.0` for copy-and-paste examples.

### 4. Optional scope manifest

Bind agent operations to a signed evidence manifest:

```bash
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

## Signing providers

| Provider | Key custody | Availability |
| --- | --- | --- |
| File-backed | Software key under `~/.matrixscroll/` | Included in `matrixscroll==0.7.0` |
| SSX360 USB signer | NXP SE050 with RP2350 USB bridge | Supplied through `ssx360.com/contact` |

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
