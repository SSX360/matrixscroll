# Agent Quickstart

Use Matrix Scroll to sign agent-assisted commits with verifiable provenance,
without coupling public docs to a specific editor or assistant brand.

## One-time setup

```bash
pip install "matrixscroll>=0.4.1"
matrixscroll hook-install
```

## Optional local policy

Save this as `.git/matrixscroll/config.json` when you want hooks to enforce
agent attribution and publish envelopes to git notes before push:

```json
{
  "enforce": true,
  "actor_type": "agent",
  "tool": "agent-runner",
  "publish_notes": true
}
```

## Per-session environment

Set these before the agent runtime makes Git commits:

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-runner
export MATRIXSCROLL_TOOL_VERSION=2026.06
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

`MATRIXSCROLL_TOOL` is free-form provenance metadata. Use a generic public label
such as `agent-runner`, or your own internal runtime name if you do not want to
publish vendor branding in commit metadata.

## Commit and verify locally

```bash
git commit -m "feat: agent-assisted change"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

## Before opening a PR

Publish envelopes to git notes so CI can verify the PR range:

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
git push origin HEAD
```

## CI gate

Add [`examples/ci/protected-branch.yml`](../examples/ci/protected-branch.yml)
to `.github/workflows/provenance.yml`.

See also: [`quickstart-git.md`](quickstart-git.md), [`quickstart-claude-code.md`](quickstart-claude-code.md).
