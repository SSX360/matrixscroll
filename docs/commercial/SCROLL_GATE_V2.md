# Scroll Gate verification

Scroll Gate checks every commit in a selected Git range. The shipped SDK,
GitHub Action, and MCP server can run the check locally against on-disk
envelopes, git notes, or an exported bundle. Local verification needs no account
or API key.

## Local paths

| Surface | Command or tool |
| --- | --- |
| CLI | `matrixscroll envelope-verify-range --base <base> --head <head> --source notes` |
| MCP | `verify_pr_range` with `source=local`, `notes`, or `bundle` |
| GitHub Action | `SSX360/matrixscroll/.github/actions/verify@action-v1` |

Install the current MCP release with:

```bash
pip install "matrixscroll[mcp]==0.6.4"
```

The stdio server exposes 14 tools. `verify_pr_range` fails closed on an empty
range by default, so a mistyped base ref cannot become a successful check. Its
explicit `allow_empty=true` opt-in keeps the result labelled as an empty range.

## Optional hosted path

`verify_pr_range` with `source=hosted`, `list_envelopes`, and the hosted branch of
`audit_export` call the SSX360 API. Those calls require an `SSX360_API_KEY`
supplied outside the package. Matrix Scroll does not contain an enrollment,
billing, or API-key issuance flow.

The repository workflow posts hosted checks to:

```text
POST https://ssx360.com/api/v1/verify
Authorization: Bearer $SSX360_API_KEY
```

Use the local paths unless your organization has been given hosted access by
SSX360.

## What a pass proves

A successful range check proves that the selected commits carry envelopes whose
Ed25519 signatures validate under the configured key and policy inputs. It does
not prove who was authorized to use a key, replace build-artifact provenance, or
constitute a certification.

## Hardware signing

The same verifier accepts envelopes produced by the completed SSX360 USB signer.
The physical signer is available through
[SSX360 contact](https://ssx360.com/contact); connect it to the MCP server with
the `matrixscroll[mcp,hardware]` extras and `MATRIXSCROLL_MODE=hardware`.
