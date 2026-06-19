# Changelog

All notable changes to the Matrix Scroll Python SDK are documented here. The
format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/SSX360/matrixscroll/releases/tag/v0.1.0
