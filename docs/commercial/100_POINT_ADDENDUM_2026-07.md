# 100-point scorecard addendum (2026-07-02)

Cross-repo QA verification against live surfaces (PyPI, GitHub API, raw README).

## Version truth (verified)

| Surface | Version | Status |
|---------|---------|--------|
| PyPI `matrixscroll` | 0.5.1 | Live |
| GitHub Release `SSX360/matrixscroll` | v0.5.1 | Live |
| SDK `__init__.py` / pyproject | 0.5.1 | Local |
| verify-action default pin | 0.5.1 | Local + CI |
| Site / portal constants | 0.5.1 | Sibling repos |

## Spear / handle doctrine

- **Spear (protocol):** matrixscroll.com — verify, compare, docs, try
- **Handle (control plane):** ssx360.com — signup, download, billing, Scroll Gate hosted

Public READMEs and proof links in SDK + verify-action must use matrixscroll.com for verifier surfaces.

## Gates extended

- `scripts/release-readiness.py` now fails if `README.md` install pins disagree with `pyproject.toml` / PyPI.
- verify-action `validate.yml` greps README for `0.5.1`, matrixscroll.com proof links, and absence of `0.2.6`.

## Blocked on maintainer

- **digital-rain-releases v1.0.4:** `release-manifest.signed.json` template + doc shipped; attaching to existing GitHub Release assets requires RJ credentials.
- **matrixscroll PR #20:** rebase/merge conflict with main — resolve before merge.

## Repo description

GitHub `SSX360/matrixscroll` description updated to honest hardware wording (SE050 in progress, not shipped).
