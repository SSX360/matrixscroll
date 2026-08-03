# Publish envelopes to git notes

Envelopes are written locally when the post-commit hook runs. A reviewer or CI
job on another machine cannot see them until you publish them. Git notes are the
transport: they attach data to a commit without changing its hash.

!!! note "Stub"
    This page covers the common path. Bundle transport and Forgejo/GitLab
    equivalents are not yet written.

## Publish a range

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
```

The first command writes envelopes into `refs/notes/matrixscroll`. The second
pushes that ref. Notes are not pushed by `git push` alone; the refspec is
required every time.

## Fetch on another machine

```bash
git fetch origin "refs/notes/matrixscroll:refs/notes/matrixscroll"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

## Push notes automatically

Add a refspec to the remote so ordinary pushes carry notes:

```bash
git config --add remote.origin.push "refs/heads/*:refs/heads/*"
git config --add remote.origin.push "refs/notes/matrixscroll:refs/notes/matrixscroll"
```

## Resolve a notes conflict

Two people publishing notes for overlapping ranges produces a rejected push.
Merge rather than force:

```bash
git fetch origin "refs/notes/matrixscroll:refs/notes/origin-matrixscroll"
git notes --ref=matrixscroll merge -s cat_sort_uniq refs/notes/origin-matrixscroll
git push origin refs/notes/matrixscroll
```

Never force-push the notes ref. It destroys other people's evidence.

## Related

- [Gate a protected branch in GitHub Actions](gate-protected-branch.md)
