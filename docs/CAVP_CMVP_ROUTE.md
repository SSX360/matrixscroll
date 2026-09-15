# CAVP / CMVP route (honest path)

Evidence mapping only; not a certification claim. Naming NIST CAVP, CMVP, ACVP,
or FIPS 140-3 here does not assert that Matrix Scroll or SSX360 holds a
validation certificate.

## Current state (shipping)

| Layer | What exists | What it is not |
| --- | --- | --- |
| ACVP sample vectors | `vectors/acvp-sigver-fips204-fips205.json`, `vectors/acvp-mlkem-fips203.json`, tests `tests/test_acvp_*.py` | Not a CAVP certificate |
| Ed25519 | `cryptography` (pyca) path in `matrixscroll.crypto_backend` | Not a Matrix Scroll CMVP module |
| PQC overlay | liboqs / liboqs-python mechanisms | Open Quantum Safe states liboqs is not recommended for production reliance; not CMVP |

## Intended route

```text
ACVP samples in-repo (today)
        |
        v
Fuller ACVP vector coverage for selected mechanisms
        |
        v
CAVP: only when the cryptographic backend under test is already on a CAVP-tested
      path (for classical: pyca/cryptography with an AWS-LC or other CAVP-tested
      provider where the deployment actually uses that provider)
        |
        v
CMVP: provider switch design MATRIXSCROLL_FIPS=1 (fail-closed algorithm allowlist)
      after an actual FIPS 140-validated module is selected and configured
```

## `MATRIXSCROLL_FIPS=1` design (stub today)

[`matrixscroll/fips_mode.py`](../matrixscroll/fips_mode.py) reads
`MATRIXSCROLL_FIPS=1` and, when set, allows only algorithms routed through the
classical `cryptography` stack (today: `ed25519`) and rejects liboqs-only paths
with `IdentityError`. That is a fail-closed policy switch for deployments that
want to refuse non-FIPS-oriented backends. It is **not** CMVP validation and
does not make the process a FIPS 140-3 module.

## liboqs boundary

Keep liboqs for:

- Development and research overlays
- ACVP known-answer tests against sample vectors
- Parameter-set readiness language (for example ML-DSA-87 as Category 5 /
  CNSA 2.0 signature parameter readiness)

Do **not** claim production FIPS posture, CAVP, or CMVP on the strength of
liboqs alone.

## Evidence mapping table

| Claim you might want | Evidence you can point to today | Still required |
| --- | --- | --- |
| "We run ACVP samples" | Vector files + pytest | Broader vector sets; lab CAVP if you need a certificate |
| "Ed25519 uses pyca/cryptography" | `crypto_backend.py` | Confirm the deployed OpenSSL/AWS-LC build matches your policy |
| "FIPS mode refuses liboqs" | `fips_mode.py` + unit tests | Operational enablement; validated module selection |
| "We are FIPS validated" | None | CMVP certificate for the actual module; never assert without it |

## Related docs

- [`CRYPTO_ROADMAP.md`](CRYPTO_ROADMAP.md)
- [`docs/explanation/gold-standard.md`](explanation/gold-standard.md)
