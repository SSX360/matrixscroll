# Commercial docs (SDK)

Product and platform documentation for the Matrix Scroll SDK and the SSX360 hosted control plane:

| Doc | Description |
|-----|-------------|
| [SCROLL_GATE_V2.md](./SCROLL_GATE_V2.md) | Scroll Gate v2 hosted verification — CI setup, API, SLSA mapping |
| [PLATFORM_PIVOT.md](./PLATFORM_PIVOT.md) | SSX360 platform migration guide — URL map, product split, pricing tiers |
| [SSX360_SCROLL.md](./SSX360_SCROLL.md) | Provenance-native Git governance — `scroll commit` and universal actions |

Full platform docs: [ssx360.com/docs](https://ssx360.com/docs) · Protocol docs: [matrixscroll.com](https://matrixscroll.com)

Release quality gate: `python scripts/release-readiness.py` verifies version truth across PyPI, README quickstart pins, and the consumer action pin.
