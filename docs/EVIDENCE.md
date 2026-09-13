# Release evidence for Matrix Scroll 0.9.0

Public evidence a NIST or DARPA reviewer can re-run without SSX360 staff in the
room. This is an evidence log, not a third-party audit, certification, or
accreditation.

## Release pins

| Item | Value |
| --- | --- |
| Package | `matrixscroll==0.9.0` |
| Supported install line | `0.7.0` and `0.9.0` on PyPI |
| Public git history | Begins at the supported 0.9.0 line (`PUBLIC_HISTORY.md`) |
| Wheel SHA-256 | `7eb7ac3c0884d9d99b783805386b06624ad79b62f0119b377f86b186372f3a46` |
| Sdist SHA-256 | `46bfc6b44e5ade77…` (confirm on PyPI files page for the full digest) |
| MCP tools | 13 |
| Default custody | Device-agnostic `IdentityProvider`; emulated Ed25519 under `~/.matrixscroll` |

Confirm digests against the files you download. Do not trust a copied table alone.

## PyPI provenance (PEP 740)

```bash
curl -H "Accept: application/vnd.pypi.integrity.v1+json" \
  https://pypi.org/integrity/matrixscroll/0.9.0/matrixscroll-0.9.0-py3-none-any.whl/provenance
```

Expect a GitHub Trusted Publishing attestation for repository `SSX360/matrixscroll`,
workflow `publish.yml`, environment `pypi`. The attested `subject[].digest.sha256`
must match the wheel SHA-256 above.

## Offline verification (classical)

```bash
pip install "matrixscroll==0.9.0"
matrixscroll verify vectors/valid_simple.json          # exit 0, "ok": true
matrixscroll verify vectors/tampered_field.json        # exit 2, "ok": false
python tools/independent_verify.py vectors/            # second implementation; no SDK import
```

CI enforces agreement between the SDK and `tools/independent_verify.py` on the
committed vector set and on 500 randomly generated documents
(`tests/test_independent_verifier.py`).

## Post-quantum evidence (parameter readiness)

Install the evaluation extra:

```bash
pip install "matrixscroll[pqc]==0.9.0"
python -m pytest tests/test_pqc.py tests/test_acvp_sigver.py tests/test_acvp_mlkem.py tests/test_sealed.py -q
```

| Surface | What it proves | What it does not prove |
| --- | --- | --- |
| ML-DSA / SLH-DSA overlay | Dual signatures verify through liboqs; ACVP sample vectors in `vectors/acvp-sigver-fips204-fips205.json` | Not FIPS CMVP, not CAVP lab validation, not CNSA certification |
| ML-KEM-1024 (`matrixscroll.kem`) | KeyGen / encaps / decaps against `vectors/acvp-mlkem-fips203.json` | Same boundary |
| Sealed evidence packs (`matrixscroll.sealed`) | Hybrid X25519 + ML-KEM-1024, AES-256-GCM body, Ed25519 + ML-DSA-87 | Same boundary; liboqs is not a production crypto module recommendation |

Default for new software PQC keys in 0.9.0 is **ML-DSA-87** (CNSA 2.0 signature
parameter set). Naming that set is parameter-set readiness only. See
`docs/CRYPTO_ROADMAP.md` and the Verification boundaries section of the README.

## Continuous checks on `main`

| Workflow | Role |
| --- | --- |
| `ci-unit` | Full pytest with `.[dev,mcp,pqc]`, CLI smoke, Glama pin |
| `verify-manifest` | Conformance vectors + PQC tests |
| `formal-verify` | TLA+ / TLC on canonical bytes, dual signature, Scroll Gate |
| `codeql` | Static analysis |
| `provenance-gate` | Hosted Scroll Gate path when configured |

Badges and run history: https://github.com/SSX360/matrixscroll/actions

## Outside evaluator (scheduled)

A release-pinned bundle asks an external security engineer, with no SSX360
assistance during the run, to:

1. install the 0.9.0 wheel and check its digest
2. verify a valid evidence record
3. reject a tampered record and an unauthorised signer
4. answer: what did you have to trust, and what blocked you

Results (pass or fail) land in this file when the run completes. Until then the
row is **scheduled**, not claimed.

## Honest limits for programme managers

- Matrix Scroll is not a FIPS 140 module, not CNSA-certified, and not NSA-approved.
- Hosted Scroll Gate and commercial evidence maintenance are separate from the
  open SDK; offline verify needs no account.
- Pre-0.7 releases are unsupported. Prefer a fresh clone after the public history
  reset.
