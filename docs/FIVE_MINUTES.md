# Add Commit Provenance in 5 Minutes

Matrix Scroll is easiest to evaluate in a real repo. This guide gives OSS teams a
five-minute path from `pip install` to a verifiable commit envelope.

## What you will prove

- A local commit can carry a signed commit envelope.
- The envelope records `actor_type` and `tool`.
- Anyone can verify the envelope without trusting the IDE session.

## 1. Install the SDK

```bash
pip install "matrixscroll==0.4.1"
matrixscroll hook-install
matrixscroll hook-status
```

## 2. Mark the commit as agent-assisted

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-runner
```

PowerShell:

```powershell
$env:MATRIXSCROLL_ACTOR_TYPE = "agent"
$env:MATRIXSCROLL_TOOL = "agent-runner"
```

## 3. Make one real commit

```bash
git commit -m "feat: add Matrix Scroll pilot"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

You should see `ok: true` and the active `mode` in the verification output.

`MATRIXSCROLL_TOOL` is free-form provenance metadata. The examples here use
`agent-runner` to keep the public quickstart tool-agnostic.

## 4. Put the proof where CI can see it

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
```

## 5. Add one GitHub Action

```yaml
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

## What a good first pilot looks like

- One repo has hooks installed.
- One PR publishes notes and passes the GitHub Action.
- The team verifies at least one envelope locally and once in the browser.

## Next reads

- [Git quickstart](quickstart-git.md)
- [Adopter kit](ADOPTER_KIT.md)
- [Commit-time proof vs artifact-time proof](COMMIT_TIME_VS_ARTIFACT_TIME.md)
