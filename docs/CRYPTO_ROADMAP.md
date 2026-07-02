# Cryptographic roadmap — Ed25519 today, post-quantum overlay, Q-Day migration

**Status:** POC 2 audit baseline · June 2026  
**Audience:** Security reviewers, enterprise pilots, protocol implementers

## Executive summary

| Layer | Algorithm | POC 2 (today) | Q-Day window (est.) | Replacement |
| ----- | --------- | ------------- | ------------------- | ----------- |
| **Root of trust (hardware)** | Ed25519 (RFC 8032) | SE050 / NFC signers | 2028–2033 CRQC risk | Ed25519 until hardware PQC firmware |
| **Software signers** | Ed25519 + optional overlay | `matrixscroll[pqc]` ML-DSA / SLH-DSA | Same | Dual-verify: Ed25519 + PQC required by policy |
| **Verifier contract** | Ed25519 required | All envelopes | Transition period | Accept PQC-only after announced sunset |

Ed25519 is the correct choice **on classical computers today**. It is **not** quantum-resistant.
Shor's algorithm breaks the elliptic-curve discrete log problem — Curve25519 and secp256k1
require roughly the same logical qubit budget (~1,200–2,000) on a cryptographically relevant
quantum computer (CRQC).

Matrix Scroll does **not** claim Ed25519 survives Q-Day. We ship an **additive** NIST FIPS 204/205
overlay (ML-DSA, SLH-DSA) on software signers while hardware remains Ed25519-only until secure
elements support lattice signatures in firmware.

## Timeline (honest)

```text
2026 POC 2     Ed25519 root + optional PQC overlay (v0.5.x)
2027           Policy: require_pqc for agent commits; TLA+ dual-signature models in CI
2028–2033      Estimated CRQC window — public keys become derivation targets
2028+          Hybrid verify default: Ed25519 AND ML-DSA pass
TBD            Hardware PQC firmware (SE050 class) — same verifier API, new algorithm field
Post-sunset    Ed25519-only envelopes rejected when org policy mandates PQC
```

## What we verify today

1. **Ed25519** over canonical manifest bytes (`signature` block, RFC 8032).
2. **PQC overlay** (optional) over `canonical_bytes_pqc` — excludes `signature` and `pqc_signatures`
   from the Ed25519 payload (v0.5.0 fix: overlay must not break Ed25519 verify).
3. **Browser / CLI** report `pqc_present` and algorithms; full ML-DSA verify requires
   `pip install matrixscroll[pqc]` locally.

## NIST replacements (software overlay)

| NIST | Former name | Role | Matrix Scroll |
| ---- | ----------- | ---- | ------------- |
| FIPS 204 | ML-DSA (Dilithium) | Primary PQC signature | `ml-dsa-44/65/87` via liboqs |
| FIPS 205 | SLH-DSA (SPHINCS+) | Hash-based backup | `slh-dsa-sha2-128s/f` |

Enable: `pip install "matrixscroll[pqc]==0.5.1"` and `MATRIXSCROLL_PQC=ml-dsa-65`.

## POC 2 audit answers

**Q: Is Ed25519 enough for 10-year archives?**  
A: No. Archive high-value provenance with PQC overlay enabled on software signers; plan
hardware migration when available.

**Q: Does PQC replace Ed25519 in v0.5.0?**  
A: No. PQC is additive. Hardware path is unchanged Ed25519.

**Q: What breaks on Q-Day if we do nothing?**  
A: Public Ed25519 keys reveal private keys; historical signatures are forgeable. Mitigation:
dual-signature policy + key rotation + timestamped evidence exports.

## Formal methods

See [`formal/tla/CanonicalBytes.tla`](../formal/tla/CanonicalBytes.tla) and
[`formal/tla/DualSignature.tla`](../formal/tla/DualSignature.tla). TLC checks that tamper
and wrong-key failures remain impossible regardless of PQC overlay presence.

## References

- NIST FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA)
- RFC 8032 (Ed25519)
- [`docs/SECURITY_PROPERTIES.md`](SECURITY_PROPERTIES.md)
- [`schemas/pqc-signature.v1.json`](../schemas/pqc-signature.v1.json)
