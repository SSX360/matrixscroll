# Governed Git commits and universal action envelopes

Phase 1 gives you a thin wrapper plus hooks. Git stays the object store and the
commit format is unchanged.

## Module location

- `matrixscroll/scroll/` holds the Phase 1 `scroll commit` wrapper
- `matrixscroll/provenance/` holds the universal action envelope builders

## Quick start

```bash
pip install "matrixscroll==0.6.3"
matrixscroll hook-install
matrixscroll scroll commit -m "feat: governed commit"
```

## Universal actions

```bash
matrixscroll sign-action --type ci_step \
  --payload ./ci-step.json \
  --output ./ci-step.signed.json \
  --actor-type ci
```

Action types: `git_commit`, `ci_step`, `iac_change`, `db_migration`, `api_call`,
`contract_deploy`.

Schema: [`schemas/action-envelope.v1.json`](../../schemas/action-envelope.v1.json)
