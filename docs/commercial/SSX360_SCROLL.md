# Governed Git commits and universal action envelopes

Matrix Scroll adds signed provenance records around normal Git operations. Git
remains the object store and the commit format is unchanged.

**Shipping now:** the `scroll commit` wrapper, Git hooks, and universal action
envelopes. **Not:** a Git replacement or a change to Git's object format.

## Module location

- `matrixscroll/scroll/` contains the `scroll commit` wrapper.
- `matrixscroll/provenance/` contains the universal action-envelope builders.

## Quick start

```bash
pip install "matrixscroll==0.7.0"
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
and `contract_deploy`.

Schema: [`schemas/action-envelope.v1.json`](../../schemas/action-envelope.v1.json)
