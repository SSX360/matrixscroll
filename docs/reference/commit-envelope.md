# Commit envelope schema

!!! note "Stub"
    The normative definition is
    [`schemas/commit-envelope.v1.json`](https://github.com/SSX360/matrixscroll/blob/main/schemas/commit-envelope.v1.json)
    and [`SPEC.md`](https://github.com/SSX360/matrixscroll/blob/main/SPEC.md) §4.
    This page is a reading aid and is not yet field-complete. Where the two
    disagree, the schema wins.

An envelope is canonical UTF-8 JSON: sorted keys, ASCII-escaped, no `NaN`, with
the `signature` block excluded from the bytes that get signed.

## Required blocks

The `required` array in `commit-envelope.v1.json` names four blocks.

| Block | Purpose |
| --- | --- |
| `schema` | Schema identifier, `matrixscroll.commit_envelope.v1`. A verifier rejects unknown values. |
| `commit` | The commit this envelope binds to. Holds `tree`, `parents`, `author`, `committer`, `message`, and the `actual_id` SHA the post-commit hook fills in. |
| `provenance` | Declared `actor_type` (`human`, `agent`, or `ci`) and `tool`. Optional `tool_version`, `agent_scope`, and `session_id`. |
| `repository` | Repository `name`, with optional `remote_url` and `branch`. |

The `signature` block sits outside that array, because the schema also describes
an envelope before it is signed. Verification is stricter than the schema: a
missing `signature` block returns exit `2`.

A present `signature` block requires `schema`, `algorithm`, `device_id`,
`public_key`, `mode`, `signed_at` and `value`. Its bytes are excluded from the
bytes that get signed.

## Optional blocks

| Block | Purpose |
| --- | --- |
| `delegation` | Human owner and approver attestation for agent commits. Requires `owner_id`. Added in release 0.2.4, and the wire format stays backward compatible. |
| `pqc_signatures` | Array of ML-DSA or SLH-DSA overlays attached by a software signer, defined in `commit-envelope.v1.1.json`. Additive, so a verifier that ignores the array still succeeds. |

A declared agent scope travels as `provenance.agent_scope`, a URI or path
pointing at a signed evidence manifest, rather than as a top-level block.

## Signature block

`signature.algorithm` must be `"ed25519"`. A verifier rejects every other value.
Keys and seeds are 32 bytes. Signatures are 64 bytes and detached, per
[RFC 8032](https://www.rfc-editor.org/rfc/rfc8032).

## Conformance

Run any port against
[`vectors/`](https://github.com/SSX360/matrixscroll/tree/main/vectors/) to
self-certify. The vectors are CC0.

## Related

- [Exit codes](exit-codes.md) for what a failed verification returns
- [Python API](python-api.md) for the canonical encoder
