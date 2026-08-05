# SLSA v1.2 Source Track Mapping

Matrix Scroll commit envelopes map to **SLSA Source Track** levels for agent-assisted Git changes.

## Positioning

- Sigstore/SLSA artifact tracks answer **what CI built**.
- Matrix Scroll answers **who attested this commit before push**.
- Scroll Gate provides partial Source Track coverage at commit time, complementing CI artifact attestations.

## Mapping

| SLSA Source level | Matrix Scroll capability | Notes |
|-------------------|-------------------------|-------|
| L1 — version controlled | Git commit + signed envelope | Baseline today |
| L2 — hosted build / protected history | Protected-branch Scroll Gate + branch protection | Requires org policy enforcement |
| L3 — two-party review + protected refs | Policy templates + human co-sign rules in SSX360 | Roadmap with assessor presets |
| L4 — two-person review + hermetic builds | Requires customer CI hardening beyond protocol alone | Partner narrative, not solo claim |

## Evidence artifacts

- Signed commit envelope (`matrixscroll.identity.v1`)
- Scroll Gate CI result on protected branches
- Optional `ssx360.evidence-pack.v1` export for assessors, an unsigned index
  over the signed envelopes it lists
  ([`schemas/ssx360.evidence-pack.v1.json`](../schemas/ssx360.evidence-pack.v1.json))

## Related docs

- SDK: `matrixscroll/docs/commercial/SCROLL_GATE_V2.md`
- Portal: `/docs/slsa`
- Compare: commit-time vs artifact-time provenance

## Language

Use **aligned to SLSA Source Track L1–L2 evidence** — never **SLSA certified**.
