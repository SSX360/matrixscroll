# Hosted path and governed commits

Matrix Scroll signs and verifies locally with no account. Of the two pages here,
only `SCROLL_GATE_V2.md` describes a call that leaves your machine, so read it
before you set `SSX360_API_KEY`. `SSX360_SCROLL.md` covers
`matrixscroll scroll commit` and `matrixscroll sign-action`, which both run
locally and need no key.

| Doc | Description |
|-----|-------------|
| [SCROLL_GATE_V2.md](./SCROLL_GATE_V2.md) | Hosted verification: which paths need `SSX360_API_KEY`, plus the SLSA gap table |
| [SSX360_SCROLL.md](./SSX360_SCROLL.md) | Governed Git commits and universal action envelopes, both local |

Protocol docs: [matrixscroll.com/docs](https://matrixscroll.com/docs/)

Release quality gate: `python scripts/release-readiness.py` verifies version
truth across PyPI, README quickstart pins, and the consumer action pin.
