# SSX360 hardware provider (L2)

**Status:** Stage-0 prototype — `HardwareProvider` reports unavailable until the
NXP SE050 transport ships on the SSX360 reference device.

## Planned behavior

- `MATRIXSCROLL_MODE=hardware` selects the secure-element provider
- Private keys never leave the SE050; no seed on disk
- User-presence touch gating for protected-branch commits
- Compatible with the same manifest and commit-envelope schemas as L1 emulated mode

## Related docs

- [`docs/yubikey-bridge.md`](yubikey-bridge.md) — bridge path before SSX360 GA
- [`SPEC.md`](../SPEC.md) — wire format (unchanged for L2 signing algorithm)

## Device

Reference hardware: [matrixscroll.com/device](https://matrixscroll.com/device)
