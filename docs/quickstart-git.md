# Git Quickstart

Matrix Scroll Git hooks attach a signed **commit envelope** to every local commit.

## Install hooks

From any git repository:

```bash
pip install matrixscroll
python path/to/matrixscroll/tools/git/install.py
```

Or from a clone of this repo:

```bash
cd matrixscroll
pip install -e ".[dev]"
python tools/git/install.py
```

## What happens on commit

1. `pre-commit` builds a commit envelope from the staged tree and message
2. The envelope is signed with your active Matrix Scroll identity
3. The signed envelope is stored at `.git/matrixscroll/envelopes/<sha>.json`

By default hooks run in **warn mode** (signing failures do not block commits).
Enable enforce mode in `.git/matrixscroll/config.json`:

```json
{
  "enforce": true,
  "actor_type": "human",
  "tool": "cursor"
}
```

## Agent provenance

Set environment variables before committing:

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=cursor
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.json
```

## Verify in CI

```bash
matrixscroll verify .git/matrixscroll/envelopes/<commit-sha>.json
```

See [docs/superpowers/specs/2026-06-19-matrixscroll-git-design.md](../superpowers/specs/2026-06-19-matrixscroll-git-design.md).
