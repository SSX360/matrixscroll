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
- `matrixscroll.commit_envelope.v1` — Git commit provenance document (see §10).
- `matrixscroll.release_manifest.v1` and evidence-pack schemas — release and
  audit artifacts (see §10).

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

## 10. Document types

Beyond the generic signed-manifest pattern in §5–§6, v0.2.x defines typed
documents. Each document carries a top-level `schema` string and a `signature`
block conforming to §5.

### 10.1 Commit envelope (`matrixscroll.commit_envelope.v1`)

Binds provenance metadata to a Git commit. Used by post-commit hooks and
`matrixscroll envelope-verify`.

Required top-level fields:

- `schema` — constant `"matrixscroll.commit_envelope.v1"`.
- `commit` — normalized commit object (tree, parents, author, committer,
  message; `expected_id` is informational for pre-sign drafts).
- `provenance` — `actor_type` (`human` | `agent` | `ci`), `tool`, optional
  `tool_version`, optional scope manifest reference.
- `repository` — optional remote URL, branch, and repo name.
- `signature` — per §5.

Storage path (reference implementation):

    .git/matrixscroll/envelopes/<40-char-commit-sha>.json

JSON Schema: [`schemas/commit-envelope.v1.json`](schemas/commit-envelope.v1.json).
Conformance vector: [`vectors/valid_commit_envelope.json`](vectors/valid_commit_envelope.json).

### 10.2 Release manifest (`matrixscroll.release_manifest.v1`)

Signed release metadata (version, tag, artifact list). JSON Schema:
[`schemas/release-manifest.v1.json`](schemas/release-manifest.v1.json).

### 10.3 Evidence pack

Signed audit or agent-scope evidence. JSON Schema:
[`schemas/evidence-pack.v1.json`](schemas/evidence-pack.v1.json).

## 11. Post-quantum overlay (v1.1 extension)

Matrix Scroll v1 **requires** an Ed25519 `signature` block (§5). USB, NFC, and SE050
hardware signers produce **only** this block today and remain unchanged.

Software signers MAY attach an optional `pqc_signatures` array for FIPS 204 (ML-DSA)
and FIPS 205 (SLH-DSA) post-quantum overlays. This is an **additive** extension;
verifiers that do not implement PQC MUST still verify Ed25519 and MAY ignore
`pqc_signatures`.

### 11.1 PQC signature block

Each element of `pqc_signatures`:

```json
{
  "schema": "matrixscroll.pqc_signature.v1",
  "algorithm": "ml-dsa-65",
  "public_key": "<base64(raw public key bytes)>",
  "value": "<base64(detached signature)>",
  "signed_at": "<RFC 3339 UTC, informational>"
}
```

Allowed `algorithm` values: `ml-dsa-44`, `ml-dsa-65`, `ml-dsa-87`,
`slh-dsa-sha2-128s`, `slh-dsa-sha2-128f`.

Hardware envelopes (`signature.mode` = `"hardware"`) MUST NOT include
`pqc_signatures` until secure-element firmware supports PQC. Policy engines
MUST exempt hardware mode from `require_pqc` rules.

### 11.2 Canonical input for PQC (§4.1)

PQC signing and verification remove **both** top-level keys `"signature"` and
`"pqc_signatures"` before applying §4 encoding rules. Because Ed25519 is applied
first, the PQC signing input is byte-identical to the Ed25519 signing input.

### 11.3 Verification

1. Verify Ed25519 per §6 (always required).
2. If `pqc_signatures` is absent, stop (valid for v1-only policy).
3. For each PQC block: validate `schema`, decode keys, verify against PQC canonical bytes.
4. If policy requires PQC and verification fails or array is missing (non-hardware), reject.

### 11.4 Policy knobs

| `require_pqc` | Behavior |
| ------------- | -------- |
| `false` (default) | PQC optional |
| `emulated_only` | Require valid PQC when `signature.mode` is `emulated` or `tpm` |
| `true` | Require valid PQC for all modes except `hardware` |

JSON Schema: [`schemas/pqc-signature.v1.json`](schemas/pqc-signature.v1.json),
[`schemas/commit-envelope.v1.1.json`](schemas/commit-envelope.v1.1.json).
