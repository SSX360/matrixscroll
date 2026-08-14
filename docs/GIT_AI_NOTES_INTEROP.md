# Git AI Notes Interop Design

## Context

Git AI / Next Element stores line-level attribution in Git Notes (`usegitai.com`). Their format is a de facto attribution candidate.

## Strategy: sign, don't fight

Matrix Scroll should **sign and attest Git AI notes**, not introduce a competing attribution format.

## Flow

```text
Agent edit → Git AI note (line attribution) → Matrix Scroll envelope signs note + commit metadata → CI verifies both
```

## Evidence value

- Git AI note: self-reported line-level attribution surviving rebase/squash
- Matrix Scroll envelope: cryptographic proof the note and commit metadata were attested together at gate time

## Deliverables

| Item | Status |
|------|--------|
| Note canonicalization rules | Design |
| `matrixscroll attest-git-ai-notes` CLI | Planned adapter |
| Scroll Gate policy: require signed note when Git AI present | Planned |

## Verification boundaries

- Line attribution remains **self-reported**; signing proves integrity of the declaration, not ground-truth authorship detection.

## References

- Git AI docs: https://usegitai.com
- Matrix Scroll compare page: commit-time declared origin
