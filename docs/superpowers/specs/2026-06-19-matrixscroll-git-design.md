# matrixscroll-git — Design Spec

**Date:** 2026-06-19  
**Status:** Approved for v0.2.0 implementation  
**Scope:** Local Git hooks, commit-envelope manifest, CLI extensions, CI verification contract

## 1. Goal

Attach a Matrix Scroll cryptographic provenance envelope to every Git commit made
by a human or AI agent. Verify envelopes offline in CI without trusting the
host IDE or agent runtime.

This is the Day-1 beachhead: Git commits are standardized, high-consequence, and
already support signing workflows.

## 2. Non-goals (v0.2.0)

- Replacing GPG/SSH commit signing (Matrix Scroll is additive metadata)
- Remote attestation (L3) or hardware touch gating (L2 transport)
- Server-side registry or enrollment APIs

## 3. Commit envelope schema

Schema id: `matrixscroll.commit_envelope.v1`

See [`schemas/commit-envelope.v1.json`](../../schemas/commit-envelope.v1.json) and
[`examples/commit-envelope.json`](../../examples/commit-envelope.json).

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Constant `matrixscroll.commit_envelope.v1` |
| `commit` | object | Git commit identity material |
| `commit.tree` | string | Full tree SHA-1 hex |
| `commit.parents` | string[] | Parent commit SHAs (empty for root) |
| `commit.author` | object | `{name, email, date}` from commit object |
| `commit.committer` | object | `{name, email, date}` from commit object |
| `commit.message` | string | Raw commit message bytes as UTF-8 string |
| `provenance` | object | Who/what produced the commit |
| `provenance.actor_type` | string | `human` \| `agent` \| `ci` |
| `provenance.tool` | string | e.g. `agent-cli`, `ci-runner`, `git-cli` |
| `provenance.tool_version` | string | Optional semver or build id |
| `provenance.agent_scope` | string | Optional reference to signed agent evidence manifest |
| `repository` | object | `{name, remote_url}` best-effort from git config |
| `signature` | object | Matrix Scroll signature block (see SPEC.md §5) |

### Signing input

The envelope is signed with `sign_manifest()` using canonical JSON rules from
SPEC.md §4. The top-level `signature` block is excluded from the signing input.

### Commit binding

The envelope MUST be bound to the commit it describes:

```
commit_id = SHA-1( commit_object_bytes )
```

The hook computes `commit_id` from the staged tree + message at commit time
(before the commit object exists) using:

```
tree = git write-tree
commit_body = git commit-tree $tree -p $parents -m "$message"
commit_id = SHA-1(commit_body)  # computed, not yet committed
```

The envelope stores `commit.expected_id` (the computed SHA). After commit,
`commit.actual_id` is written to `.git/matrixscroll/envelopes/<sha>.json`.

## 4. Storage layout

```
.git/matrixscroll/
  config.json          # hook config (require_envelope, actor defaults)
  envelopes/
    <40-char-sha>.json # one signed envelope per commit
```

Envelopes are **local provenance artifacts**. They may be exported to CI as
build artifacts or pushed to a release evidence bucket; they are not committed
to the source tree by default.

## 5. CLI commands

Extend the `matrixscroll` CLI:

| Command | Description | Exit codes |
|---------|-------------|------------|
| `matrixscroll hook install` | Install pre-commit + pre-push hooks | 0 ok, 1 error |
| `matrixscroll hook uninstall` | Remove hooks | 0 ok |
| `matrixscroll hook status` | JSON: installed, config, envelope count | 0 |
| `matrixscroll envelope build` | Build envelope for staged commit (stdin/flags) | 0 ok, 2 fail |
| `matrixscroll envelope verify <sha\|file>` | Verify envelope for commit | 0 pass, 2 fail |
| `matrixscroll verify <file>` | *(existing)* verify any signed manifest | 0 pass, 2 fail |

Environment variables (inherit from SDK):

- `MATRIXSCROLL_MODE` — `emulated` (default) or `hardware`
- `MATRIXSCROLL_HOME` — key store override
- `MATRIXSCROLL_ACTOR_TYPE` — default `human` | `agent` | `ci`
- `MATRIXSCROLL_TOOL` — default tool name for provenance block

## 6. Hook behavior

### pre-commit

1. Read staged tree via `git write-tree`
2. Build commit preview (parents from `HEAD`, message from `-F` or `-m`)
3. Construct commit envelope manifest
4. Sign with active provider via `sign_manifest()`
5. Write envelope to `.git/matrixscroll/envelopes/<expected_id>.json`
6. Exit 0 (never block commit on signing failure in v0.2.0 **warn mode**;
   **enforce mode** exits 2)

Config flag `enforce: true` blocks commits when signing fails.

### pre-push

1. For each commit being pushed not already on remote:
   - Load envelope from `.git/matrixscroll/envelopes/<sha>.json`
   - Run `verify_manifest()`
2. Exit 2 if any envelope missing or invalid (when `enforce: true`)

### prepare-commit-msg (optional, phase 2)

Append `Matrix-Scroll-Envelope: <sha>` trailer to commit message for
human-visible provenance pointer.

## 7. CI verification contract

CI MUST NOT parse free-text hook output. Use exit codes:

| Exit code | Meaning |
|-----------|---------|
| 0 | Signature valid |
| 1 | Usage / configuration error |
| 2 | Verification failed (tampered, missing, wrong schema) |

### GitHub Actions pattern

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install matrixscroll
- run: matrixscroll verify evidence/commit-envelope.json
```

For protected branches, CI receives exported envelopes as artifacts from a
prior build job or fetches them from object storage.

Policy extensions (v0.2.1):

```bash
matrixscroll verify release.json \
  --require-mode hardware \
  --trusted-keys trusted-keys.json
```

## 8. Error handling

| Failure | Hook (warn) | Hook (enforce) | CI |
|---------|-------------|----------------|-----|
| Provider unavailable | warn, continue | exit 2 | exit 2 |
| Corrupt envelope | warn | exit 2 | exit 2 |
| Tampered manifest | warn | exit 2 | exit 2 |
| Missing envelope | warn | exit 2 | exit 2 |
| Wrong schema version | warn | exit 2 | exit 2 |

## 9. Security considerations

- Envelopes prove **who signed the provenance record**, not that Git's native
  signature is valid. Pair with branch protection + required status checks.
- Emulated mode (L1) is suitable for dev; release branches SHOULD require
  `mode: hardware` once L2 ships.
- Never store private keys in envelope files; only public key + signature.

## 10. Test plan

- Unit: envelope schema validation, commit_id computation
- Integration: `hook install` → commit → envelope exists → `verify` passes
- Tamper: modify envelope field → `verify` exits 2
- Vectors: add `vectors/valid_commit_envelope.json` in v0.2.0

## 11. Implementation files

| File | Responsibility |
|------|----------------|
| `schemas/commit-envelope.v1.json` | JSON Schema |
| `examples/commit-envelope.json` | Reference example |
| `tools/git/install.py` | Hook installer |
| `tools/git/hooks/pre-commit` | Pre-commit hook script |
| `tools/git/hooks/pre-push` | Pre-push hook script |
| `matrixscroll/git.py` | Python hook/envelope API (v0.2.0) |
| `tests/test_git_envelope.py` | Tests |

## 12. Rollout phases

1. **v0.2.0-alpha:** warn-mode hooks, emulated signing, local envelopes
2. **v0.2.0:** enforce-mode, GitHub Action, commit-envelope vectors
3. **v0.2.1:** policy flags (`--require-mode`, trusted keys)
4. **v0.3.0:** YubiKey bridge provider, hardware mode for release branches
