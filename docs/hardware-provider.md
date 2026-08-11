# SSX360 hardware provider

**Status:** L2 Hardware bench prototype, not generally available (2026-07-21). Mock transport
and USB CDC host transport ship in `matrixscroll[hardware]==0.6.3`. Pico 2 W
(RP2350) + GMT130 ST7789 LCD/LED bring-up is locked. NXP SE050 M1 signing PoC
is accepted on contractor firmware; the display bring-up UF2 keeps
`pubkey`/`sign` fail-closed until Plug & Trust + object ID restore. **Not GA.**

## What this mode means

- `MATRIXSCROLL_MODE=hardware` selects the SE050-backed provider prototype.
- The device signs canonical manifest bytes directly with Ed25519.
- The private key stays inside the secure element.
- The host and verifier stay on the same manifest schema and verification path
  used by emulated mode.

## Quickstart (mock)

```powershell
$env:MATRIXSCROLL_MODE = "hardware"
$env:MATRIXSCROLL_SE050_MOCK = "1"
matrixscroll status
```

## Quickstart (USB CDC prototype)

```bash
pip install "matrixscroll[hardware]==0.6.3"
export MATRIXSCROLL_MODE=hardware
export MATRIXSCROLL_SE050_PORT=/dev/ttyACM0
matrixscroll status
```

On Windows, use `COM3` (or the enumerated Raspberry Pi CDC port) for
`MATRIXSCROLL_SE050_PORT`.

## Bench hardware (locked)

| Piece | Detail |
|---|---|
| MCU | Raspberry Pi Pico 2 W / RP2350 |
| Secure element | NXP SE050 (OM-SE050ARD-E) |
| Display | GMT130-V1.0 IPS 240×240 ST7789 |
| Display pins | SCK18 MOSI19 CS17 DC20 RST21 BL16 (SPI mode 3) |
| Protocol | `ssx360.se050.poc.v1` |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `MATRIXSCROLL_MODE=hardware` | Select hardware provider |
| `MATRIXSCROLL_SE050_MOCK=1` | Use in-process Ed25519 mock transport for dev or CI |
| `MATRIXSCROLL_SE050_PORT` | USB CDC serial device path, e.g. `COM3` or `/dev/ttyACM0` |
| `MATRIXSCROLL_SE050_BAUD` | Optional serial baud override (default `115200`) |
| `MATRIXSCROLL_SE050_TIMEOUT_MS` | Optional request timeout in milliseconds (default `3000`) |

Wire protocol: [`SE050_USB_PROTOCOL.md`](SE050_USB_PROTOCOL.md)  
Contractor-facing PoC scope: [`SE050_POC_SCOPE.md`](SE050_POC_SCOPE.md)

## Related docs

- [`yubikey-bridge.md`](yubikey-bridge.md) - criteria for external hardware key backends
- [`SPEC.md`](../SPEC.md) - wire format and verification contract
- [`SE050_USB_PROTOCOL.md`](SE050_USB_PROTOCOL.md) - newline-delimited JSON framing
- [`SE050_POC_SCOPE.md`](SE050_POC_SCOPE.md) - contractor-ready scope and acceptance

## Rollout rule

External security keys are welcome as future Matrix Scroll backends, but they
only graduate into the mainline when they preserve the same Ed25519 byte
contract. The SE050 prototype does that; non-Ed25519 bridge experiments do not.
Do not claim GA or “hardware-backed signing ships today” while the bring-up
UF2 remains fail-closed for live SE050.

## Device

The reference hardware is a bench prototype and is not generally available, so no
product page exists. `matrixscroll.com/device` used to be linked here and returns
404. The current bench scope lives in
[`SE050_POC_SCOPE.md`](SE050_POC_SCOPE.md) and
[`SE050_USB_PROTOCOL.md`](SE050_USB_PROTOCOL.md).
