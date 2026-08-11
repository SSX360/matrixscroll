# Python API

This page is generated from the package source by mkdocstrings. It cannot drift
from the code, because it is the code. If a signature here looks wrong, the
docstring is wrong, and the fix belongs in the module.

## Package surface

::: matrixscroll
    options:
      members:
        - status
        - sign
        - verify
        - sign_manifest
        - verify_manifest
        - device_id
        - public_key_b64
        - identity_info
        - store_dir
        - get_provider
        - IdentityProvider
        - EmulatedProvider
        - HardwareProvider
        - IdentityError
      show_root_heading: false
      heading_level: 3

## `status()` fields

`status()` is the fastest way to see which trust level is active.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema` | `str` | Always `matrixscroll.identity.v1` for this release line |
| `algorithm` | `str` | Always `ed25519` for this release line |
| `available` | `bool` | Whether a signing key could be loaded |
| `mode` | `str` | `emulated` for the software signer, `hardware` for the secure-element prototype path |
| `device_id` | `str` | Stable identifier derived from the public key |
| `public_key` | `str` | Base64 Ed25519 public key, 32 bytes decoded |
| `created_at` | `str` | UTC timestamp recorded when the key store was created |

`mode` and `available` together expose the compliance level: `emulated` is L1,
`hardware` is the L2 prototype path.

The `matrixscroll status` command prints these seven fields plus a `pqc` block
reporting the post-quantum backend. The library function returns the seven fields
only, because `pqc_status()` in `matrixscroll.pqc` is a separate call.

## Canonical encoding

::: matrixscroll.canonical
    options:
      heading_level: 3
      show_root_heading: true

## Errors

::: matrixscroll.errors
    options:
      heading_level: 3
      show_root_heading: true
