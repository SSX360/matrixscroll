# Git Quickstart

Matrix Scroll Git hooks attach a signed **commit envelope** to every local commit.

## Install hooks

```bash
pip install matrixscroll
matrixscroll hook-install
matrixscroll hook-status
```

Hooks ship inside the Python wheel (`matrixscroll/hooks/`). No separate clone path
is required for pip-installed users.

## What happens on commit

1. **post-commit** reads the new commit SHA and builds a commit envelope from `git show`
2. The envelope is signed with your active Matrix Scroll identity
3. The signed envelope is stored at `.git/matrixscroll/envelopes/<sha>.json`

**pre-push** verifies envelopes only for commits being pushed (not every envelope
ever stored locally).

By default hooks run in **warn mode** (signing failures do not block commits).
Enable enforce mode in `.git/matrixscroll/config.json`:

```json
{
  "enforce": true,
  "actor_type": "human",
  "tool": "cursor"
}
```

## Windows

Commit-envelope signing requires **matrixscroll 0.2.1+** (fixes Git `cat-file` parsing on Windows). After upgrading:

```powershell
pip install -U "matrixscroll>=0.2.1"
matrixscroll hook-install
```

Use `python -m matrixscroll.cli` if the `matrixscroll` script is not on your PATH.

## Agent provenance

Set environment variables before committing:

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=cursor
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

## Verify in CI

```bash
matrixscroll verify .git/matrixscroll/envelopes/<commit-sha>.json
matrixscroll envelope-verify <commit-sha>
```

Or use [`SSX360/matrixscroll-verify-action@v1`](https://github.com/SSX360/matrixscroll-verify-action).

## Demo

```bash
bash examples/demo/agent-commit-demo.sh
```

See [WHITEPAPER.md](WHITEPAPER.md) and [`schemas/commit-envelope.v1.json`](../schemas/commit-envelope.v1.json).
