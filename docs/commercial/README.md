# Verification and governed commits

Matrix Scroll signs and verifies locally with no account. The MCP server ships
in the `matrixscroll[mcp]` package and exposes the same local protocol operations
to agents. A configured `SSX360_API_KEY` is needed only for tools that explicitly
call the SSX360 hosted API.

| Doc | Description |
|-----|-------------|
| [SCROLL_GATE_V2.md](./SCROLL_GATE_V2.md) | Local and optional hosted commit-range verification |
| [SSX360_SCROLL.md](./SSX360_SCROLL.md) | Governed Git commits and universal action envelopes |

Protocol documentation: [matrixscroll.com/docs](https://matrixscroll.com/docs/)

Physical SSX360 USB signers are available through
[SSX360 contact](https://ssx360.com/contact). PyPI supplies the host software,
not the device.

Release quality gate: `python scripts/release-readiness.py` verifies version
truth across PyPI, README quickstart pins, and the consumer action pin.
