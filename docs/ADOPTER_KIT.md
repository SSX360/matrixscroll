# Adopter Kit

This page is for OSS maintainers, platform teams, and design-partner engineers
who want to trial Matrix Scroll without changing their core workflow.

## Best first-fit teams

- OSS repos with active PR review and at least one protected branch
- platform or DevSecOps teams evaluating agent-assisted coding controls
- teams that already use GitHub Actions and can add one verification job

## 15-minute pilot

1. Install `matrixscroll==0.4.1` in one repo.
2. Run `matrixscroll hook-install`.
3. Make one agent-assisted commit and verify it locally.
4. Publish notes with `matrixscroll envelope-publish-notes`.
5. Add `SSX360/matrixscroll-verify-action@v1` to PR CI.

## Suggested evaluation workflow

```yaml
name: Verify PR commit envelopes

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  verify-provenance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: SSX360/matrixscroll-verify-action@v1
        with:
          head-ref: ${{ github.event.pull_request.head.sha }}
          base-ref: ${{ github.event.pull_request.base.sha }}
          source: notes
          matrixscroll-version: "0.4.1"
          require-mode: emulated
```

## What to collect during the pilot

- one passing local `envelope-verify`
- one passing PR range check
- one example of a failed verify after tampering or missing notes
- reviewer feedback on whether actor / tool attribution is useful

## Success criteria

- the team can explain the difference between commit-time and artifact-time proof
- the GitHub Action is understandable to the repo owner
- the team can point to one real decision that the envelope data improved

## What not to assume

- L1 emulated mode is not a hardware root of trust
- Matrix Scroll does not replace IAM or sandboxing
- Matrix Scroll does not replace release-signing or artifact attestations

## Clean-machine proof status

Recorded on `2026-06-21` against the pinned public flow:
`pip install "matrixscroll==0.4.1"` -> `matrixscroll hook-install` ->
`matrixscroll hook-status` -> first agent-assisted commit ->
`matrixscroll envelope-verify`.

Hosted source of truth: GitHub Actions run
`27904509800` on `codex/trust-layer-rollout`.

| Platform | Result | Notes |
| --- | --- | --- |
| Windows | PASS | GitHub-hosted smoke completed with `1.0s` to first verified commit. Local temp-venv proof also passed in `8.7s`. |
| Ubuntu | PASS | GitHub-hosted smoke completed with `0.4s` to first verified commit. |
| macOS | PASS | GitHub-hosted smoke completed with `0.3s` to first verified commit. |

Local environment note: the workspace WSL image is still missing `python3-pip`
and `python3-venv`, so local Ubuntu reproduction remains under-provisioned even
though launch evidence is now covered by the hosted workflow.

## Public follow-through

If a pilot works, publish one of these:

- a short repo note describing the evaluation
- a screenshot of the passing GitHub Action
- a testimonial about why commit-time attribution mattered
