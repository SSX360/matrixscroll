# CLI commands

The package installs the console scripts `matrixscroll`, `matrixscroll-mcp`,
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
| `matrixscroll status` | Print the active identity, plus a `pqc` block, as JSON. See [`status()` fields](python-api.md#status-fields). |
| `matrixscroll identity` | Report whether this key carries a verified-identity certificate. Exits `0` when valid, `2` when absent or expired. |
| `matrixscroll claim` | Bind this key to a verified SSX360 identity. Needs a network and an account, and is the only command here that does. |
| `matrixscroll pqc-keygen --algorithm <algo>` | Generate or load an ML-DSA or SLH-DSA key. Needs the `pqc` extra. |

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
| `matrixscroll hook-install` | Install the `post-commit` and `pre-push` hooks in the current repository. `matrixscroll hook` is an alias. |
| `matrixscroll hook-status` | Report which hooks are installed, how many envelopes exist, and the recorded config. |
| `matrixscroll envelope` | Build and sign an envelope for `HEAD` without the hook. |
| `matrixscroll envelope-verify <sha>` | Verify the envelope bound to one commit, or a path to an envelope file. |
| `matrixscroll envelope-verify-range` | Verify every commit between two refs. This is what the CI gate calls. |
| `matrixscroll envelope-publish-notes` | Write envelopes into `refs/notes/matrixscroll`. |
| `matrixscroll envelope-fetch-notes` | Fetch the envelope notes ref from a remote. |
| `matrixscroll envelope-export` | Export a range of local envelopes into a filesystem bundle. |
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
| `matrixscroll envelope-publish-rekor` | Publish envelopes to a Rekor transparency log. Dry-run by default. Pass `--rekor-cli` with a `--rekor-url` to upload. |
| `matrixscroll agent-trace` | Sign and verify agent run traces (`agent_trace.v1`). |

## Environment variables

| Variable | Effect |
| --- | --- |
| `MATRIXSCROLL_MODE` | Select the provider. `emulated` is the default and the supported evaluation path. `hardware` targets the SE050 bench prototype, which is not generally available. `yubikey` and `tpm` are experimental previews that run a mock path. |
| `MATRIXSCROLL_HOME` | Override the key-store directory. Defaults to `~/.matrixscroll`. |
| `MATRIXSCROLL_ACTOR_TYPE` | Record the actor on the next commit: `human`, `agent`, or `ci`. |
| `MATRIXSCROLL_TOOL` | Record the tool that produced the commit. |

## Exit codes

See [Exit codes](exit-codes.md).
