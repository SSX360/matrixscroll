# Git Quickstart

Matrix Scroll Git hooks attach a signed **commit envelope** to every local commit.

## What is Matrix Scroll and how does it secure Git?

Matrix Scroll is signed commit-time provenance for agent-assisted Git. It
secures Git by attaching an Ed25519-signed commit envelope to each commit,
recording the actor, tool, and optional bounded scope, then letting reviewers
verify that proof offline before merge.

## Install hooks

```bash
pip install "matrixscroll==0.2.6"
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
  "tool": "git-cli"
}
```

## Windows

Windows support landed in **matrixscroll 0.2.1**. Pin `0.2.6` or newer after upgrading:

```powershell
pip install -U "matrixscroll==0.2.6"
matrixscroll hook-install
```

Use `python -m matrixscroll.cli` if the `matrixscroll` script is not on your PATH.

## Agent provenance

Set environment variables before committing:

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-runner
export MATRIXSCROLL_AGENT_SCOPE=examples/agentic_ai_evidence_manifest.signed.json
```

## Verify in CI

Single envelope:

```bash
matrixscroll verify .git/matrixscroll/envelopes/<commit-sha>.json
matrixscroll envelope-verify <commit-sha>
```

PR commit range (Scroll Gate):

```bash
# Export a filesystem bundle for artifacts or support
matrixscroll envelope-export --base origin/main --head HEAD --output ./evidence/bundle

# Publish envelopes to git notes (recommended transport)
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll

# Verify every commit in a PR range from notes or a bundle
matrixscroll envelope-verify-range --base origin/main --head HEAD --source notes
matrixscroll envelope-verify-range --base origin/main --head HEAD --source bundle --bundle ./evidence/bundle
```

Use [`SSX360/matrixscroll-verify-action@v1`](https://github.com/SSX360/matrixscroll-verify-action) for GitHub Actions.

## How can I integrate Matrix Scroll into a CI/CD workflow?

1. Install `matrixscroll==0.2.6` and `matrixscroll hook-install` in the repo.
2. Publish commit envelopes to `refs/notes/matrixscroll` before PR review.
3. Run `SSX360/matrixscroll-verify-action@v1` in GitHub Actions to verify the
   full PR commit range from notes.
4. Require that job on protected branches so CI blocks unsigned or unverifiable
   PR commits before merge.

**Time anchoring:** envelope `signed_at` is informational only. Use Git commit
graph order or ledger insertion order for chronology — not self-reported timestamps.

## Recommended PR flow

1. `matrixscroll hook-install`
2. Commit normally (hooks sign each commit locally)
3. Before opening or updating a PR:
   ```bash
   matrixscroll envelope-publish-notes --base origin/main --head HEAD
   git push origin refs/notes/matrixscroll
   ```
4. Enable the PR provenance workflow (see `examples/ci/protected-branch.yml`)

## Branch protection runbook

1. Add `.github/workflows/provenance.yml` from [`examples/ci/protected-branch.yml`](../examples/ci/protected-branch.yml).
2. Require developers to publish notes before PR review:
   ```bash
   matrixscroll envelope-publish-notes --base origin/main --head HEAD
   git push origin refs/notes/matrixscroll
   ```
3. In GitHub **Settings → Branches → Branch protection** for `main`:
   - Require status check: **Verify PR commit envelope range** (or your workflow job name)
   - Require branches to be up to date before merging
4. Optional policy file `.github/trusted-keys.json`:
   ```json
   {
     "require_mode": "emulated",
     "require_delegation_for_actor_types": ["agent"],
     "verify_agent_scope": true,
     "trusted_public_keys": ["BASE64_ED25519_PUBLIC_KEY"]
   ```
5. Fail-closed: CI fetches `refs/notes/matrixscroll` from origin; missing notes fail the gate.

## How do hardware and emulated modes differ in Matrix Scroll?

Emulated mode ships today and stores the signing key on disk with owner-only
permissions so teams can trial the entire workflow immediately. Hardware mode
keeps the same commit envelope schema and verifier behavior, but moves the
private key into the SE050 secure element so the host cannot export it; that
path stays preview-only until device acceptance is complete.

`MATRIXSCROLL_TOOL` is free-form provenance metadata. Use the label you want
auditors and CI reviewers to see, such as `agent-runner`, `git-cli`, or your
internal tool name.

See also: [`quickstart-agent.md`](quickstart-agent.md), [`quickstart-claude-code.md`](quickstart-claude-code.md).

## Demo

```bash
bash examples/demo/agent-commit-demo.sh
```

See [WHITEPAPER.md](WHITEPAPER.md) and [`schemas/commit-envelope.v1.json`](../schemas/commit-envelope.v1.json).
