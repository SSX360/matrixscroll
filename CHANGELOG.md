# Changelog

All notable changes to the Matrix Scroll Python SDK are documented here. The
format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.2.2]: https://github.com/SSX360/matrixscroll/releases/tag/v0.2.2
[0.2.1]: https://github.com/SSX360/matrixscroll/releases/tag/v0.2.1
[0.2.0]: https://github.com/SSX360/matrixscroll/releases/tag/v0.2.0
[0.1.1]: https://github.com/SSX360/matrixscroll/releases/tag/v0.1.1
[0.1.0]: https://github.com/SSX360/matrixscroll/releases/tag/v0.1.0
