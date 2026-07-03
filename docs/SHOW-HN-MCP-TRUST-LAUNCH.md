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
manifest gate reusable workflow in `matrixscroll-verify-action`. Remaining items are
human-only: asciinema recording, DNS / demo URL go-live, and HN post timing.

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

### First comment (FINAL draft)

```
Hi HN — I'm Ryan, building Matrix Scroll / SSX360.

The gap we kept hitting: MCP registries list servers, model providers receipt
the call, but nobody signs the *tool surface* — names, descriptions, input
schemas — and verifies it at install time. A server you trusted yesterday can
quietly ship different tool descriptions today, and your agent will follow
them. The ecosystem has already seen this class of attack: an npm MCP package
shipped an update that silently added exfiltration behavior after users had
installed it, and MCP tooling itself has had real CVEs this cycle
(CVE-2025-6514 in mcp-remote, CVE-2025-49596 in MCP Inspector). Install-time
trust with no re-verification is the standing assumption, and it's wrong.

What this launch does:
• Free CLI: fingerprint a server's tool surface → Ed25519 sign → verify offline
• Live scan: `matrixscroll mcp scan --connect stdio --server-command "npx -y <server>"`
• Re-scan diffs against your signed baseline — a mutated description or input
  schema exits 2 with an exact diff (rug-pull detection)
• GitHub Action fails CI on unsigned or drifted manifests
• CC0 spec: ssx360.mcp-manifest.v1 — no lock-in, no cloud, no signup

Commit provenance is our core wedge ("they receipt the model call; we receipt
the merge"). MCP manifest signing extends the same offline verify model to
what tools your agent can invoke.

Try it in the browser (nothing uploaded): https://matrixscroll.com/scan
Repo: https://github.com/SSX360/matrixscroll

Happy to answer questions on canonical JSON hashing, how this differs from
runtime tool-call signing (Signet), and the SEP-1766 pivot plan if official
MCP signing ships.
```

**Do NOT** name Postmark/ActiveCampaign as the attacker — the 2025 incident was an
*unofficial impersonator package*, not the vendor. Say "an npm MCP package" and let
commenters supply links. No unrelated founder lore.

### Demo GIF / asciinema plan

1. Record on Linux/macOS terminal, 80×24, dark theme, JetBrains Mono:
   `asciinema rec -c ./examples/demo/mcp-rugpull-demo.sh mcp-rugpull.cast`
2. The script self-paces (0.6s beats) and ends on the red `▲ DRIFT DETECTED` block —
   that frame is the thumbnail.
3. Convert for README/HN: `agg mcp-rugpull.cast mcp-rugpull.gif --theme monokai`
   (or svg-term for crisp text). Keep under 15s loop.
4. Embed GIF at top of README section + link the cast on asciinema.org.
5. Optional second take: live `--connect stdio` scan of matrixscroll's own MCP
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
