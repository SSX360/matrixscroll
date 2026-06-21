# SSX360 hardware provider

**Status:** Mock transport and the host USB CDC transport preview are available
now. Real RP2350 firmware still needs bench validation on Pico 2 +
OM-SE050ARD-E.

## What this mode means

- `MATRIXSCROLL_MODE=hardware` selects the SE050-backed provider preview.
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

## Quickstart (USB CDC preview)

```bash
pip install "matrixscroll[hardware]==0.2.6"
export MATRIXSCROLL_MODE=hardware
export MATRIXSCROLL_SE050_PORT=/dev/ttyACM0
matrixscroll status
```

## Environment variables

| Variable | Purpose |
|----------|---------|
| `MATRIXSCROLL_MODE=hardware` | Select hardware provider |
| `MATRIXSCROLL_SE050_MOCK=1` | Use in-process Ed25519 mock transport for dev or CI |
| `MATRIXSCROLL_SE050_PORT` | USB CDC serial device path, e.g. `COM7` or `/dev/ttyACM0` |
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
contract. The SE050 preview does that; non-Ed25519 bridge experiments do not.

## Device

Reference hardware: [matrixscroll.com/device](https://matrixscroll.com/device)
