# Rekor / GUAC envelope bridge (design)

> Status: MVP shipped in v0.2.5 (`envelope-export-guac`, `envelope-publish-rekor` dry-run).

## Goal

Push verified Matrix Scroll commit envelopes into existing transparency and aggregation
systems (Sigstore Rekor, OpenSSF GUAC) without building a proprietary ledger first.

Matrix Scroll remains the **agent-authorship evidence layer**; Rekor/GUAC remain the
**audit retention and graph** layers.

## Inputs

| Source | Format | When |
|--------|--------|------|
| Git notes `refs/notes/matrixscroll` | Signed `commit_envelope.v1` JSON | After `envelope-publish-notes` |
| Filesystem bundle | `matrixscroll.envelope_bundle.v1` + `<sha>.json` | CI artifact upload |
| `envelope-verify-range` summary | JSON with per-commit results | After PR gate |

## Verification contract (unchanged)

Ingest MUST re-run:

1. `verify_manifest(envelope)` — cryptographic validity
2. `commit.actual_id == sha` — SHA binding
3. Optional `VerifyPolicy` — trusted keys, mode, actor/delegation rules

Only cryptographically valid envelopes enter external logs.

## Rekor publish (proposed)

```
envelope JSON → canonical bytes → SHA-256 digest
              → rekor-cli upload --artifact <file> --signature <ed25519> --pki-format=x509
```

Open questions:

- Map Ed25519 envelope signature to Rekor entry format (may use `hashedrekord` with envelope bytes as artifact)
- Include `device_id` and `actor_type` as custom annotations in Rekor API v2
- Anchor chronology on **Rekor insertion index**, not envelope `signed_at`

## GUAC collector (proposed)

Emit SPDX/SLSA-adjacent attestation JSON per commit:

```json
{
  "predicateType": "https://matrixscroll.com/attestation/commit-envelope/v1",
  "subject": [{"name": "<repo>@<sha>", "digest": {"sha1": "<sha>"}}],
  "predicate": { "...commit envelope or URI..." }
}
```

GUAC ingests via existing collector plugins; no Matrix Scroll SaaS required.

## CLI sketch (future)

```bash
matrixscroll envelope-publish-rekor --base origin/main --head HEAD
matrixscroll envelope-export-guac --bundle ./evidence/bundle --output guac.jsonl
```

## Non-goals

- Replace Sigstore for container signing
- Host a proprietary transparency log before Rekor interop ships
- Runtime agent monitoring

## Dependencies

- Scroll Gate adoption (notes/bundle transport) — shipped in 0.2.3+
- Owner/delegation attestation — shipped in 0.2.4 schema
- PyPI package with stable `gate.py` export API

## References

- [`docs/COMPARISON.md`](COMPARISON.md) — complementary positioning vs Sigstore/GUAC
- [`research/competitive-landscape-2026-06.md`](../../research/competitive-landscape-2026-06.md)
- Rekor: https://docs.sigstore.dev/logging/overview/
- GUAC: https://github.com/guacsec/guac
