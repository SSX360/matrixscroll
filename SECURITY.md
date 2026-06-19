# Security Policy

## Reporting a Vulnerability

The Matrix Scroll protocol underpins code provenance and release integrity, so
security reports get priority handling.

**Please do not file public GitHub issues for security vulnerabilities.**

Instead:

1. Email **security@matrixscroll.com** with a description of the issue, a
   proof-of-concept if available, and your preferred disclosure timeline.
2. Or open a private GitHub Security Advisory at
   <https://github.com/SSX360/matrixscroll/security/advisories/new>.

We aim to acknowledge new reports within **3 business days** and to have a
remediation or mitigation plan within **30 days** for confirmed issues.

## Scope

In scope:

- Cryptographic correctness of the signing and verification paths.
- Canonical encoding determinism (any input that produces different signing
  bytes across platforms, locales, or Python versions).
- Private key disclosure or persistence beyond the documented store.
- Provider isolation (any path that lets a caller exfiltrate a private seed).
- CLI behavior that produces incorrect verify results.

Out of scope:

- Vulnerabilities in upstream dependencies (`cryptography`, CPython) — please
  report those to the relevant project. We will track and update pins.
- Issues that require an attacker to already have local filesystem access at
  the same privilege level as the user running the SDK (these are documented
  trust boundaries; the secure element exists to address them).

## Supported Versions

| Version | Status |
| ------- | ------ |
| 0.1.x   | Active development; security fixes shipped on patch releases. |

Pre-1.0 there is no extended support window. Pin to a known-good version
in production until 1.0.

## Disclosure

We follow a coordinated-disclosure model. Once a fix is available we publish a
GitHub Security Advisory with a CVE (where applicable) and credit the reporter
unless anonymity is requested.

## Cryptographic Primitives

- Signing: Ed25519 (RFC 8032) via `cryptography`'s `Ed25519PrivateKey`.
- Hashing for device id derivation: SHA-256 (truncated to 8 hex chars for the
  human-readable id; the full key is the actual identity).
- Canonical encoding: JSON with sorted keys, ASCII escaping, `allow_nan=False`,
  and the `signature` block excluded from the signing input. See `SPEC.md`.

Changes to any of the above are breaking and bump the protocol schema version.
