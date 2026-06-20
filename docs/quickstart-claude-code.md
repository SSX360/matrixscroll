# Agent quickstart: Claude Code

Use Matrix Scroll to sign **agent-assisted commits** from Claude Code with verifiable provenance.

## One-time setup

```bash
pip install "matrixscroll>=0.2.5"
matrixscroll hook-install
```

## Per-session environment

Export before Claude Code commits via your shell integration:

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=claude-code
export MATRIXSCROLL_TOOL_VERSION=1.0
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

Optional delegation block fields are added to the envelope when you extend
`build_commit_envelope` output or use a wrapper script that injects
`delegation.owner_id` before signing.

## Commit and verify

```bash
git commit -m "feat: agent change"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

## PR transport

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
```

## CI gate

Copy [`examples/ci/protected-branch.yml`](../examples/ci/protected-branch.yml).

See also: [`quickstart-git.md`](quickstart-git.md), [`quickstart-cursor.md`](quickstart-cursor.md).
