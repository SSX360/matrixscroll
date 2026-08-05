# Hosted-path docs

Matrix Scroll signs and verifies locally with no account. These two pages cover
the parts that reach the SSX360 API, so you can read exactly what leaves your
machine before you set `SSX360_API_KEY`.

| Doc | Description |
|-----|-------------|
| [SCROLL_GATE_V2.md](./SCROLL_GATE_V2.md) | Hosted verification: CI setup, the API call, and the SLSA gap table |
| [SSX360_SCROLL.md](./SSX360_SCROLL.md) | Governed Git commits and universal action envelopes, both local |

Protocol docs: [matrixscroll.com/docs](https://matrixscroll.com/docs/)

Release quality gate: `python scripts/release-readiness.py` verifies version
truth across PyPI, README quickstart pins, and the consumer action pin.
