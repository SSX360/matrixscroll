# Release evidence for Matrix Scroll 0.10.0

Public evidence a NIST or DARPA reviewer can re-run without SSX360 staff in the
room. This is an evidence log, not a third-party audit, certification, or
accreditation.

## Release pins

| Item | Value |
| --- | --- |
| Package | `matrixscroll==0.10.0` |
| Supported install line | `0.7.0` through `0.10.0` on PyPI |
| Public git history | Begins at the supported 0.9.0 line (`PUBLIC_HISTORY.md`); 0.10.0 continues that line |
| Wheel SHA-256 | `07e6a64b54ca9906ef8134336567f72018aefba18f58953c47de67c23a341e1b` |
| Sdist SHA-256 | `f4ad791ccef4f55b5b08222b2457e536c206b6ede5061c51637a18d59ffe6b2b` |
| MCP tools | 13 |
| Default custody | Device-agnostic `IdentityProvider`; emulated Ed25519 under `~/.matrixscroll` |
| New in 0.10.0 | Hash-linked ledger (SPEC §12), primary ML-DSA-87 opt-in, Rust verifier crate |
| GitHub Release | https://github.com/SSX360/matrixscroll/releases/tag/v0.10.0 |
| PyPI | https://pypi.org/project/matrixscroll/0.10.0/ |

Confirm digests against the files you download. Do not trust a copied table alone.

## PyPI provenance (PEP 740)

```bash
curl -H "Accept: application/vnd.pypi.integrity.v1+json" \
  https://pypi.org/integrity/matrixscroll/0.10.0/matrixscroll-0.10.0-py3-none-any.whl/provenance
```

Expect a GitHub Trusted Publishing attestation for repository `SSX360/matrixscroll`,
workflow `publish.yml`, environment `pypi`.

## Offline verification (classical)

```bash
pip install "matrixscroll==0.10.0"
matrixscroll verify vectors/valid_simple.json          # exit 0, "ok": true
matrixscroll verify vectors/tampered_field.json        # exit 2, "ok": false
matrixscroll ledger verify --bundle path/to/bundle.json
python tools/independent_verify.py vectors/            # second implementation; no SDK import
```

## Local benchmark

```bash
python scripts/evidence_benchmark.py
```

See `docs/EVIDENCE_BENCHMARK.md` for the measured report shape.

## Related evidence

- `docs/ASSESSMENT_PROGRESS_2026-09-15.md` — scorecard progress vs the 15 Sep assessment
- `docs/AUDIT_RFP.md` — third-party audit engagement brief (not an audit report)
- `docs/CAVP_CMVP_ROUTE.md` — CAVP/CMVP route (policy and backend plan)
- `docs/briefings/ERA_OF_STRUCTURAL_TRUST_CORRECTED.md` — corrected claim sheet for the corporate briefing
- `rust/README.md` — memory-safe verifier start; Kani proofs are Shipping for toy invariants, Lean/F* remains the bar
