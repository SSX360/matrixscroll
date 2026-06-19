# Matrix Scroll Protocol — v1

This document specifies the on-the-wire format and cryptographic conventions
for Matrix Scroll. It is the source of truth for conforming implementations.

The specification text is dedicated to the public domain under CC0 1.0. The
Python reference implementation is licensed Apache-2.0; see `LICENSE`.

## 1. Versioning

Two schema identifiers are stamped into every artifact:

- `matrixscroll.identity.v1` — identity descriptors (`identity_info`,
  `status`, the on-disk key store).
- `matrixscroll.signature.v1` — the signature block attached to manifests.

A breaking change to canonical encoding, signature layout, device id
derivation, or algorithm choice **must** bump the relevant version. Minor
additions that preserve byte-for-byte signature compatibility do not bump
the schema string.

## 2. Algorithm

- **Signing:** Ed25519 (RFC 8032). 32-byte private seed, 32-byte public key,
  64-byte signature.
- **Hash for device id derivation:** SHA-256 of the raw public key bytes.

No other algorithms are valid for v1. A `signature.algorithm` value other
than `"ed25519"` MUST be rejected.

## 3. Device identifier

Given the raw 32-byte public key `P`:

    digest = uppercase(hex(SHA256(P)))
    device_id = "MS-" + digest[0:4] + "-" + digest[4:8]

The device id is a human-friendly handle; **the public key is the real
identity**. Verifiers MUST check signatures against the public key, never
against the device id alone.

## 4. Canonical encoding

The signing input is a deterministic JSON serialization of the manifest with
the top-level `signature` block removed.

Rules:

1. **Remove** the top-level key `"signature"` (if present) before encoding.
2. **Sort keys** at every level, ascending by Unicode code point.
3. **No insignificant whitespace.** Use the JSON separator pair `(",", ":")`.
4. **ASCII escape** all non-ASCII characters (`\uXXXX`). Equivalent to
   Python's `json.dumps(..., ensure_ascii=True)`.
5. **Reject NaN and Infinity.** Equivalent to `allow_nan=False`. These have
   no portable JSON representation; producing or accepting them is a bug.
6. **UTF-8** the resulting string to bytes before passing to Ed25519.

Reference implementation (`matrixscroll._core._canonical`):

```python
body = {k: v for k, v in payload.items() if k != "signature"}
return json.dumps(
    body,
    sort_keys=True,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
).encode("utf-8")
```

Any implementation that produces different bytes for the same logical
manifest is **non-conforming**. See `vectors/` for cross-checking.

## 5. Signature block

`sign_manifest` returns a copy of the input manifest with a `signature` key
appended:

```json
{
  "signature": {
    "schema": "matrixscroll.signature.v1",
    "algorithm": "ed25519",
    "device_id": "MS-XXXX-XXXX",
    "public_key": "<base64(raw 32-byte ed25519 public key)>",
    "mode": "emulated" | "hardware",
    "signed_at": "<RFC 3339 UTC timestamp, second precision, trailing Z>",
    "value": "<base64(64-byte ed25519 signature)>"
  }
}
```

Field rules:

- `schema` and `algorithm` are constants for v1.
- `public_key` and `value` use standard base64 (RFC 4648) without URL-safe
  alphabet and without trailing whitespace.
- `signed_at` is informational; verifiers MUST NOT trust it as authoritative
  time. Pair with an external trusted timestamp if needed.
- `mode` is informational; downstream policy may require `"hardware"` for
  release-grade evidence.

## 6. Verification

Given a signed manifest `M`:

1. Read `block = M["signature"]`. If absent or not a dict, **reject**.
2. Compute `input_bytes = canonical(M)` (which removes `signature`).
3. Decode `pub = base64(block["public_key"])` and
   `sig = base64(block["value"])`.
4. Run Ed25519 verify: `verify(pub, input_bytes, sig)`.
5. If the verify succeeds, the manifest is **valid**. Otherwise **invalid**.

Verifiers MUST additionally check that `block["device_id"]` matches the
derivation from `block["public_key"]`. The public key remains the authoritative
cryptographic identity; the device id check prevents UI and policy layers from
displaying a forged human-readable handle.

## 7. Key storage (emulated mode)

The emulated provider persists a key store at `~/.matrixscroll/device.json`
(override with the `MATRIXSCROLL_HOME` environment variable). The directory
is created mode `0700` and the file is created mode `0600` via `os.open` so
the seed is never momentarily world-readable.

The store schema:

```json
{
  "schema": "matrixscroll.identity.v1",
  "mode": "emulated",
  "created_at": "<RFC 3339 UTC>",
  "device_id": "MS-XXXX-XXXX",
  "public_key": "<base64>",
  "private_key": "<base64 of 32-byte seed>"
}
```

A corrupt or truncated store **MUST** fail loud (no silent re-mint).

## 8. Hardware mode

In `MATRIXSCROLL_MODE=hardware`, the provider talks to a secure element (the
reference device uses an NXP SE050) and `device.json` holds only public
material. The protocol is identical; only the provider implementation changes.

## 9. Conformance

A conforming implementation MUST:

- Reproduce the byte output of canonical encoding for every fixture in
  `vectors/valid_*.json`.
- Verify every `vectors/valid_*.json` as **valid**.
- Verify every `vectors/tampered_*.json` and `vectors/unsigned_*.json`
  as **invalid**.

It SHOULD also publish its own cross-language vectors for community testing.
