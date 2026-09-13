# SSX360 Scroll (concept — Phase 2)

**Status:** Design + thin wrapper stub. **Not** a Git replacement.

SSX360 Scroll is a Git-compatible client that wraps standard Git operations
with mandatory provenance envelopes, actor attribution, and policy hooks.
Git remains the object store; Scroll adds the governance layer on top.

## Target flow

```
Developer → scroll commit → git commit (under the hood) → signed envelope
         → scroll push   → git push + envelope notes
         → SSX360 Gate   → hosted verify before deploy
```

## Phase 1 (ships today)

Use the Matrix Scroll CLI and hooks directly:

```bash
matrixscroll hook-install
git commit -m "feat: example"   # post-commit hook signs envelope
matrixscroll envelope-publish-notes --base origin/main --head HEAD
```

## Phase 2 (roadmap)

```bash
scroll commit -m "feat: example"   # wraps git commit + auto-envelope
scroll push                        # push + publish notes
scroll verify-range --base main --head HEAD
```

Implementation will live in `matrixscroll.scroll` and delegate to `matrixscroll.git`.

See [docs/commercial/SSX360_SCROLL.md](../../docs/commercial/SSX360_SCROLL.md).
