# AIMS Actor Identity Interop

## Context

IETF **AIMS** (Agent Identity for Multi-agent Systems) draft work (Mar 2026, WIMSE/SPIFFE lineage) defines agent identity fields for authorization and audit.

## Mapping proposal

| AIMS concept | Matrix Scroll envelope field |
|--------------|------------------------------|
| Agent ID | `actor.id` |
| Agent type | `actor.type` (`human`, `agent`, `ci`) |
| Tool/session | `tool.name`, `tool.session_id` |
| SPIFFE/WIMSE URI (optional) | `actor.identity_uri` (extension) |

## Principles

- Use AIMS-compatible field names where they do not break `matrixscroll.identity.v1`.
- Treat identity URI as optional until customers require federation.
- Never claim AIMS compliance until draft stabilizes and test vectors exist.

## Next steps

1. Track AIMS draft revisions monthly.
2. Add extension block to spec when field names freeze.
3. Publish conformance vector once draft hits working-group consensus.

## Related standards

- Microsoft Agent Governance Toolkit (DIDs, Ed25519)
- NIST NCCoE agent identity concept paper (Feb 2026)
