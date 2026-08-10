# Changelog

All notable changes to the Matrix Scroll Python SDK are documented here. The
format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.3] - 2026-08-10

Repository layout and documentation. No code, CLI or wire-format changes.

### Added
- **The Matrix Scroll Verify action now lives in this repo** at
  [`.github/actions/verify`](.github/actions/verify), and the reusable MCP
  manifest gate at `.github/workflows/mcp-manifest-gate.yml`. Both were
  published from the separate `SSX360/matrixscroll-verify-action` repository,
  which is now archived. Inputs, outputs and exit codes are unchanged.

### Changed
- **Call sites move to the new reference.** Replace
  `SSX360/matrixscroll-verify-action@v1` with
  `SSX360/matrixscroll/.github/actions/verify@action-v1`, and
  `SSX360/matrixscroll-verify-action/.github/workflows/mcp-manifest-gate.yml@main`
  with `SSX360/matrixscroll/.github/workflows/mcp-manifest-gate.yml@action-v1`.
  The `action-v1` tag tracks the current action release line and is separate
  from the SDK's `v0.6.x` tags.
- The reusable MCP gate now defaults `matrixscroll_version` to `0.6.3`, matching
  the action default and the published PyPI release. It runs on `workflow_call`
  and `workflow_dispatch` only, so it does not add a job to every SDK pull
  request.

### Fixed
- **PyPI dropped every relative link in the README.** Its sanitiser removes any
  `href` it cannot resolve, so 17 documentation links arrived on the project
  page as plain text and the MCP rug-pull demo GIF arrived as its alt text,
  leaving that section without its only visual. All of them are absolute
  `github.com` and `raw.githubusercontent.com` URLs now.
- **Three README links promised a tamper demo at a page that redirects.**
  `matrixscroll.com/try` routes to `/docs/`. The demo is the browser verifier
  at `/verify/`, which carries the Tamper sample control, so the inline links
  point there. The `Try it` entry under Public proof links repeated the
  verifier line above it and is now the MCP Trust Scanner at `/scan/`.
- **`SECURITY.md` offered support for 0.2.x and 0.1.x.** A reader installing
  the published release found their version missing from the table on the page
  the PyPI sidebar links as the security policy.

## [0.6.2] - 2026-08-03

Documentation and packaging metadata only. No code, CLI or wire-format changes,
and no new dependencies.

### Fixed
- **Packaging URLs pointed at pages that had moved or gone.** `Documentation` and
  `Verifier` routed through `ssx360.com` redirects that land on
  `matrixscroll.com`, `Reference Device` pointed at a culled `/hardware` page,
  and `Compare` duplicated `Documentation`. Every link now resolves directly, and
  `Homepage` is the protocol site rather than the maintainer's.
- **The README described a hosted control plane with billing.** SSX360 is an
  independent audit practice that sells assessments, not a platform, so the
  README now says who maintains the protocol and why that separation exists. The
  links to the retired `/enterprise`, `/signup` and `/compare` pages are gone.

### Documentation
- **State the post-quantum limit where people actually read it.** The summary and
  keywords claim FIPS 204 and FIPS 205, but nothing on the PyPI page said the
  overlay is an algorithm implementation through liboqs rather than a
  CMVP-validated module, or repeated liboqs's own warning against production use.
  Honest limits now carries both.
- Summary rewritten to lead with what the protocol does rather than the hardware
  signing path, which is a bench prototype and not a product.
- Install pin `matrixscroll==0.6.2`.

## [0.6.1] - 2026-07-22

### Documentation
- **L2 Hardware prototype (2026-07-21)** — Pico 2 W / RP2350 + GMT130 ST7789
  LCD/LED bring-up locked; SE050 M1 PoC remains bench-validated (not GA).
  README compliance table, `docs/hardware-provider.md`, and roadmap updated.
  Docs-only release; install pin `matrixscroll==0.6.1`.

## [0.6.0] - 2026-07-03

MCP Trust Scanner — sign any MCP server's tool surface and detect rug-pulls offline.

### Added
- **`matrixscroll mcp scan|sign|verify`** — fingerprint an MCP server's tool
  surface (names, descriptions, input schemas), Ed25519-sign a manifest, and
  verify offline against a committed baseline (drift exits 2 with exact diff).
- **`--connect stdio|sse`** — live scan of running MCP servers via the MCP SDK
  client (`--server-command` for stdio, URL for SSE).
- **`--pretty`** — colored terminal output: scan table and `▲ DRIFT DETECTED`
  verdict block.
- **MCP tools** — `scan_mcp_server`, `sign_mcp_manifest`, `verify_mcp_manifest`
  on the matrixscroll MCP server.
- **CC0 schema** — `schemas/ssx360.mcp-manifest.v1.json` (`ssx360.mcp-manifest.v1`).
- **Golden artifact** — `examples/mcp/matrixscroll-mcp.signed.json` (matrixscroll's
  own MCP server, 12 tools, scanned live and signed).
- **Rug-pull demo** — `examples/demo/mcp-rugpull-demo.sh` (asciinema-ready).

### Documentation
- README "catch a rug-pull in 60 seconds" quickstart; install pins moved to
  `matrixscroll==0.6.0`.

## [0.5.1] - 2026-07-02

### Added
- **`ssx360` and `ssx360-ledger` console scripts** — ship on PyPI with the SDK
  (local repo had entry points since POC 2 baseline; 0.5.0 wheel omitted them).

### Documentation
- Pin public install examples and CI workflows to `matrixscroll==0.5.1`.

## [0.5.0] - 2026-07-02

Post-quantum overlay (v1.1 additive extension).

### Added
- **SPEC.md §11** — optional `pqc_signatures` array (ML-DSA FIPS 204, SLH-DSA FIPS 205).
- **`matrixscroll.pqc`** — software-only PQC overlay; Ed25519 `signature` block unchanged.
- **`matrixscroll pqc-keygen`** — generate/load PQC keys under `~/.matrixscroll/pqc/`.
- **`MATRIXSCROLL_PQC`** env — attach overlay on sign (e.g. `ml-dsa-65`); hardware mode exempt.
- **Policy `require_pqc`** — `false` (default), `emulated_only`, or `true` (hardware exempt).
- **Optional extra `[pqc]`** — `liboqs-python` backend for ML-DSA / SLH-DSA.

### Unchanged
- USB/NFC/SE050 device signing remains **Ed25519-only** (no firmware change).
- All v1 vectors and Ed25519 verification behavior.

## [0.4.2] - 2026-06-29

Crypto backend consolidation (middle path).

### Changed
- **`matrixscroll.crypto_backend`** — all Ed25519 sign/verify/keygen and
  security-relevant SHA-256 hashing route through the `cryptography` package
  (native wheels; no user Rust toolchain).
- **Dependency** — `cryptography>=42.0` is now required (was `>=41.0`).
- **Docs** — `docs/CRYPTO_BACKEND.md`, README security note, SECURITY_PROPERTIES
  backend section.

### Removed
- Scattered direct `cryptography` / `hashlib` calls in providers and gate paths
  in favor of the centralized backend module (Git SHA-1 wire hashing unchanged).

## [0.4.1] - 2026-06-29

Universal provenance SDK expansion and SSX360 Scroll Phase 1 wrapper.

### Added
- **`matrixscroll.provenance`** — action envelope builders for `ci_step`, `iac_change`,
  `db_migration`, `api_call`, and `contract_deploy` (`schemas/action-envelope.v1.json`).
- **`matrixscroll sign-action`** CLI — sign typed action envelopes with Ed25519.
- **`matrixscroll scroll commit`** — thin Git wrapper (Phase 1; not a Git replacement).
- **MCP** — `sign_action` validates typed payloads; new `matrixscroll://schema/action-envelope.v1` resource.
- **Docs** — SSX360 Scroll brief, Scroll Gate v2 SLSA L1–2 honest mapping.

## [0.3.0] - 2026-06-28

Digital Rain removal and provenance-only SDK surface.

### Removed
- **Workspace intelligence modules** — deleted unused Digital Rain-era helpers
  (`benchmark`, `brainstorm`, `scanner`, `vault`, radar modules, and related tests).

### Changed
- **Public copy** — removed Digital Rain funnel language from README, MCP docs,
  and hero demo script; SSX360 remains the hosted control plane reference.
- **Version pins** — bumped public quickstart and product docs to `0.3.0`.

## [0.2.6] - 2026-06-21

SDK rollout hardening: generic public attribution, SE050 host transport preview,
and repo-local hardware rollout docs.

### Added
- **USB CDC host transport preview** - `SerialSE050Transport` for newline-delimited
  JSON `ping` / `pubkey` / `sign` framing over the RP2350 USB bridge.
- **Hardware extra** - `pip install "matrixscroll[hardware]"` now pulls in
  `pyserial` for the SE050 host path.
- **Rollout docs** - adopter kit, five-minute guide, hardware provider quickstart,
  SE050 protocol reference, and contractor-facing PoC scope kept inside the SDK repo.

### Changed
- **Public quickstarts** - replaced editor-specific public quickstarts with
  generic agent-facing guidance while keeping the manifest schema and API unchanged.
- **Hardware messaging** - clarified that the SDK now ships a host transport
  preview and mock path, while real device signing still depends on firmware PoC validation.
- **Release copy** - aligned README, support docs, CI examples, and package metadata
  around the `0.2.6` rollout surface.

## [0.2.5] - 2026-06-20

Credibility and compatibility patch: GitHub gpgsig commit binding, SE050 mock transport, YubiKey pubkey export, Rekor/GUAC CLI MVP.

### Added
- **GitHub `gpgsig` commit binding** — verify envelopes against raw commit object SHA when OpenPGP signatures are present.
- **SE050 mock transport** — `MATRIXSCROLL_SE050_MOCK=1` enables `HardwareProvider` for development (`providers/se050_transport.py`).
- **YubiKey public key export** — PKCS#11 EC public key read path (mock + real token).
- **GUAC export CLI** — `matrixscroll envelope-export-guac --bundle DIR --output guac.jsonl`.
- **Rekor publish stub** — `matrixscroll envelope-publish-rekor --bundle DIR` (dry-run artifacts; optional `--rekor-cli`).

### Fixed
- **`parse_commit()` / envelope verify** on GitHub-signed commits with multi-line `gpgsig` headers (Windows CRLF safe).

## [0.2.4] - 2026-06-20

Who-Acted gate productization: attribution policy, delegation schema, CI hardening.

### Added
- **Attribution policy** — `require_actor_types`, `deny_actor_types`,
  `require_delegation_for_actor_types`, `verify_agent_scope` in `VerifyPolicy`.
- **`delegation` block** in commit envelope schema with owner/approver/manifest pin.
- **`delegation-attestation-rfc.md`**, IDE quickstarts (Cursor, Copilot, Claude Code),
  branch-protection runbook, Rekor/GUAC bridge design doc.
- **GitHub Step Summary** in verify-action range mode; fail-closed notes fetch.
- **pre-push** SHA-bound verification; optional `publish_notes` in hook config.

### Fixed
- Empty commit ranges in `verify_envelope_range` now pass with `note: no commits in range`.

## [0.2.3] - 2026-06-20

Scroll Gate export MVP: PR commit-range verification with git notes and bundle transport.

### Added
- **`matrixscroll/gate.py`** — SHA-bound envelope verification, commit-range discovery,
  filesystem bundle export, git notes publish/fetch, and range verification summaries.
- **CLI commands** — `envelope-export`, `envelope-publish-notes`, `envelope-fetch-notes`,
  and `envelope-verify-range` with policy flags and JSON summaries for CI.
- **GitHub Action range mode** — `head-ref` / `base-ref` inputs for PR provenance gates
  via notes or bundle sources.

## [0.2.2] - 2026-06-20

Policy flags for CI and release gates.

### Added
- **CLI policy flags** — `matrixscroll verify` and `matrixscroll envelope-verify` accept
  `--require-mode` and `--trusted-keys` (JSON policy file), wired to
  `verify_manifest_with_policy()`.

## [0.2.1] - 2026-06-20

Windows and cross-platform commit envelope fix.

### Fixed
- **`parse_commit()` on Windows** — read author/committer timezone from `git cat-file commit`
  instead of reconstructing dates with `%z` (unsupported in `git show` format on Windows).

## [0.2.0] - 2026-06-20

Agent provenance release: Git commit envelopes, SDK module split, CI scaffolding.

### Added
- **Git integration** — `matrixscroll/git.py` with post-commit envelope signing
  and pre-push verification for commits being pushed.
- **Hook installer** — `matrixscroll hook-install` / `matrixscroll hook-status`
  (hooks ship inside the wheel at `matrixscroll/hooks/`).
- **Commit envelope schema** — `schemas/commit-envelope.v1.json` plus release and
  evidence-pack schemas under `schemas/`.
- **Signed examples** — `examples/*.signed.json` for CI and documentation.
- **Agent demo** — `examples/demo/agent-commit-demo.sh` and signed-example generator.
- **SDK split** — `canonical.py`, `manifest.py`, `policy.py`, `providers/` with
  `_core.py` retained as a compatibility shim.
- **Policy verification** — `verify_manifest_with_policy()` for mode and trusted-key gates.
- **YubiKey prototype** — `providers/yubikey.py` boundary (`MATRIXSCROLL_MODE=yubikey`).
- **CI** — `verify-manifest` workflow and protected-branch example using
  `SSX360/matrixscroll-verify-action@v1`.

### Changed
- CLI adds `envelope`, `envelope-verify`, and hook subcommands.
- Commit envelopes bind to the **actual** commit SHA via post-commit signing.

## [0.1.1] - 2026-06-19

Copy and citation hardening patch. No protocol or API changes.

### Changed
- Clarified public README and package metadata: v0.1.x ships a software root of
  trust; SSX360/NXP SE050 hardware signing is the compatible reference-device
  path in progress.
- Replaced a direct PDF citation that may return `403` from some environments
  with resolvable official agency pages for the joint agentic-AI guidance.
- Added regression checks so PyPI-facing metadata avoids over-strong hardware
  availability claims.

## [0.1.0] - 2026-06-19

Initial public release. Extracted from the SSX360 reference implementation.

### Added
- `EmulatedProvider` — software Ed25519 root of trust backed by a local key
  store at `~/.matrixscroll/device.json` (override with `MATRIXSCROLL_HOME`).
  Private seed is written 0600 at file-create time (no write-then-chmod race).
- `HardwareProvider` — typed stub for the NXP SE050 secure element; reports
  `is_available()` honestly so read-only surfaces can render without crashing
  before the SE050 transport ships.
- `status()` — soft status surface returning `available`/`reason` without
  raising; `identity_info()` retains the loud-failure behavior used by signing.
- `sign_manifest()` / `verify_manifest()` — manifest-level helpers using a
  deterministic canonical JSON encoding (sorted keys, ASCII-escaped, NaN
  rejected, `signature` block excluded).
- `matrixscroll` console script (`status` / `verify` / `sign`) for field
  debugging and release-evidence verification without a host application.
- Conformance test vectors under `vectors/` for third-party implementations.

### Protocol
- Identity schema: `matrixscroll.identity.v1`.
- Signature schema: `matrixscroll.signature.v1`.
- Algorithm: `ed25519`.
- Device id format: `MS-XXXX-XXXX` (SHA-256 of the raw public key, first 8 hex
  chars, uppercase).

[0.6.3]: https://github.com/SSX360/matrixscroll/releases/tag/v0.6.3
[0.6.2]: https://github.com/SSX360/matrixscroll/releases/tag/v0.6.2
[0.6.1]: https://github.com/SSX360/matrixscroll/releases/tag/v0.6.1
[0.6.0]: https://github.com/SSX360/matrixscroll/releases/tag/v0.6.0
[0.5.1]: https://github.com/SSX360/matrixscroll/releases/tag/v0.5.1
[0.5.0]: https://github.com/SSX360/matrixscroll/releases/tag/v0.5.0
[0.2.2]: https://github.com/SSX360/matrixscroll/releases/tag/v0.2.2
[0.2.1]: https://github.com/SSX360/matrixscroll/releases/tag/v0.2.1
[0.2.0]: https://github.com/SSX360/matrixscroll/releases/tag/v0.2.0
[0.1.1]: https://github.com/SSX360/matrixscroll/releases/tag/v0.1.1
[0.1.0]: https://github.com/SSX360/matrixscroll/releases/tag/v0.1.0
