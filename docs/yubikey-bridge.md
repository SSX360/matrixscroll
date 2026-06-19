# YubiKey Bridge Provider — Research & Prototype

**Date:** 2026-06-19  
**Status:** Prototype boundary defined for v0.2.x  
**Provider mode:** `MATRIXSCROLL_MODE=yubikey`

## Executive summary

Matrix Scroll v1 uses **Ed25519** for manifest signatures. YubiKey PIV slots natively
support **RSA-2048/3072/4096** and **EC P-256/P-384** — not Ed25519. Therefore the
YubiKey bridge has three viable paths:

| Path | Pros | Cons | Recommendation |
|------|------|------|----------------|
| **A. PIV ECDSA P-256 bridge** | Enterprise-standard, PKCS#11, touch policy | Different algorithm than v1 Ed25519 manifests | **Phase 1 bridge** — sign digest via PIV, map to Matrix Scroll v2 or hybrid block |
| **B. OpenPGP card Ed25519** | Same curve as v1 | Less uniform on Windows, harder CI automation | Dev-only optional path |
| **C. SSH FIDO2 (`ed25519-sk`)** | Native Ed25519, Git-native | FIDO2 is auth-oriented; not ideal for automated manifest signing | Pair with Git commit signing, not Matrix Scroll manifests |

**Recommendation:** Ship `YubiKeyProvider` as a **PIV ECDSA-P256 bridge** that signs
manifest digests via PKCS#11, with a `signature.algorithm` extension proposal for
v2 (`ecdsa-p256`). Until v2 ships, use YubiKey bridge for **release-grade evidence**
where policy accepts P-256, and keep emulated Ed25519 for dev vectors.

## Yubico integration surfaces

Per [Yubico PIV Walk-Through](https://developers.yubico.com/PIV/Guides/PIV_Walk-Through.html):

- **Yubico PIV Tool** — slot management, key generation
- **ykcs11 / opensc-pkcs11** — PKCS#11 module for signing
- **PIV touch policy** — `touch-policy=always` for user presence

Per [Securing git with SSH and FIDO2](https://developers.yubico.com/SSH/Securing_git_with_SSH_and_FIDO2.html):

- Git commit signing via `ed25519-sk` is complementary, not a replacement for
  Matrix Scroll commit envelopes
- Hosting platforms verify SSH signatures separately from Matrix Scroll manifests

## Prototype architecture

```
manifest (JSON)
    │
    ▼
canonical_bytes(manifest)          # unchanged SPEC.md rules
    │
    ▼
SHA-256(canonical_bytes)             # 32-byte digest
    │
    ▼
PKCS#11 C_Sign (PIV slot 9c)       # ECDSA P-256 over digest
    │
    ▼
signature block (mode=yubikey)
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MATRIXSCROLL_MODE` | `emulated` | Set to `yubikey` |
| `MATRIXSCROLL_YKCS11_MODULE` | platform-specific | Path to `ykcs11.dll` / `.so` |
| `MATRIXSCROLL_PIV_SLOT` | `9c` | PIV signature slot |
| `MATRIXSCROLL_PIV_PIN` | — | Optional PIN (prefer prompt/agent) |

### Failure modes

| Condition | Behavior | Exit / exception |
|-----------|----------|------------------|
| Module not found | `is_available() → (False, reason)` | status JSON, no crash |
| No YubiKey inserted | `(False, "no token present")` | signing raises `IdentityError` |
| Wrong PIN | `(False, "authentication failed")` | signing raises `IdentityError` |
| Touch timeout | `(False, "user presence required")` | signing raises `IdentityError` |
| Slot empty | `(False, "no key in PIV slot")` | signing raises `IdentityError` |
| PKCS#11 unavailable on CI | use emulated in dev CI; require hardware in release CI via policy | policy exit 2 |

## SSH signing compatibility

Matrix Scroll commit envelopes and Git SSH commit signatures are **orthogonal**:

1. **Git SSH signature** — proves commit object integrity on GitHub/GitLab
2. **Matrix Scroll envelope** — proves provenance metadata (agent, tool, scope)

Recommended developer setup:

```bash
# Git native signing (optional)
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519_sk.pub

# Matrix Scroll envelope (required for agentic provenance)
export MATRIXSCROLL_MODE=yubikey   # or emulated for dev
matrixscroll hook-install
```

## Implementation status

Prototype stub: [`matrixscroll/providers/yubikey.py`](../../matrixscroll/providers/yubikey.py)

- Defines provider interface and availability checks
- Documents PKCS#11 integration points
- Does **not** add PKCS#11 runtime dependency yet (per CONTRIBUTING no-deps rule)

Future optional extra:

```toml
[project.optional-dependencies]
yubikey = ["python-pkcs11>=0.7"]
```

## v2 protocol extension (proposed)

Add to SPEC.md when PIV bridge ships:

```json
{
  "signature": {
    "algorithm": "ecdsa-p256",
    "digest": "sha256",
    "value": "<base64 DER ECDSA signature>"
  }
}
```

Conformance vectors required before enabling in release CI.

## Test plan

1. Unit: mock PKCS#11 session returns fixed signature → verify path
2. Integration (manual): YubiKey 5 + ykcs11 on Linux/macOS/Windows
3. Policy: `--require-mode yubikey` on release manifests only

## References

- [Yubico Developer Program](https://developers.yubico.com/Developer_Program/)
- [PIV Walk-Through](https://developers.yubico.com/PIV/Guides/PIV_Walk-Through.html)
- [Securing git with SSH and FIDO2](https://developers.yubico.com/SSH/Securing_git_with_SSH_and_FIDO2.html)
- [Overview of the SDK](https://docs.yubico.com/yesdk/users-manual/getting-started/overview-of-sdk.html)
