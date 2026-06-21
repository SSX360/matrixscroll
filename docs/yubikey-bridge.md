# External key backends and YubiKey notes

**Status:** Research and rollout criteria only. Not part of the public signing
contract today.

## Public rule

Matrix Scroll v1 signs canonical manifest bytes with **pure Ed25519**. A
hardware backend qualifies for the public SDK only if it can:

1. hold a non-exportable private key or equivalent hardware root
2. sign the canonical manifest bytes directly
3. return a public key that fits the current `device_id` derivation
4. verify through the existing SDK with no alternate algorithm or verifier path

## Why the earlier PIV bridge is not shipping

YubiKey PIV is strong for authentication and enterprise device trust, but the
current PIV signing surfaces are centered on RSA or ECDSA rather than the pure
Ed25519 contract Matrix Scroll v1 already ships. That makes a PIV bridge a
different trust shape, not a drop-in Matrix Scroll backend.

For that reason:

- the public SDK does not widen the signature algorithm surface
- the earlier PIV prototype stays explicitly experimental
- the mainline release path stays anchored on Ed25519-only verification

## What counts as a good near-term backend

- an Ed25519-capable hardware path that signs canonical bytes directly
- a reproducible public-key export path
- clear user presence or key-protection semantics
- clean local developer ergonomics on at least one supported platform

Existing keys from ecosystems like YubiKey, Nitrokey, Solo, or platform
hardware can still be complementary trust roots for developers today. They
become first-class Matrix Scroll backends only when they satisfy the same byte
contract as emulated mode and the SE050 preview.

## Experimental PIV prototype

`MATRIXSCROLL_MODE=yubikey` is retained only as an explicit research boundary.
It is disabled by default and requires
`MATRIXSCROLL_ENABLE_EXPERIMENTAL_PIV=1` for local prototype work.

That path is intentionally out of the public rollout because it would otherwise
blur the trust model.

## Related docs

- [`hardware-provider.md`](hardware-provider.md)
- [`SE050_USB_PROTOCOL.md`](SE050_USB_PROTOCOL.md)
- [`SE050_POC_SCOPE.md`](SE050_POC_SCOPE.md)
