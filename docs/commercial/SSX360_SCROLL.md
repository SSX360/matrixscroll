# SSX360 Scroll — Provenance-native Git governance

**Status:** Phase 1 thin wrapper + hooks. **Not** a Git replacement.

See also the platform copy in [digital-rain/docs/commercial/SSX360_SCROLL.md](https://github.com/SSX360/digital-rain/blob/main/docs/commercial/SSX360_SCROLL.md).

## Module location

- `matrixscroll/scroll/` — Phase 1 `scroll commit` wrapper
- `matrixscroll/provenance/` — universal action envelope builders

## Quick start

```bash
pip install "matrixscroll==0.5.1"
matrixscroll hook-install
matrixscroll scroll commit -m "feat: governed commit"
```

## Universal actions (Layer 2)

```bash
matrixscroll sign-action --type ci_step \
  --payload ./ci-step.json \
  --output ./ci-step.signed.json \
  --actor-type ci
```

Action types: `git_commit`, `ci_step`, `iac_change`, `db_migration`, `api_call`, `contract_deploy`.

Schema: [`schemas/action-envelope.v1.json`](../schemas/action-envelope.v1.json)
