# Cryptographic backend (middle path)

Matrix Scroll v0.4.2+ routes all Ed25519 and security-relevant SHA-256
operations through a single Python module: `matrixscroll/crypto_backend.py`.

## Design

| Approach | What users install | Crypto implementation |
| -------- | ------------------ | --------------------- |
| **Full Rust rewrite** | Python SDK + Rust extension build chain | Custom PyO3/maturin crate |
| **Middle path (this release)** | `pip install matrixscroll` only | `cryptography` wheels (OpenSSL + Rust components) |
| **Pure Python fallback** | No native deps | Not used — removed from the reference SDK |

The middle path keeps the public Python API, CLI, and MCP surface unchanged while
moving primitive work onto battle-tested native code shipped inside official
`cryptography` wheels. Users never run `cargo` or `maturin`.

## Primitives

| Operation | Module API | Underlying primitive |
| --------- | ---------- | -------------------- |
| Ed25519 key generation | `generate_ed25519_private_key()` | `cryptography.hazmat.primitives.asymmetric.ed25519` |
| Ed25519 sign / verify | `ed25519_sign`, `ed25519_verify` | Same |
| SHA-256 (device IDs, gate digests, Rekor bridge) | `sha256`, `sha256_hex` | `cryptography.hazmat.primitives.hashes.SHA256` |

Git object hashing (`hashlib.sha1` in `matrixscroll/git.py`) stays on the
stdlib because it implements Git wire-format identifiers, not provenance
signatures.

## Optional provider paths

- **Emulated / TPM mock / SE050 mock** — software Ed25519 via this backend.
- **SE050 hardware** — signing occurs on the secure element; the host verifies
  responses with the same backend where needed.
- **YubiKey PIV preview** — experimental ECDSA path; not part of the v1 Ed25519
  contract and not routed through Ed25519 helpers here.

## Dependency pin

`pyproject.toml` requires `cryptography>=42.0` as a mandatory (non-optional)
dependency.

## Diagnostics

```python
from matrixscroll.crypto_backend import backend_info
print(backend_info())
```
