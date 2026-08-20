# Cryptographic roadmap: Ed25519 today, post-quantum overlay, Q-Day migration

**Status:** CNSA 2.0 parameter readiness · August 2026  
**Audience:** Security reviewers, enterprise pilots, protocol implementers

## Executive summary

| Layer | Algorithm | Shipping now | Q-Day window (est.) | Replacement |
| ----- | --------- | ------------ | ------------------- | ----------- |
| **Root of trust (hardware)** | Ed25519 (RFC 8032) | Signet / SE050 class, Ed25519 only | 2028–2033 CRQC risk | Ed25519 until hardware PQC firmware |
| **Software signers** | Ed25519 + optional overlay | `matrixscroll[pqc]` ML-DSA / SLH-DSA | Same | Dual-verify: Ed25519 + PQC required by policy |
| **Verifier contract** | Ed25519 required | All envelopes | Transition period | Accept PQC-only after announced sunset |

Ed25519 is the correct choice on classical computers today. It is not quantum-resistant.
Shor's algorithm breaks the elliptic-curve discrete log problem. Curve25519 and secp256k1
require roughly the same logical qubit budget (about 1,200 to 2,000) on a cryptographically
relevant quantum computer (CRQC).

Matrix Scroll does not claim Ed25519 survives Q-Day. We ship an additive NIST FIPS 204/205
overlay (ML-DSA, SLH-DSA) on software signers while hardware remains Ed25519-only until secure
elements support lattice signatures in firmware.

## CNSA 2.0 parameter posture

NSA's Commercial National Security Algorithm Suite 2.0 selects NIST Category 5 parameter
sets for National Security Systems: **ML-DSA-87** for signatures and **ML-KEM-1024** for
key establishment (CNSSP-15; new NSS acquisitions from 1 January 2027 unless excepted).

| Item | Status | Notes |
| ---- | ------ | ----- |
| Software overlay `ml-dsa-87` | **Shipping now** | Default when PQC is enabled; FIPS 204 Category 5 |
| Software overlay `ml-dsa-44` / `ml-dsa-65` | **Shipping now** | Explicit selection only; not the CNSA 2.0 signature set |
| Software overlay `slh-dsa-sha2-256s` / `256f` | **Shipping now** | FIPS 205 Category 5 hash-based options |
| Software overlay `slh-dsa-sha2-128s` / `128f` | **Shipping now** | Smaller SLH-DSA sets; not Category 5 |
| ML-KEM-1024 in Matrix Scroll envelopes | **Not** | Envelopes are signature-only; KEM is out of band |
| Hardware PQC (ML-DSA-87 on SE050 class) | **In progress** | Target alignment work; not shipping as product claim |
| CNSA 2.0 certification / NSA approval | **Not** | Never claimed |
| FIPS CMVP validation of the overlay | **Not** | liboqs algorithm implementation only |

Claim discipline: naming ML-DSA-87 as the default is parameter-set readiness. It is not a
claim that SSX360 or Matrix Scroll is CNSA 2.0 certified, FIPS validated, or NSA approved.

## Timeline (honest)

```text
2026           Ed25519 root + optional PQC overlay; default ML-DSA-87 for software
2027           Policy: require_pqc for agent commits; NSS acquisition date for CNSA 2.0
2028–2033      Estimated CRQC window. Public keys become derivation targets
2028+          Hybrid verify default: Ed25519 AND ML-DSA pass
TBD            Hardware PQC firmware (SE050 class). Same verifier API, new algorithm field
Post-sunset    Ed25519-only envelopes rejected when org policy mandates PQC
```

## What we verify today

1. **Ed25519** over canonical manifest bytes (`signature` block, RFC 8032).
2. **PQC overlay** (optional) over `canonical_bytes_pqc`. Excludes `signature` and
   `pqc_signatures` from the Ed25519 payload.
3. **Browser / CLI** report `pqc_present` and algorithms; full ML-DSA verify requires
   `pip install matrixscroll[pqc]` locally.

## NIST replacements (software overlay)

| NIST | Former name | Role | Matrix Scroll |
| ---- | ----------- | ---- | ------------- |
| FIPS 204 | ML-DSA (Dilithium) | Primary PQC signature | `ml-dsa-44/65/87` via liboqs; default `ml-dsa-87` |
| FIPS 205 | SLH-DSA (SPHINCS+) | Hash-based backup | `slh-dsa-sha2-128s/f` and `256s/f` |

Enable: `pip install "matrixscroll[pqc]==0.6.3"` and `MATRIXSCROLL_PQC=ml-dsa-87`
(or omit the value's algorithm after upgrade and accept the default).

## POC 2 audit answers

**Q: Is Ed25519 enough for 10-year archives?**  
A: No. Archive high-value provenance with PQC overlay enabled on software signers; plan
hardware migration when available.

**Q: Does PQC replace Ed25519?**  
A: No. PQC is additive. Hardware path is unchanged Ed25519.

**Q: What breaks on Q-Day if we do nothing?**  
A: Public Ed25519 keys reveal private keys; historical signatures are forgeable. Mitigation:
dual-signature policy + key rotation + timestamped evidence exports.

**Q: Does defaulting to ML-DSA-87 make us CNSA 2.0 compliant?**  
A: No. It aligns the software parameter set with the Category 5 choice CNSA 2.0 publishes.
Compliance for a National Security System is a program-office determination against the
full suite (including ML-KEM-1024 where key establishment applies), not a product badge.

## Formal methods

See [`formal/tla/CanonicalBytes.tla`](../formal/tla/CanonicalBytes.tla) and
[`formal/tla/DualSignature.tla`](../formal/tla/DualSignature.tla). TLC checks that tamper
and wrong-key failures remain impossible regardless of PQC overlay presence.

## References

- NIST FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA), FIPS 203 (ML-KEM)
- NSA CNSA 2.0 FAQ and CNSSP-15 (Category 5 parameter selection; NSS acquisition timeline)
- RFC 8032 (Ed25519)
- [`docs/SECURITY_PROPERTIES.md`](SECURITY_PROPERTIES.md)
- [`schemas/pqc-signature.v1.json`](../schemas/pqc-signature.v1.json)
