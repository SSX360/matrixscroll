# Matrix Scroll security properties

Machine-checkable guarantees for the reference SDK (v0.4.2). Properties marked
**verified** have Hypothesis property tests in `tests/test_security_properties.py`.
Formal TLA+ models are on the public roadmap.

| ID | Property | Statement | Status |
| -- | -------- | ----------- | ------ |
| **P1** | Sign–verify roundtrip | For any canonical manifest bytes, `verify(pub, msg, sign(msg, key))` is true when `pub` derives from the same key material. | **Verified** (Hypothesis) |
| **P2** | Tamper detection | Changing any signed byte (manifest body or signature octet) causes verification to fail. | **Verified** (Hypothesis) |
| **P3** | Wrong-key rejection | A signature valid under key A MUST NOT verify under key B's public key. | **Verified** (Hypothesis) |
| **P4** | Canonical determinism | Identical logical manifests produce identical signing input bytes after canonical JSON encoding (sorted keys, ASCII escapes, no NaN). | **Verified** (unit + vectors) |
| **P5** | Offline verification | Envelope verification requires no network, hosted API, or hardware ping once the envelope and trusted key set are local. | **Verified** (unit) |
| **P6** | Algorithm binding | Only Ed25519 (RFC 8032) signatures with `algorithm: "ed25519"` are accepted; other algorithms are rejected. | **Verified** (unit + vectors) |

## Cryptographic backend

All Ed25519 and security-relevant SHA-256 operations in the reference SDK route
through `matrixscroll/crypto_backend.py`, backed by the [`cryptography`](https://pypi.org/project/cryptography/)
package (official wheels bundle OpenSSL and Rust components; users install with
`pip install matrixscroll` only). There is no pure-Python Ed25519 fallback.

See [`CRYPTO_BACKEND.md`](CRYPTO_BACKEND.md) for the middle-path design vs a full
Rust rewrite.

## Standards alignment

- **Ed25519:** [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032) — 32-byte seed, 32-byte public key, 64-byte signature.
- **Canonical JSON:** Deterministic UTF-8 encoding per [`SPEC.md`](../SPEC.md) §4.
- **Commit envelopes:** `matrixscroll.commit_envelope.v1` schema in [`schemas/commit-envelope.v1.json`](../schemas/commit-envelope.v1.json).

## Trust modes (honest scope)

| Mode | Private key location | Shipping status |
| ---- | -------------------- | --------------- |
| **Emulated** | Owner-only file (`~/.matrixscroll/device.json`, mode 0600) | **Shipping today** |
| **Hardware (SE050)** | NXP secure element on AP2 Vault Card pilot | **Pilot / preview** — same verifier contract, key not exportable from chip |

## Roadmap (not claimed today)

- TLA+ specification of Scroll Gate merge semantics
- Third-party cryptographic audit and public threat model
- npm `@ssx360/verify` browser/Node verifier package
- IETF informational draft for commit-envelope wire format

See [`SECURITY.md`](../SECURITY.md) for vulnerability reporting.
