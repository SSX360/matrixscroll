# Show HN: MCP Trust Layer Launch Checklist

**Target window:** Late July 2026, Tuesday–Thursday, 8:00–10:00 AM ET  
**Products launching together:** #1 MCP Trust Scanner + #2 GitHub Action allowlist gate  
**HN title (draft):** Show HN: matrixscroll mcp – sign any MCP server's tool surface and detect rug-pulls offline

---

## Pre-launch (T-14 to T-3)

### Product #1 — MCP Trust Scanner

- [ ] `matrixscroll mcp scan|sign|verify` CLI shipped and documented
- [ ] MCP tools: `scan_mcp_server`, `sign_mcp_manifest`, `verify_mcp_manifest`
- [ ] CC0 schema `schemas/ssx360.mcp-manifest.v1.json` published
- [ ] Golden tests: sign/verify roundtrip, description-mutation drift
- [ ] Web demo: paste server URL or package → trust report + signed manifest snapshot
- [ ] Re-scan flow demonstrates rug-pull detection (mutated description in demo)
- [ ] README "Show HN prep" section with copy-paste quickstart

### Product #2 — GitHub Action

- [ ] `matrixscroll-verify-action` (or sibling repo) accepts signed MCP manifest path
- [ ] Unsigned manifest → fail build
- [ ] Drift vs committed baseline → fail build
- [ ] Example workflow in matrixscroll README

### Site / demo

- [ ] Working demo URL live — **no waitlist**
- [ ] Landing: matrixscroll.com or `/forge` scanner page
- [ ] Hero copy includes: "Sign the tool surface. Verify at install."
- [ ] Vercel trust page unblocked (parallel track)

### Partner pitch (do not post on HN)

- [ ] One-pager for Glama / Smithery / mcpmarket: signing layer, not rival registry

---

## Launch day (T-0)

### Timing

- [ ] Post Tue–Thu between 8:00–10:00 AM ET
- [ ] Founder available for first 4 hours of comments

### HN post

- [ ] Title matches shipped capability (manifest surface, offline verify, drift)
- [ ] Link to working demo (primary) + GitHub repo (secondary)
- [ ] No waitlist, no "coming soon" for core scanner

### First comment template

```
Hi HN — I'm [Name], building Matrix Scroll / SSX360.

The gap we kept hitting: MCP registries list servers, model providers receipt
the call, but nobody signs the *tool surface* — names, descriptions, input schemas —
and verifies it at install time. A server can rug-pull after you trust it.

This launch:
• Free CLI: fingerprint → Ed25519 sign → offline verify
• Re-scan diffs against your baseline manifest
• GitHub Action fails CI on unsigned or drifted manifests
• CC0 spec: ssx360.mcp-manifest.v1

Commit provenance is our core wedge ("they receipt the model call; we receipt
the merge"). MCP manifest signing extends the same offline verify model to
what tools your agent can invoke.

Try it: [demo URL]
Repo: https://github.com/SSX360/matrixscroll

Happy to answer questions on canonical JSON hashing, how this differs from
runtime tool-call signing (Signet), and the SEP-1766 pivot plan if official
MCP signing ships.
```

**Do NOT** mention Postmark misattribution or unrelated founder lore.

---

## Post-launch (T+1 to T+7)

- [ ] Respond to every HN comment within 24h
- [ ] File issues from feedback into `feat/mcp-trust-*` milestones
- [ ] Design-partner pilot funnel unchanged ($7.5k, 3 slots)
- [ ] Gate #4 firewall, #5 console, #7 hosted drift monitoring behind first pilot close

---

## Success signals

| Signal | Target |
| --- | --- |
| HN front page | ≥2 hours |
| Demo completions | ≥50 in 48h |
| GitHub stars (matrixscroll) | +200 in week 1 |
| Action installs | ≥10 repos in week 1 |
| Pilot inquiries | ≥3 qualified |

---

## Risk / pivot triggers

| Trigger | Response |
| --- | --- |
| SEP-1766 official signing ships pre-launch | Lead with audit ledger + compliance; manifest as table stakes |
| "Just use Signet" comments | Clarify manifest surface vs runtime invocation |
| Registry partners cold | Ship scanner anyway; partner doc is async |

---

## Related docs

- Internal decision memo: `digital-rain-internal/docs/strategy/MCP-TRUST-LAYER-DECISION-MEMO-2026-07-03.md`
- Buyer-safe summary: `digital-rain/docs/operations/MCP-TRUST-LAYER-SUMMARY.md`
