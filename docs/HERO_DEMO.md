# Hero demo script (60–90 seconds)

Record this flow once. It is the highest-value GTM asset for the quarter.

## Cast

- **Agent:** Cursor or Claude Code in a bound workspace
- **Producer:** Digital Rain or `matrixscroll` hooks / MCP `create_envelope`
- **Enforcer:** Scroll Gate (`SSX360/matrixscroll-verify-action@v1`)
- **Verifier:** [matrixscroll.com/verify/](https://matrixscroll.com/verify/) (offline, no portal trust)

## Beat sheet

| Time | Screen | Narration hook |
|------|--------|----------------|
| 0:00 | Terminal / IDE | "An agent just committed. Who — or what — wrote it?" |
| 0:10 | `git log -1` + hook output | "Digital Rain signs an Ed25519 envelope at commit time — actor, tool, scope." |
| 0:25 | Envelope JSON (redacted keys OK) | "This is the proof object. Repo contents never left the machine." |
| 0:35 | GitHub PR + Scroll Gate check | "Scroll Gate verifies the full PR range — signed vs unsigned, trusted vs untrusted." |
| 0:50 | Browser verifier paste | "Anyone verifies offline at matrixscroll.com/verify — no SSX360 login required." |
| 1:05 | SSX360 portal flash (optional) | "Identity, billing, and audit live on the control plane — verification does not." |
| 1:15 | CTA slate | "Verify → Install → Pilot." |

## Commands (copy-paste)

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=cursor
git commit -m "feat: demo agent change"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
```

Open PR → show **Scroll Gate** check green → paste envelope into browser verifier.

## Do not say

- "Required by" / "mandated" / regulation names as requirements
- Repo intelligence / scanner as the lead story

## Do say

- "Maps to" / "produces evidence for" compliance frameworks
- "Signed before merge" / "offline-verifiable" / "Scroll Gate"
