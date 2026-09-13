# Public git history

This repository's public history was reset on **14 September 2026** so that the
published tree matches the supported product line only.

| Item | Policy |
| --- | --- |
| Supported installs | `matrixscroll==0.7.0` and `matrixscroll==0.9.0` on PyPI |
| Public git source | Current `main` at **0.9.0** (device-agnostic custody) |
| Pre-0.7 git history | Not published |
| Pre-0.7 PyPI versions | Unsupported; yank when credentials allow |
| USB / SE050 host path | Removed from the public SDK in 0.9.0; protocol docs are not published |

Clones and forks created before the reset may still hold older objects. Treat
those copies as untrusted for protocol or transport reconstruction. Prefer a
fresh clone after the reset.

For release evidence suitable for proposal packages, see
[`docs/POC2_AUDIT.md`](docs/POC2_AUDIT.md) and [`SECURITY.md`](SECURITY.md).
