# External key backends and YubiKey notes

**Status:** research and rollout criteria only. The public signing contract
excludes this path today.

## Public rule

Matrix Scroll signs canonical manifest bytes with **pure Ed25519** by default,
with an optional post-quantum overlay when `matrixscroll[pqc]` is installed. A
hardware backend qualifies for the public SDK only if it can:

1. hold a non-exportable private key or equivalent hardware root
2. sign the canonical manifest bytes directly
3. return a public key that fits the current `device_id` derivation
4. verify through the existing SDK with no alternate algorithm or verifier path

Implement that surface as an `IdentityProvider`. The default provider remains
file-backed emulated keys.

## Why the earlier PIV bridge stays out of the SDK

YubiKey PIV is strong for authentication and enterprise device trust, but the
current PIV signing surfaces are centered on RSA or ECDSA rather than the pure
Ed25519 contract Matrix Scroll already implements. That makes a PIV bridge a
different trust shape rather than a drop-in Matrix Scroll backend.

For that reason:

- the public SDK does not widen the signature algorithm surface for PIV
- the earlier PIV prototype stays explicitly experimental
- the mainline release path stays anchored on Ed25519 verification (plus the
  documented optional PQC overlay)

## What counts as a good near-term backend

- an Ed25519-capable hardware path that signs canonical bytes directly
- a reproducible public-key export path
- clear user presence or key-protection semantics
- clean local developer ergonomics on at least one supported platform

Existing keys from ecosystems like YubiKey, Nitrokey, Solo, or platform
hardware can still be complementary trust roots for developers today. They
become first-class Matrix Scroll backends only when they satisfy the same byte
contract as the emulated provider.

## Experimental PIV prototype

`MATRIXSCROLL_MODE=yubikey` is retained only as an explicit research boundary.
It is disabled by default and requires
`MATRIXSCROLL_ENABLE_EXPERIMENTAL_PIV=1` for local prototype work.

That path is intentionally out of the public rollout because it would otherwise
blur the trust model.

## Related docs

- [`CRYPTO_ROADMAP.md`](CRYPTO_ROADMAP.md)
- [`explanation/trust-boundaries.md`](explanation/trust-boundaries.md)
