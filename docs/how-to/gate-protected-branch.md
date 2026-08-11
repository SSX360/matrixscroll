# Gate a protected branch in GitHub Actions

This guide makes Matrix Scroll proof a merge requirement: a pull request cannot
merge unless every commit in its range carries a valid envelope.

You need a repository with envelopes already published to git notes. If you have
not done that, follow [Publish envelopes to git notes](publish-git-notes.md)
first.

## 1. Add the verification workflow

Create `.github/workflows/provenance.yml`:

```yaml
name: provenance

on:
  pull_request:

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          # Range verification needs the full history, not a shallow clone.
          fetch-depth: 0

      - uses: SSX360/matrixscroll/.github/actions/verify@action-v1
        with:
          head-ref: ${{ github.event.pull_request.head.sha }}
          base-ref: ${{ github.event.pull_request.base.sha }}
          source: notes
          matrixscroll-version: "0.7.0"
          require-mode: emulated
```

`fetch-depth: 0` is not optional. The default shallow checkout does not contain
the base commit, and range verification fails with a confusing history error
rather than a provenance error.

## 2. Let the action fetch the notes ref

`actions/checkout` does not fetch `refs/notes/*`. The action does it for you. With
`source: notes` it runs
`git fetch origin refs/notes/matrixscroll:refs/notes/matrixscroll` before
verifying, because `fetch-notes` defaults to `true`. Change the ref with
`notes-ref` if you publish elsewhere.

Set `fetch-notes: false` only when an earlier step already fetched the ref, or
when you want the job to fail rather than reach the network. Then do the fetch
yourself:

```yaml
      - name: Fetch provenance notes
        run: git fetch origin "refs/notes/matrixscroll:refs/notes/matrixscroll"
```

## 3. Choose an enforcement mode

`require-mode` controls how strict the gate is.

| Value | Effect | Use when |
| --- | --- | --- |
| omitted | Any valid signature passes | Rolling out, measuring coverage |
| `emulated` | Software-signed envelopes pass | Normal enforcement |
| `hardware` | Only secure-element signatures pass | The expected SSX360 signer key is registered |

Set `require-mode: hardware` only after you register the expected SSX360 signer
key and confirm every required commit can reach the device.

## 4. Require the check on the branch

In the repository, open **Settings**, then **Branches**, then add or edit the
protection rule for your default branch. Enable **Require status checks to pass
before merging** and select the `verify` check.

Until you do this the workflow reports failures but does not block anything.

## 5. Capture a summary artifact

Auditors ask how many commits in a release were agent-authored. Emit the counts:

```yaml
        with:
          head-ref: ${{ github.event.pull_request.head.sha }}
          base-ref: ${{ github.event.pull_request.base.sha }}
          source: notes
          matrixscroll-version: "0.7.0"
          summary-output: provenance-summary.json
```

Then upload `provenance-summary.json` with `actions/upload-artifact` so the
evidence outlives the workflow run.

## Troubleshooting

**Every commit fails with a missing-envelope error.** The notes ref never
arrived, or the envelopes were never published. Confirm that `source` is `notes`
and `fetch-notes` is not `false`, then confirm the author ran
`matrixscroll envelope-publish-notes` and pushed `refs/notes/matrixscroll`.

**Verification passes locally and fails in CI.** The runner installed a
different version. Pin `matrixscroll-version` explicitly rather than relying on
the latest release.

**Merge commits fail.** Merge commits created by the GitHub web interface are
not signed by your hook, because they are not created on a developer machine.
Either use a merge strategy that preserves signed commits, or exclude merge
commits from the range.

## Related

- [Publish envelopes to git notes](publish-git-notes.md)
- [Exit codes](../reference/exit-codes.md)
