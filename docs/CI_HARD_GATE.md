# CI hard gate — Scroll Gate Phase C

Enable required provenance on `SSX360/matrixscroll` after contributors can publish git notes.

## 1. Repository variable

```bash
gh variable set ENFORCE_PROVENANCE --body true --repo SSX360/matrixscroll
```

When set, [`verify-manifest.yml`](.github/workflows/verify-manifest.yml) **fails** PRs missing `refs/notes/matrixscroll` envelopes.

## 2. Branch protection

In GitHub → Settings → Branches → `main`:

- Require status check: **Verify Matrix Scroll manifest**
- Require branches up to date before merging

```bash
gh api repos/SSX360/matrixscroll/branches/main/protection \
  --method PUT \
  -f required_status_checks[strict]=true \
  -f required_status_checks[checks][][context]='Verify Matrix Scroll manifest' \
  -f enforce_admins=false \
  -f required_pull_request_reviews[required_approving_review_count]=0
```

Adjust review count to match your team policy.

## 3. Contributor flow

Every PR must:

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
matrixscroll envelope-verify-range --base origin/main --head HEAD --source notes
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Rollback

```bash
gh variable set ENFORCE_PROVENANCE --body false --repo SSX360/matrixscroll
```

Soft gate resumes (warning only in Step Summary).
