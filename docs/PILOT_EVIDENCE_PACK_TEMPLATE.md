# Pilot evidence pack template

Template for named pilots **without** publishing identifiable customer names
until written consent exists. Replace placeholders in square brackets. Do not
fill this template with Bank of Hawaii or other real customer legal names in
the public tree.

Compliance language is evidence mapping, not a certification claim against
NIST, the SSDF, PCI DSS, or SOC 2.

## Cover

| Field | Value |
| --- | --- |
| Pilot codename | `[codename]` |
| Sector placeholder | Choose one: Hawaiʻi commercial bank / utility operator / PacSec divided-ledger / payment-integration assessment |
| Matrix Scroll version | `matrixscroll==0.10.0` (or pin actually deployed) |
| Engagement window | `[start]` to `[end]` |
| Operator contact | `[email]` |
| Consent to name publicly | No / Yes (attach approval id) |

## Scope

- Systems and repositories in scope: `[list]`
- Envelope types used: commit / action / MCP manifest / ledger epoch
- Verify paths: CLI, CI Scroll Gate, independent verifier, Rust CLI (if used)
- Out of scope: `[list]`

## Evidence checklist

| Item | Path or digest | Verdict |
| --- | --- | --- |
| Sample signed envelope | `[path]` SHA-256=`[hex]` | CONSISTENT / … |
| Independent verifier run | `[log path]` | |
| Scroll Gate range | `base..head` = `[range]` | |
| Ledger bundle (if any) | `[path]` | |
| Optional receipt / SCITT dry-run | `[path or "none"]` | |
| SBOM / dependency pin note | `[path]` | |

## Limits stated to the pilot sponsor

- Records are tamper-evident, not tamper-proof.
- A holder of a valid signing key can sign false-but-well-formed statements.
- Simulator or lab detection rates cite sample size N and are not field SLAs.
- Optional PQC overlays are software parameter readiness, not FIPS 140-3 /
  CMVP validation of Matrix Scroll.

## Independence Firewall confirmation

- Offline verify succeeded without Matrix Scroll hosted credentials: Yes / No
- Second verifier used: Yes (`tools/independent_verify.py`) / No
- Any INDETERMINATE results and their causes: `[notes]`

## Anonymization

Public excerpts use only the sector placeholders above. Internal packs may hold
legal names under the pilot's data-handling rules; those names stay out of
git until consent is recorded on the cover row.
