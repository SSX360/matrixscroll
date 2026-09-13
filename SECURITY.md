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
| 0.7.x | Active development. Security fixes are released as patch versions. The published release is 0.7.0. |
| 0.6.x | Maintenance through 2026-11-09 under the 90-day previous-minor policy. |
| 0.5.x and earlier | Legacy. Upgrade to 0.7.x for the current MCP server, USB signer host path, and in-repo verify action. |

Pre-1.0 there is no extended support window. Pin to a known-good version
in production until 1.0.

## Disclosure

We follow a coordinated-disclosure model. Once a fix is available we publish a
GitHub Security Advisory with a CVE (where applicable) and credit the reporter
unless anonymity is requested.

**Primary report path:** open a private GitHub Security Advisory at
<https://github.com/SSX360/matrixscroll/security/advisories/new>.

Email **security@matrixscroll.com** remains listed for continuity; if inbound mail
on that domain is retired, use the GitHub advisory path above.

## Offline verification boundary

Core verification (`verify_manifest`, commit envelope verify, local range verify)
does **not** contact `matrixscroll.com`. JSON Schema `$id` values on that domain
are identifiers; the SDK loads schemas from the installed package. Optional hosted
SSX360 API tools require `SSX360_API_KEY` and reach `ssx360.com` only.

## Release yank policy

If a published release embeds a secret or contains a key-recovery vulnerability:

1. **Yank** the affected version on PyPI.
2. Publish a **GitHub Security Advisory** with remediation steps.
3. **Disclose publicly** once a fix is available.

Quiet removal without disclosure is not acceptable for a provenance library.

## Commercial boundary

- **Open (Apache-2.0):** protocol spec, schemas, vectors, verifier, MCP local tools.
- **SSX360 commercial:** physical USB signer supply, hosted Scroll Gate, scoped
  cybersecurity services. See [`docs/commercial/README.md`](docs/commercial/README.md)
  and [`docs/DOCTRINE.md`](docs/DOCTRINE.md).

## Signing key custody

Production signing keys must not reside on developer laptops.

| Environment | Expected custody |
|-------------|------------------|
| Local development | Emulated keys in `~/.matrixscroll/` only; never used for production releases |
| Production / fleet | SE050 secure element or hardware token / HSM with non-exportable Ed25519 |
| Rotation | Generate new identity, update deployment `trusted-keys.json`, record date in team notes |

See [`docs/OPERATOR_RUNBOOK.md`](docs/OPERATOR_RUNBOOK.md) for credential rotation
and [`docs/CRYPTO_ROADMAP.md`](docs/CRYPTO_ROADMAP.md) for the Category 5 overlay
and sealed evidence-pack posture.

## Cryptographic Primitives

- Signing: Ed25519 (RFC 8032) via `cryptography`'s `Ed25519PrivateKey`.
- Hashing for device id derivation: SHA-256 (truncated to 8 hex chars for the
  human-readable id; the full key is the actual identity).
- Canonical encoding: JSON with sorted keys, ASCII escaping, `allow_nan=False`,
  and the `signature` block excluded from the signing input. See `SPEC.md`.

Changes to any of the above are breaking and bump the protocol schema version.
