# Matrix Scroll Conformance Vectors

These JSON fixtures are the canonical conformance set for the Matrix Scroll
protocol. Every implementation should produce the same verify result on each
file. The expected result is encoded in the filename prefix:

Hardware acceptance vectors from the SSX360 USB signer live in [`se050/`](se050/).
See that README for the fixture naming convention.

The filename-prefix table below applies to the Matrix Scroll conformance
fixtures only. The NIST ACVP bundle described in its own section further down is
a separate file with its own layout and is not a `verify_manifest` fixture.

| Prefix | Expected `verify_manifest` result |
| ------ | --------------------------------- |
| `valid_*.json`    | **true** — well-formed, signed, untampered. |
| `tampered_*.json` | **false** — body or signature was modified after signing. |
| `unsigned_*.json` | **false** — missing or malformed signature block. |

## Regenerating

The vectors are signed by a fixture key checked into `_fixture_key.json` so
they are reproducible across machines (this is a **test-only** key — do not
reuse it for any real signing). To regenerate after a protocol change:

```bash
cd matrixscroll
python vectors/_generate.py
pytest tests/test_vectors.py -v
```

## Using these from another language

1. Load `valid_simple.json` or `valid_commit_envelope.json`.
2. Parse the top-level `signature` block to recover `public_key` (base64).
3. Compute the canonical encoding of the manifest **with the `signature` key
   removed**, per `SPEC.md §4`.
4. Run Ed25519 verify against the signature `value` (also base64).
5. The result must be **true**.

Repeat for the other `valid_*` files. Then confirm that every `tampered_*`
and `unsigned_*` file returns **false**.

## NIST ACVP vectors (separate from the conformance set)

Post-quantum signature-verification vectors live in
`acvp-sigver-fips204-fips205.json`: a subset of the NIST ACVP-Server gen-val
sample files for ML-DSA-87 (FIPS 204) and SLH-DSA-SHA2-256s/256f (FIPS 205),
external interface, pure variant, with the NIST tcIds, verdicts and reason
strings, and the URL and SHA-256 of each source file. sigVer groups are NIST's
valid and modified verification inputs; sigGen groups are NIST's expected
signatures over an empty context, restated as positive verification cases so the
overlay's own verify path is exercised. `tests/test_acvp_sigver.py` runs them
through the liboqs mechanism that the overlay uses; it skips when
`matrixscroll[pqc]` is not installed. This is an evidence mapping to the NIST
sample vectors, not a certification claim: no CAVP or CMVP validation is claimed
(see `docs/CRYPTO_ROADMAP.md` for what is shipping, in progress and not claimed).

`acvp-mlkem-fips203.json` holds the ML-KEM-1024 (FIPS 203) subset for the
CNSA 2.0 full-suite track: keyGen vectors (seed `d || z` to `ek` and `dk`),
NIST-produced ciphertexts checked through decapsulation, and decapsulation
cases including the implicit-rejection values for modified ciphertexts.
`tests/test_acvp_mlkem.py` runs them through `matrixscroll.kem`. Same
provenance layout, same evidence-mapping boundary.

## Public domain

The vectors are dedicated to the public domain under CC0 1.0 so any
implementation can ship them as part of its own test suite.
