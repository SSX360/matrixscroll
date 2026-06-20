# Delegation attestation RFC (commit envelope v1.1)

> Status: implemented in schema 0.2.4; wire format backward compatible via optional `delegation` block.

## Problem

Alien Agent ID leads on **human→agent delegation chains**. Matrix Scroll envelopes
record `actor_type` but cannot answer *"who authorized this agent?"* without a
structured, verifiable delegation attestation.

## Solution

Add optional top-level `delegation` block to `matrixscroll.commit_envelope.v1`:

```json
"delegation": {
  "owner_id": "security@matrixscroll.com",
  "approver_id": "repo-owner",
  "delegation_manifest_uri": "examples/agentic_ai_evidence_manifest.signed.json",
  "delegation_manifest_sha256": "abc123..."
}
```

| Field | Required | Purpose |
|-------|----------|---------|
| `owner_id` | yes | Named system/resource owner (AAI-04) |
| `approver_id` | no | Human who approved scope for this session |
| `delegation_manifest_uri` | no | Path/URI to signed `agentic_ai_evidence` manifest |
| `delegation_manifest_sha256` | no | Content pin for linked manifest |

Schema: [`schemas/commit-envelope.v1.json`](../schemas/commit-envelope.v1.json)

## Verification rules

When `delegation` is present:

1. `owner_id` MUST be non-empty
2. If `delegation_manifest_uri` is set, file MUST exist and `verify_manifest()` MUST pass
3. If `delegation_manifest_sha256` is set, MUST match SHA-256 of manifest bytes

Policy gate (`VerifyPolicy`):

```json
{
  "require_delegation_for_actor_types": ["agent"]
}
```

Agent commits without `delegation.owner_id` fail closed.

## Relationship to `provenance.agent_scope`

- `agent_scope` — quick reference URI (existing, optional)
- `delegation` — structured accountability with owner + optional manifest pin

When `verify_agent_scope: true` in policy, gate verifies `agent_scope` manifest signature.
Delegation manifest is verified independently when `delegation_manifest_uri` is set.

## Control mapping

- **AAI-04** human accountability — `owner_id`, `approver_id`
- **AAI-02** least privilege — linked evidence manifest `task.allowed_operations`
- **AAI-07** monitoring — gate summaries count agent vs human commits

## Future work

- OIDC/DPoP binding (Alien parity) without cloud dependency
- Multi-agent delegation chains in one envelope
- Hardware-backed owner signatures (L2/L3)
