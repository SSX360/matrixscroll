# Agent quickstart: Cursor

Use Matrix Scroll to sign **agent-assisted commits** from Cursor with verifiable provenance.

## One-time setup

```bash
pip install "matrixscroll>=0.2.5"
matrixscroll hook-install
```

Enable auto-publish of envelopes to git notes before push (optional):

```json
{
  "enforce": true,
  "actor_type": "agent",
  "tool": "cursor",
  "publish_notes": true
}
```

Save as `.git/matrixscroll/config.json` or export env vars per session.

## Per-session environment

Set before Cursor (or your terminal) commits:

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=cursor
export MATRIXSCROLL_TOOL_VERSION=0.42
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

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

Add [`examples/ci/protected-branch.yml`](../examples/ci/protected-branch.yml) to `.github/workflows/provenance.yml`.

See also: [`quickstart-git.md`](quickstart-git.md), [`quickstart-claude-code.md`](quickstart-claude-code.md), [`quickstart-copilot.md`](quickstart-copilot.md).
