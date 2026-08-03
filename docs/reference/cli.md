# CLI commands

Four console scripts ship with the package: `matrixscroll`, `matrixscroll-mcp`,
`ssx360`, and `ssx360-ledger`.

!!! note "Partial stub"
    The command list below is complete for `matrixscroll`. Per-flag documentation
    is written for the commands most often used in a gate; the rest carry a
    one-line summary. `ssx360` and `ssx360-ledger` are not yet documented here.

Run `matrixscroll <command> --help` for the authoritative flag list. The parser
is the source of truth.

## Identity

| Command | Purpose |
| --- | --- |
| `matrixscroll status` | Print the active identity as JSON. See [`status()` fields](python-api.md#status-fields). |
| `matrixscroll identity` | Inspect the key store location and permissions. |
| `matrixscroll claim` | Claim a device identity. |

## Signing and verifying

| Command | Purpose |
| --- | --- |
| `matrixscroll sign <file>` | Sign a JSON manifest. Writes the signed document to stdout. |
| `matrixscroll verify <file>` | Verify a signed manifest. Exits `2` on failure. |
| `matrixscroll sign-action --type <type>` | Sign a universal action envelope: `ci_step`, `iac_change`, `db_migration`, `api_call`, `contract_deploy`. |
| `matrixscroll sign-payment` | Sign a payment-authorization record. |

## Git integration

| Command | Purpose |
| --- | --- |
| `matrixscroll hook-install` | Install the post-commit hook in the current repository. |
| `matrixscroll hook-status` | Report whether the hook is installed and active. |
| `matrixscroll envelope-verify <sha>` | Verify the envelope bound to one commit. |
| `matrixscroll envelope-verify-range` | Verify every commit between two refs. This is what the CI gate calls. |
| `matrixscroll envelope-publish-notes` | Write envelopes into `refs/notes/matrixscroll`. |
| `matrixscroll scroll commit` | Thin governed wrapper over `git commit`. Not a Git replacement. |

### `matrixscroll envelope-verify-range`

| Flag | Purpose |
| --- | --- |
| `--base <ref>` | Exclusive lower bound of the range. |
| `--head <ref>` | Inclusive upper bound. |
| `--source notes\|bundle\|local` | Where to read envelopes from. |
| `--require-mode emulated\|hardware` | Reject signatures not produced by that provider. |
| `--trusted-keys <path>` | Restrict acceptance to a key allowlist. |
| `--summary-output <path>` | Write agent and human commit counts as JSON. |

## MCP trust

| Command | Purpose |
| --- | --- |
| `matrixscroll mcp scan` | Fingerprint a server's tool surface: name, description, input schema. |
| `matrixscroll mcp sign <manifest>` | Sign a scanned manifest as a baseline. |
| `matrixscroll mcp verify <manifest> --baseline <path>` | Diff against a baseline. Exits `2` on drift. |

See [Scan an MCP server for drift](../how-to/scan-mcp-server.md).

## Interop

| Command | Purpose |
| --- | --- |
| `matrixscroll envelope-export-guac` | Export envelopes in GUAC ingest format. |
| `matrixscroll envelope-publish-rekor` | Publish to a Rekor transparency log. Dry-run only. |
| `matrixscroll agent-trace` | Sign and verify agent run traces (`agent_trace.v1`). |

## Environment variables

| Variable | Effect |
| --- | --- |
| `MATRIXSCROLL_MODE` | Select the provider: `emulated` (default) or `hardware`. |
| `MATRIXSCROLL_HOME` | Override the key-store directory. Defaults to `~/.matrixscroll`. |
| `MATRIXSCROLL_ACTOR_TYPE` | Record the actor on the next commit: `human`, `agent`, or `ci`. |
| `MATRIXSCROLL_TOOL` | Record the tool that produced the commit. |

## Exit codes

See [Exit codes](exit-codes.md).
