# Cryptographic roadmap: Ed25519 today, post-quantum overlay, Q-Day migration

**Status:** CNSA 2.0 parameter readiness Â· September 2026 (standards status checked 12 September 2026)  
**Audience:** Security reviewers, enterprise pilots, protocol implementers

## Executive summary

| Layer | Algorithm | Shipping now | Q-Day window (est.) | Replacement |
| ----- | --------- | ------------ | ------------------- | ----------- |
| **Root of trust (hardware)** | Ed25519 (RFC 8032) | HSM / secure-element class, Ed25519 only | 2028-2033 CRQC risk | Ed25519 until hardware PQC firmware |
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
key establishment. The CNSA 2.0 FAQ (version 2.1, December 2024) states that CNSSP-15
requires all new NSS acquisitions to be CNSA 2.0 compliant from 1 January 2027 unless
otherwise noted, and that SLH-DSA is not part of CNSA 2.0. The CNSA 2.0 advisory
(September 2022) asks that new software and firmware use CNSA 2.0 signing algorithms by
2025 and that all deployed software and firmware do so by 2030, with LMS and XMSS
(SP 800-208) named for firmware signing and ML-DSA-87 permitted for signing.

| Item | Status | Notes |
| ---- | ------ | ----- |
| Software overlay `ml-dsa-87` | **Shipping now** | Default for new software PQC keys from 0.8.0; FIPS 204 Category 5; the CNSA 2.0 signature set |
| Software overlay `ml-dsa-44` / `ml-dsa-65` | **Shipping now** | Explicit selection only; not the CNSA 2.0 signature set |
| Software overlay `slh-dsa-sha2-256s` / `256f` | **Shipping now** | FIPS 205 Category 5 hash-based options; SLH-DSA is not a CNSA 2.0 algorithm |
| Software overlay `slh-dsa-sha2-128s` / `128f` | **Shipping now** | Smaller SLH-DSA sets; not Category 5 |
| NIST ACVP known-answer tests for the overlay | **Shipping now** | `vectors/acvp-sigver-fips204-fips205.json` and `tests/test_acvp_sigver.py` (0.8.0): ML-DSA-87 and SLH-DSA-SHA2-256s/f sample vectors from the NIST ACVP-Server; evidence mapping, not a CAVP or CMVP validation |
| ML-KEM-1024 primitives (`matrixscroll.kem`) | **Shipping now** | Key generation, encapsulation and decapsulation through liboqs with NIST ACVP known-answer tests (0.8.0); used by sealed evidence packs from 0.9.0 |
| ML-KEM-1024 in Matrix Scroll envelopes | **Not** | Commit/action envelopes remain signature-only; sealed evidence packs carry KEM ciphertext |
| LMS / XMSS (SP 800-208) firmware signing | **Not** | Stateful hash-based signatures need state management the file-backed signer does not provide |
| FN-DSA (FIPS 206) | **Not** | NIST has not published the draft standard as of 12 September 2026; no implementation until a final standard |
| Hardware PQC (ML-DSA-87 on secure-element class) | **In progress** | PQC signing stays software-only until a secure element ships it |
| CNSA 2.0 certification / NSA approval | **Not** | Never claimed |
| FIPS CMVP validation of the overlay | **Not** | liboqs algorithm implementation only; the Open Quantum Safe project states that it does not recommend relying on liboqs in production |

Claim discipline: naming ML-DSA-87 as the default is parameter-set readiness. It is not a
claim that SSX360 or Matrix Scroll is CNSA 2.0 certified, FIPS validated, or NSA approved.
The tested backend is liboqs 0.16.0 with liboqs-python 0.16.0 (July 2026), which names the
mechanisms `ML-DSA-87` and `SLH_DSA_PURE_SHA2_256S`; the overlay resolves its identifiers
against the enabled mechanism list at run time.

## Policy dates (United States, September 2026)

| Instrument | Date | What it says |
| ---------- | ---- | ------------ |
| CNSSP-15 (updated March 2025) via the CNSA 2.0 FAQ v2.1 | 1 January 2027 | New NSS acquisitions must be CNSA 2.0 compliant unless otherwise noted |
| CNSA 2.0 advisory (September 2022) | 2025 / 2030 | New software and firmware signed with CNSA 2.0 algorithms by 2025; all deployed software and firmware by 2030 |
| Executive Order 14412 (22 June 2026) and OMB M-26-15 | 31 December 2030 / 31 December 2031 | Federal high-value assets: quantum-resistant key establishment by end of 2030, signatures by end of 2031 |
| Department of War PQC Strategy (dated 1 April 2026) | 31 December 2030 / 31 December 2031 | Systems support PQC or are phased out by end of 2030; use PQC by end of 2031 |
| NIST IR 8547 (initial public draft, November 2024) | 2030 / 2035 | Quantum-vulnerable signatures at 112-bit strength deprecated after 2030; ECDSA, RSA and EdDSA disallowed after 2035. Still a draft as of 12 September 2026 |

Ed25519 falls under the 2035 disallowance line in the IR 8547 draft. Matrix Scroll keeps
Ed25519 as the base scheme through the transition and adds the overlay where policy asks
for it; the dates above are the reason the overlay defaults to the Category 5 set.

## Timeline (honest)

```text
2026           Ed25519 root + optional PQC overlay; default ML-DSA-87 for software (0.8.0)
2027           Policy: require_pqc for agent commits; CNSSP-15 date for new NSS acquisitions
2028-2033      Estimated CRQC window. Public keys become derivation targets
2028+          Hybrid verify default: Ed25519 AND ML-DSA pass
2030-2031      EO 14412 / DoW dates: PQC key establishment, then PQC signatures
2035           NIST IR 8547 draft: Ed25519, ECDSA and RSA disallowed
TBD            Hardware PQC firmware (secure-element class). Same verifier API, new algorithm field
Post-sunset    Ed25519-only envelopes rejected when org policy mandates PQC
```

## CNSA 2.0 full-suite track (in progress)

The shipped overlay is a hybrid: Ed25519 stays the base scheme and ML-DSA-87 is
attached beside it. The full CNSA 2.0 suite also names ML-KEM-1024 for key
establishment. This track takes both Category 5 algorithms from the parameter
table into working code, in this order.

| Step | What it delivers | Status | Evidence |
| ---- | ---------------- | ------ | -------- |
| 1. ML-KEM-1024 primitives | `matrixscroll.kem`: `kem_generate_keypair`, `kem_encapsulate`, `kem_decapsulate`, deterministic key generation from the FIPS 203 seed `d \|\| z` | **Shipping now** (0.8.0) | `tests/test_acvp_mlkem.py` against `vectors/acvp-mlkem-fips203.json`: 5 keyGen, 18 decapsulation (8 NIST ciphertexts, 10 decapsulation cases including implicit rejection) |
| 2. Sealed evidence packs | An `evidence-pack` export encrypted to an auditor's public key with a hybrid X25519 + ML-KEM-1024 key agreement (the combiner follows the TLS hybrid construction), AES-256-GCM for the body, and the pack digest signed with Ed25519 plus ML-DSA-87 | **Shipping now** (0.9.0) | `schemas/sealed-evidence-pack.v1.json`, `matrixscroll.sealed` (`seal_evidence_pack` / `unseal_evidence_pack`), `tests/test_sealed.py`; ACVP vectors for the KEM half already pass |
| 3. ML-DSA-87 as a first-class signature | A verifier profile that accepts an ML-DSA-87 signature without an Ed25519 companion once an organisation's policy sets a sunset date | **In progress** (policy field designed; `require_pqc` exists, PQC-only acceptance does not) | `formal/tla/DualSignature.tla` extended before code |
| 4. Hardware ML-DSA-87 | External secure-element firmware signing ML-DSA-87 (not shipped in this SDK) | **Not** until a secure element ships FIPS 204 in firmware | Vendor roadmap tracking; TPM 2.0 library specification revision 185 (March 2026) adds ML-DSA to the TPM side |

Each step keeps the claim discipline above: NIST sample vectors show that the
implementation computes what the standard says; they are not a CAVP certificate
or a CMVP validation, and the liboqs caveat applies to every step.

## What we verify today

1. **Ed25519** over canonical manifest bytes (`signature` block, RFC 8032).
2. **PQC overlay** (optional) over `canonical_bytes_pqc`. Excludes `signature` and
   `pqc_signatures` from the Ed25519 payload.
3. **Browser / CLI** report `pqc_present` and algorithms; full ML-DSA verify requires
   `pip install matrixscroll[pqc]` locally.

## NIST replacements (software overlay)

| NIST | Former name | Role | Matrix Scroll |
| ---- | ----------- | ---- | ------------- |
| FIPS 204 (final 13 August 2024) | ML-DSA (Dilithium) | Primary PQC signature | `ml-dsa-44/65/87` via liboqs; default `ml-dsa-87` |
| FIPS 205 (final 13 August 2024) | SLH-DSA (SPHINCS+) | Hash-based backup | `slh-dsa-sha2-128s/f` and `256s/f` |
| FIPS 206 (draft not yet published) | FN-DSA (Falcon) | Compact lattice signature | Not implemented; waits for the final standard |
| FIPS 203 (final 13 August 2024) | ML-KEM (Kyber) | Key establishment | `ml-kem-1024` and `ml-kem-768` in `matrixscroll.kem`; sealed evidence packs (`matrixscroll.sealed`, 0.9.0); envelopes remain signature-only |
| RFC 9881 (October 2025) | ML-DSA in X.509 | Certificate profile | Not used; envelopes carry raw public keys, not certificates |

Enable: `pip install "matrixscroll[pqc]==0.7.0"` and `MATRIXSCROLL_PQC=ml-dsa-87`
(published `0.7.0` still defaults to `ml-dsa-65`; after the next release that
ships this default change, you can omit the algorithm and accept `ml-dsa-87`).

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

- NIST FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA), FIPS 203 (ML-KEM), all final 13 August 2024; FIPS 204 carries an errata note dated 31 July 2026
- NIST IR 8547 (initial public draft, 12 November 2024): transition timeline; NIST SP 800-227 (final 18 September 2025): KEM recommendations
- NSA CNSA 2.0 advisory (September 2022) and FAQ version 2.1 (December 2024); CNSSP-15 (March 2025)
- Executive Order 14412 (22 June 2026) and OMB M-26-15; Department of War PQC Strategy (1 April 2026)
- NIST ACVP-Server gen-val sample vectors (ML-DSA sigVer and sigGen, FIPS 204; SLH-DSA sigVer and sigGen, FIPS 205), copied with source digests into `vectors/acvp-sigver-fips204-fips205.json`
- Open Quantum Safe liboqs 0.16.0 (9 July 2026) and liboqs-python 0.16.0 (23 July 2026)
- RFC 8032 (Ed25519); RFC 9881 (ML-DSA in X.509, October 2025)
- [`docs/SECURITY_PROPERTIES.md`](SECURITY_PROPERTIES.md)
- [`schemas/pqc-signature.v1.json`](../schemas/pqc-signature.v1.json)

