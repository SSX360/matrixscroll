# Agent quickstart: GitHub Copilot

Use Matrix Scroll to sign **agent-assisted commits** from GitHub Copilot (IDE or CLI) with verifiable provenance.

## One-time setup

```bash
pip install "matrixscroll>=0.2.4"
matrixscroll hook-install
```

## Per-session environment

In the terminal where you commit Copilot-assisted changes:

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=copilot
export MATRIXSCROLL_TOOL_VERSION=2026.06
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

## Commit and verify

```bash
git commit -m "feat: copilot-assisted refactor"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

## PR transport

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
```

## Policy example for agent-only repos

`.github/trusted-keys.json`:

```json
{
  "require_mode": "emulated",
  "require_delegation_for_actor_types": ["agent"],
  "verify_agent_scope": true,
  "trusted_public_keys": ["YOUR_BASE64_PUBLIC_KEY"]
}
```

Pass to CI via `--trusted-keys .github/trusted-keys.json`.

See also: [`quickstart-git.md`](quickstart-git.md), [`quickstart-cursor.md`](quickstart-cursor.md).
