# Matrix Scroll Conformance Vectors

These JSON fixtures are the canonical conformance set for the Matrix Scroll
protocol. Every implementation should produce the same verify result on each
file. The expected result is encoded in the filename prefix:

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
cd matrixscroll-sdk
python vectors/_generate.py
pytest tests/test_vectors.py -v
```

## Using these from another language

1. Load `valid_simple.json`.
2. Parse the top-level `signature` block to recover `public_key` (base64).
3. Compute the canonical encoding of the manifest **with the `signature` key
   removed**, per `SPEC.md §4`.
4. Run Ed25519 verify against the signature `value` (also base64).
5. The result must be **true**.

Repeat for the other `valid_*` files. Then confirm that every `tampered_*`
and `unsigned_*` file returns **false**.

## Public domain

The vectors are dedicated to the public domain under CC0 1.0 so any
implementation can ship them as part of its own test suite.
