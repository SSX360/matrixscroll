# Commercial & operator docs (SDK)

Canonical operator runbooks live in **digital-rain** (docs hub):

| Doc | URL (repo path) |
|-----|-----------------|
| Boja 2-week infra plan | `digital-rain/docs/commercial/BOJA_2WEEK_WORKPLAN.md` |
| Oliver 100-point standard | `digital-rain/docs/commercial/OLIVER_100_POINT_STANDARD.md` |
| Compliance mappings | `digital-rain/docs/commercial/COMPLIANCE_MAPPINGS.md` |
| Scroll Gate v2 | [SCROLL_GATE_V2.md](./SCROLL_GATE_V2.md) (local) |

**SDK-specific gates (Boja Week 2):** `python scripts/release-readiness.py` must be a **required** CI check before merge. Version truth: PyPI `0.5.1` ↔ README quickstart ↔ consumer action pin.

**Oliver Machine persona:** README protocol links point to matrixscroll.com; relabel `ssx360` CLI simulators if binary not shipped; no AP2 Vault Card in public proof links.
