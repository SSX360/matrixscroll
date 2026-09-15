# Changelog

All notable changes to the Matrix Scroll Python SDK are documented here. The
format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.10.0] - 2026-09-15

Path-to-10 assessment work: hash-linked ledger, supply-chain hygiene, primary
ML-DSA-87 opt-in, Rust verifier start, and funder/auditor preparation packs.
Evidence mapping only; not a certification claim.

### Added
- **Hash-linked ledger** (`matrixscroll.ledger`, SPEC §12): domain-separated
  record hashes, Merkle epoch checkpoints, three-valued `Verdict` API, CLI
  `matrixscroll ledger append|epoch|verify`, schemas, tests, and
  `formal/tla/LedgerChain.tla`.
- **Primary ML-DSA-87 mode** via `MATRIXSCROLL_PRIMARY_ALG=ml-dsa-87` (requires
  `matrixscroll[pqc]`); composite `composite-ml-dsa-65-ed25519` keeps Ed25519
  primary and attaches ML-DSA-65.
- RFC 3161-shaped timestamp field, policy knobs `require_timestamp` /
  `require_receipt`, trusted-key lifecycle windows, MCP intercept helper,
  OCSF/OTel export, JCS alias, SCITT mapping, I-D scaffold, SSDF map, SBOM
  script, Scorecard workflow, SHA-pinned CI actions, FIPS policy switch stub
  (`MATRIXSCROLL_FIPS`), Rust `matrixscroll-verify` crate with Kani stubs.
- Path-to-10 packs: `docs/AUDIT_RFP.md`, `docs/OPENSSF_SANDBOX_APPLICATION.md`,
  `docs/CAVP_CMVP_ROUTE.md`, `docs/SCITT_DATATRAILS_PLAYBOOK.md`,
  `docs/briefings/ERA_OF_STRUCTURAL_TRUST_CORRECTED.md`,
  `docs/PILOT_EVIDENCE_PACK_TEMPLATE.md`,
  `docs/ASSESSMENT_PROGRESS_2026-09-15.md`.

### Changed
- README labels Shipping vs Bar for the gold-standard pipeline.
- COMPARISON.md repaired and extended (Pipelock, IETF agent-record drafts,
  SEP-1766 closed).
- CRYPTO_ROADMAP: ML-DSA first-class as opt-in primary.

## [0.9.0] - 2026-09-13

Device-agnostic custody and CNSA 2.0 Category 5 sealed evidence packs. The USB/SE050
signing path is removed from the public SDK; historical `signature.mode=hardware`
envelopes still verify.

### Removed
- **`matrixscroll[hardware]`**, `HardwareProvider`, USB CDC SE050 transport, MCP
  `connect_card`, SE050 acceptance vectors, and USB-first documentation. Setting
  `MATRIXSCROLL_MODE=hardware` raises `IdentityError` with migration guidance.
- Product visualizations and protocol docs that described a single USB signer as the
  custody path.

### Added
- **Sealed evidence packs** (`matrixscroll.sealed`, schema
  `matrixscroll.sealed-evidence-pack.v1`): hybrid X25519 + ML-KEM-1024 key agreement,
  AES-256-GCM body, Ed25519 + ML-DSA-87 signatures. Requires `matrixscroll[pqc]`.
  Parameter-set readiness through liboqs; not a CNSA certification or FIPS validation.
- Device-agnostic custody documentation: implement `IdentityProvider` for any device
  or HSM; default remains the file-backed `emulated` provider.

### Changed
- MCP stdio server is **13 tools** (was 14). Version pins, action default, and
  public docs target **0.9.0**.
- CRYPTO_ROADMAP sealed-pack step marked shipping for 0.9.0.

## [0.8.0] - 2026-09-12

Default post-quantum signature set moves to the CNSA 2.0 parameter set. No
wire-format change; Ed25519 remains the default signature scheme and the
post-quantum overlay remains opt-in through `MATRIXSCROLL_PQC`.

### Changed
- **Default PQC algorithm is now `ml-dsa-87`.** When you run
  `matrixscroll pqc-keygen` without `--algorithm`, and when a library caller
  invokes `load_pqc_keypair` or `attach_pqc_overlay` without an algorithm while
  `MATRIXSCROLL_PQC` is unset, the SDK selects ML-DSA-87 (FIPS 204 Category 5).
  That matches the CNSA 2.0 signature parameter set. Git commit envelopes and
  `sign_manifest_with_pqc` attach the overlay only when you enable it:
  `MATRIXSCROLL_PQC` names the set (`MATRIXSCROLL_PQC=ml-dsa-87`) or the caller
  passes `pqc_algorithm`; `0`, `false`, `off` and `no` disable it, and an unset
  variable leaves the manifest Ed25519-only. `matrixscroll sign`, the MCP
  `sign_action` tool and `sign_mcp_manifest` remain Ed25519-only, as in 0.7.0;
  the MCP `create_envelope` tool signs Git envelopes through
  `sign_manifest_with_pqc`. It is parameter-set readiness through liboqs, not
  CNSA certification, FIPS CMVP validation, or NSA approval.
  Callers can still pass `ml-dsa-44` or `ml-dsa-65` explicitly. Existing key
  files under `~/.matrixscroll/pqc/` are unchanged; a new default only affects
  newly generated keys. `0.7.0` and earlier default to `ml-dsa-65`. Status of
  each algorithm (shipping now, in progress, not planned) is the table in
  `docs/CRYPTO_ROADMAP.md`.
- The public README and documentation now lead with the offline verification
  outcome, use explicit verification-boundary sections, and reserve signer
  implementation detail for qualified setup.
- **Documentation refreshed against the standards status of 12 September 2026.**
  `docs/CRYPTO_ROADMAP.md` gains a policy-dates table (CNSSP-15 and the CNSA 2.0
  FAQ v2.1, Executive Order 14412 and OMB M-26-15, the Department of War PQC
  strategy, the NIST IR 8547 draft) and rows for FIPS 206, ML-KEM, LMS/XMSS and
  the ACVP tests; `docs/COMPARISON.md` gains a dated landscape section (Sigstore,
  GitHub attestations, gittuf, forge commit signing, MCP scanners, 2025-2026
  agent-receipt projects) and a list of claims Matrix Scroll does not make. The
  README and the documentation home open with the SSX360 USB signer render
  (`docs/images/ssx360-usb-signer.jpg`, replaced) and the signer section shows
  the sign round-trip sequence.

### Added
- **`slh-dsa-sha2-256s` and `slh-dsa-sha2-256f`** in the allowed PQC algorithm
  list (FIPS 205 Category 5 hash-based options), schema, and CLI choices.
- **NIST ACVP vectors** for the overlay: `vectors/acvp-sigver-fips204-fips205.json`
  carries a subset of the ACVP-Server sample vectors for ML-DSA-87,
  SLH-DSA-SHA2-256s and SLH-DSA-SHA2-256f (external interface, pure variant):
  sigVer cases with the NIST tcIds, verdicts and reason strings, and sigGen
  expected signatures over an empty context restated as positive cases. The
  provenance block records the URL and SHA-256 of each source file. This is an
  evidence mapping to NIST sample vectors, not a certification claim
  (`docs/CRYPTO_ROADMAP.md`).
- **`tests/test_acvp_sigver.py`** verifies the NIST-valid empty-context
  signatures through `pqc_verify`, verifies and rejects the context-string
  cases through liboqs's `verify_with_ctx_str` on the same mechanism the
  overlay uses, and treats a wrong-length signature as invalid without calling
  the verifier; the provenance check runs without liboqs.
- **`tests/test_pqc.py`** signs, verifies and rejects a tampered signature for
  every identifier in `PQC_ALGORITHMS`, and checks that a key file naming a set
  the build does not enable fails through `IdentityError`.
- **`tools/independent_verify.py`**, a second implementation of the verifier
  written from SPEC.md alone: its own canonical serializer, a pure-Python
  RFC 8032 Ed25519, the device-id derivation and the section 6 procedure, with
  no import from the SDK (the section 11 overlay is checked when liboqs is
  present). `tests/test_independent_verifier.py` holds it against the SDK on
  every committed vector, on 500 random documents and on fresh signatures; the
  README's "Ten-minute check for reviewers" names the commands.
- **`matrixscroll.kem`** (CNSA 2.0 full-suite track, in progress): ML-KEM-1024
  and ML-KEM-768 key generation, encapsulation and decapsulation through liboqs,
  with deterministic key generation from the FIPS 203 seed. No envelope or
  export format uses the module yet; `docs/CRYPTO_ROADMAP.md` names the sealed
  evidence-pack design that will. `vectors/acvp-mlkem-fips203.json` and
  `tests/test_acvp_mlkem.py` check it against the NIST ACVP sample vectors
  (keyGen, decapsulation of NIST ciphertexts, implicit rejection of modified
  ciphertexts); evidence mapping, not a certification claim.
- **`CNSA_PREFERRED_PQC_ALGORITHM`** constant (`ml-dsa-87`) for policy and docs
  that need a named CNSA 2.0 signature target without hard-coding the string.
- **`docs/CRYPTO_ROADMAP.md`** CNSA 2.0 shipping / in progress / not table.

### Fixed
- **SLH-DSA identifiers now resolve against liboqs.** The overlay mapped the
  `slh-dsa-*` identifiers to mechanism names liboqs does not expose
  (`SLH-DSA-SHA2-256s`), so every SLH-DSA key generation, signature and
  verification raised `MechanismNotSupportedError` on liboqs 0.16. The backend
  now resolves each identifier against `oqs.get_enabled_sig_mechanisms()`
  (`SLH_DSA_PURE_SHA2_256S` on liboqs 0.13 and later, the hyphenated spelling as
  a fallback) and reports an unsupported set as `IdentityError` with the liboqs
  version. ML-DSA was unaffected.
- **`pqc_available()` no longer flips to true on the second call.** The probe
  cached its negative result as an empty string and returned it unchanged on
  later calls, so any second query reported the backend as present without
  liboqs installed and the next signing call failed with a raw import error
  instead of `IdentityError`. Found by the new tests, which query the probe
  from two modules.

## [0.7.0] - 2026-08-11

Fail-closed verification, package completeness, and public positioning. No
wire-format change.

### Added
- Range verification results now report agent-scope details and the formal model
  includes the default-path invariant `Inv_EmptyRangeFailsClosed`.
- Added `schemas/ssx360.evidence-pack.v1.json` for the document written by the
  evidence-pack exporter.
- Added a hardware-signed acceptance vector with CLI and CI verification
  (retired with the USB host path in 0.9.0).
- You can explicitly set the composite action's `allow-empty-range` input. It
  remains disabled by default and cannot satisfy a signature-mode requirement.

### Changed
- Empty commit ranges now return `ok: false` by default. CLI and Python callers
  that intentionally accept an empty range must opt in explicitly. MCP callers
  use the same explicit opt-in and fail closed by default.
- Documentation now describes the shipped MCP server and device-agnostic
  custody directly, without retired pricing tiers or level-based product gates.
- Development, documentation, and GitHub Action dependencies were refreshed.
- Public package metadata now describes signed machine-action records instead
  of leading with AI terminology. Exact schema terms such as `actor_type: agent`
  remain unchanged.

### Fixed
- **The verify action could hand a caller a blank `ok` when the verifier
  crashed.** It now writes all eight outputs on every path, masks captured
  verifier output in the job summary, and distinguishes tool failures from
  legitimate verification failures. Parser and action-step tests cover crashes,
  silent output, malformed JSON, and signature failures.
- Unhandled CLI exceptions now return structured JSON with exit status 1 instead
  of leaking a traceback into automation output.
- Evidence-pack annotations no longer mutate signed hosted response bodies.
- JSON schemas now ship in wheels and MCP schema resources resolve the installed
  copies.
- The MCP extra now requires the verified 1.28+ SDK line; earlier 1.x releases
  cannot register the server's annotated tools, and MCP 2.0 removed the
  `mcp.server.fastmcp` API entirely.
- You receive an explicit rejection when a hosted MCP Git range is empty, before
  any API call. Non-empty ranges send the resolved commit SHAs.
- Hosted CLI checks now write `--summary-output` on successful and empty-range
  responses, matching local checks.
- Local evidence-pack documents without a `bundle` now fail schema validation,
  and CI verifies all eight schemas from an isolated wheel installation.

### Removed
- **Breaking:** removed `matrixscroll claim`, `matrixscroll identity`, the
  `--identity` verification flag, and their private paid-enrollment client. The
  retired service no longer issues identity certificates; device identity
  remains the local Ed25519 key pair reported by `matrixscroll status`.
- Removed the retired platform-pricing and signup guide.


## Earlier releases

Versions before 0.7.0 are unsupported. Their detailed change notes and the
development history that produced them are not part of the public git
repository. Install `0.7.0` through `0.10.0` from PyPI for supported work.

