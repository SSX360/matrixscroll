<!-- vale Google.Headings = NO -->
# SE050 M1 acceptance vectors
<!-- vale Google.Headings = YES -->

Signed manifests produced by the completed SSX360 SE050 USB hardware signer.
Each file is a complete Matrix Scroll manifest with a
`matrixscroll.signature.v1` block where `mode` is `hardware`.

Filenames follow `vector_01.json` through `vector_10.json`. The manifest body uses
`schema: ssx360.test-vector.v1` so acceptance fixtures stay distinct from
general conformance vectors in the parent `vectors/` directory.

## Verify locally

```bash
matrixscroll verify vectors/se050/vector_01.json
pytest tests/test_se050_acceptance_vectors.py -v
```

Verification uses the pinned byte contract from `SPEC.md §4`: canonical JSON
(without the `signature` key) and pure Ed25519 directly over those bytes.
`device_id` is `MS-` plus the first eight uppercase hexadecimal
characters of `SHA-256(public_key)`, formatted as `MS-XXXX-XXXX`.

## Browser verifier

The Matrix Scroll site exposes vector 01 as a loadable sample at
<https://matrixscroll.com/verify/> (“Load SE050 vector 01”). Site assets live
under `assets/samples/se050/` in the separate `matrixscroll-site` repository.

## Adding vectors 02 through 10

Drop each hardware-signed file here as `vector_NN.json`, add a matching site
asset if you want a browser sample button, and extend
`tests/test_se050_acceptance_vectors.py` with the new filename.
