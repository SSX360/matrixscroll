# Show HN: MCP Trust Layer Launch Checklist

**North star:** Three ways to pay us, two Show HNs, one free scanner that makes unsigned MCP look reckless — and by September 30 either $20k+ has cleared Stripe or we stop guessing and let the March kill bar do its job early.

**Target window:** Late July 2026, Tuesday–Thursday, 8:00–10:00 AM ET  
**Products launching together:** #1 MCP Trust Scanner + #2 GitHub Action allowlist gate  
**HN title (FINAL):** Show HN: matrixscroll mcp – sign any MCP server's tool surface and detect rug-pulls offline

Title checked against shipped capability: `mcp scan --connect stdio|sse` fingerprints live
servers, `mcp sign` produces Ed25519 baselines, `mcp verify --baseline` catches drift offline
with exit code 2. All three verbs shipped and tested (see `tests/test_mcp_trust.py`).

**Revenue strategy:** SSX360 v4 — see `digital-rain-internal/docs/strategy/SSX360-REVENUE-v4-2026-07-03.md`

**Status 2026-07-03:** Products #1 and #2 shipped — `matrixscroll==0.6.0` on PyPI,
manifest gate reusable workflow in `matrixscroll-verify-action`. Asciinema recording done
2026-07-04 (see Demo GIF section). Remaining items are human-only: claim the asciinema
upload, DNS / demo URL go-live, and HN post timing.

---

## Release timeline (v4 — week anchors)

| Week | Asset | Notes |
| --- | --- | --- |
| **Wk 3** | Show HN `/forge` | Primary HN post — working demo, no waitlist |
| **Wk 5** | MCP Trust Scanner | CLI `scan\|sign\|verify` + GitHub Action ship with golden tests |
| **Wk 8** | WEB_WIZARD traces | Public agent-run provenance demos feeding Scanner narrative |

Parallel (not week-gated): FS AI RMF checklist, `ssx360.mcp-manifest.v1` CC0 spec.

Entice surfaces must CTA to Pilot (`$7.5k`), Snapshot (`$5k`), or Team (`$199/mo`) — never displace RJ sales calendar.

---

## Pre-launch (T-14 to T-3)

### Product #1 — MCP Trust Scanner

- [x] `matrixscroll mcp scan|sign|verify` CLI shipped and documented
- [x] `--connect stdio|sse` live scan of real MCP servers (MCP SDK client)
- [x] `--pretty` colored terminal output: scan table + ▲ DRIFT DETECTED verdict block
- [x] MCP tools: `scan_mcp_server`, `sign_mcp_manifest`, `verify_mcp_manifest`
- [x] CC0 schema `schemas/ssx360.mcp-manifest.v1.json` published
- [x] Golden tests: sign/verify roundtrip, description-mutation drift, exact-diff renderer (16 tests)
- [x] Golden artifact: matrixscroll's own MCP server scanned live and signed — `examples/mcp/matrixscroll-mcp.signed.json` (12 tools)
- [x] Scripted rug-pull demo: `examples/demo/mcp-rugpull-demo.sh` (asciinema-ready)
- [x] Web demo: paste tools JSON → client-side fingerprint + drift diff at matrixscroll.com/scan
- [x] Re-scan flow demonstrates rug-pull detection (mutated description in demo)
- [x] README "catch a rug-pull in 60 seconds" quickstart (install → scan → sign → mutate → catch)
- [x] PR #22 merged to main (fed4280); `matrixscroll==0.6.0` released on PyPI 2026-07-03 with the `mcp` subcommand

### Product #2 — GitHub Action

- [x] `matrixscroll-verify-action` accepts signed MCP manifest path — reusable workflow `.github/workflows/mcp-manifest-gate.yml` (`workflow_call`)
- [x] Unsigned manifest → fail build (missing file exit 1, bad signature exit 2)
- [x] Drift vs committed baseline → fail build (exit 2 with exact diff)
- [x] Example workflow in matrixscroll README (MCP Trust Scanner section)

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

### First comment (FINAL)

**Post immediately after submitting the main link** — do not wait for the thread to
gain traction; the first comment anchors the discussion.

```
Hi HN,

We are a tiny team and this is week one for Matrixscroll. We built this after realizing that while MCP is amazing for agent tooling, the discovery layer has a massive blind spot: there's no cryptographic defense against tool descriptions drifting or mutating after you initially approve them.

We wanted a free, offline, and verifiable way to ensure agents only execute against the exact tool surfaces we reviewed. Keys never leave your machine.

Here is a quick asciinema recording of the verification failing loudly on a drifted tool: https://asciinema.org/a/rbCRkIcZnjNWmqZF
```

### Demo GIF / asciinema — DONE (2026-07-04)

- Recording: <https://asciinema.org/a/rbCRkIcZnjNWmqZF> (100×30, ~37s with human
  pacing — typed prompts, narration beats, and a ~4s hold on the red
  `▲ DRIFT DETECTED` block at the end; that frame is the thumbnail)
- Cast artifact committed: `examples/demo/mcp-rugpull-demo.cast`
- GIF (agg 1.9.0) committed and embedded in README: `examples/demo/mcp-rugpull-demo.gif`
- Anonymous uploads expire after 7 days — claim it to the account via
  <https://asciinema.org/connect/b4dff431-4dff-4e33-9901-30c95ba1d6f4> before launch.
- Optional second take: live `--connect stdio` scan of matrixscroll's own MCP
  server (12 tools) to show it works on real servers, not toy JSON.

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

- Revenue strategy v4: `digital-rain-internal/docs/strategy/SSX360-REVENUE-v4-2026-07-03.md`
- Internal decision memo: `digital-rain-internal/docs/strategy/MCP-TRUST-LAYER-DECISION-MEMO-2026-07-03.md`
- Buyer-safe summary: `digital-rain/docs/operations/MCP-TRUST-LAYER-SUMMARY.md`
- Buyer-safe revenue summary: `digital-rain/docs/operations/SSX360-REVENUE-v4-SUMMARY.md`
