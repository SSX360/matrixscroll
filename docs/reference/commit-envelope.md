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

| Block | Purpose |
| --- | --- |
| `schema` | Schema identifier. Verifiers reject unknown values. |
| `commit` | The commit SHA the envelope binds to. |
| `actor` | Declared actor: `human`, `agent`, or `ci`, plus the tool. |
| `signature` | `algorithm`, `public_key`, `value`, `signed_at`. Excluded from the signed bytes. |

## Optional blocks

| Block | Purpose |
| --- | --- |
| `scope` | Bounded scope the actor declared for the change. |
| `delegation` | Owner and delegation attestation. Optional since schema 0.2.4; the wire format stays backward compatible. |
| `pqc` | ML-DSA or SLH-DSA overlay attached by a software signer. Additive: a verifier that ignores it still succeeds. |

## Signature block

`signature.algorithm` must be `"ed25519"`. Verifiers reject every other value.
Keys are 32 bytes, seeds are 32 bytes, and signatures are 64-byte detached
signatures, per [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032).

## Conformance

Run any implementation against
[`vectors/`](https://github.com/SSX360/matrixscroll/tree/main/vectors/) to
self-certify. The vectors are CC0.

## Related

- [Exit codes](exit-codes.md) for what a failed verification returns
- [Python API](python-api.md) for the canonical encoder
