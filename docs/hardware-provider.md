# SSX360 hardware provider (L2)

**Status:** Mock transport available — set `MATRIXSCROLL_SE050_MOCK=1` for development.
Real I2C firmware ships when Pico 2 + OM-SE050ARD-E kits are on the bench.

## Quickstart (mock)

```powershell
$env:MATRIXSCROLL_MODE = "hardware"
$env:MATRIXSCROLL_SE050_MOCK = "1"
matrixscroll status
```

## Planned behavior

- `MATRIXSCROLL_MODE=hardware` selects the secure-element provider
- Private keys never leave the SE050; no seed on disk
- User-presence touch gating for protected-branch commits
- Compatible with the same manifest and commit-envelope schemas as L1 emulated mode

## Environment variables

| Variable | Purpose |
|----------|---------|
| `MATRIXSCROLL_MODE=hardware` | Select hardware provider |
| `MATRIXSCROLL_SE050_MOCK=1` | Use in-process Ed25519 mock transport (dev/CI) |

Firmware scaffold: [`launch/firmware/ssx360-se050/README.md`](../../launch/firmware/ssx360-se050/README.md)

## Related docs

- [`docs/yubikey-bridge.md`](yubikey-bridge.md) — bridge path before SSX360 GA
- [`launch/reference-architecture-se050-rp2350.md`](../../launch/reference-architecture-se050-rp2350.md)
- [`SPEC.md`](../SPEC.md) — wire format (unchanged for L2 signing algorithm)

## Device

Reference hardware: [matrixscroll.com/device](https://matrixscroll.com/device)
