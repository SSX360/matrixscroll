# CI Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provide a zero-config GitHub Action that runs `matrixscroll verify` with CI-friendly exit codes.

**Architecture:** Composite action installs matrixscroll from PyPI, runs verify on one or more manifest paths, optionally applies policy flags.

**Tech Stack:** GitHub Actions, Python 3.10+, matrixscroll CLI

---

## Exit code contract

| Code | Meaning | CI interpretation |
|------|---------|-------------------|
| 0 | Valid signature | Pass check |
| 1 | Usage/config error | Fail workflow (misconfiguration) |
| 2 | Verification failed | Fail workflow (tampered/invalid) |

The action MUST propagate CLI exit codes unchanged (`set -e` in bash step).

## Action inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `manifest` | yes | — | Path to signed manifest JSON |
| `python-version` | no | `3.12` | Python for pip install |
| `matrixscroll-version` | no | `latest` | Pin e.g. `0.1.1` for reproducibility |
| `require-mode` | no | `` | Pass through to policy verify (v0.2.1) |
| `trusted-keys` | no | `` | Path to trusted keys JSON (v0.2.1) |

## Action outputs

| Output | Description |
|--------|-------------|
| `ok` | `true` or `false` |
| `device_id` | Signer device id from manifest |
| `mode` | Provider mode (`emulated`, `hardware`, `yubikey`) |

## Files

| File | Purpose |
|------|---------|
| `matrixscroll-action/action.yml` | Composite action definition |
| `matrixscroll-action/README.md` | Usage docs |
| `matrixscroll/.github/workflows/verify-manifest.yml` | Dogfood workflow |
| `matrixscroll/examples/ci/protected-branch.yml` | Copy-paste template |

## Protected branch pattern

```yaml
name: provenance
on:
  pull_request:
    branches: [main]
jobs:
  verify-release-manifest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: SSX360/matrixscroll-verify-action@v1
        with:
          manifest: examples/release-manifest.signed.json
```

## Release verification pattern

1. Build job signs release manifest, uploads artifact
2. Verify job downloads artifact, runs action
3. Deploy job requires verify job success

## Task checklist

- [x] Write action.yml composite action
- [x] Add dogfood workflow in matrixscroll repo
- [x] Add protected-branch example
- [ ] Publish action repo and tag v1 (manual release step)
- [ ] Add signed release-manifest to examples once v0.2.0 ships

## Verification

```bash
cd matrixscroll
pip install -e ".[dev]"
pytest tests/test_cli.py -v
matrixscroll verify examples/agentic_ai_evidence_manifest.json  # expect exit 2 unsigned
```
