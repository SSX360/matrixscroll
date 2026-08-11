# Matrix Scroll Verify (composite action)

Verify a signed Matrix Scroll manifest or a PR commit envelope range in CI.

```yaml
- uses: SSX360/matrixscroll/.github/actions/verify@action-v1
```

This action moved here from `SSX360/matrixscroll-verify-action`, which is now
archived. Inputs, outputs and exit codes are unchanged, so an existing call site
only needs its `uses:` reference rewritten.

**Pin SDK:** `matrixscroll-version: "0.7.0"` (recommended). The action installs
**0.7.0** when the input is omitted.

**Release line policy:** current line **0.7.x**; the previous minor release line
stays supported for **90 days** after a new minor is published. Pin explicitly in
workflows when you need reproducible Scroll Gate runs during that window.

## Single manifest

```yaml
- uses: SSX360/matrixscroll/.github/actions/verify@action-v1
  with:
    manifest: release.signed.json
    matrixscroll-version: "0.7.0"
```

## PR commit range (Scroll Gate)

Developers publish envelopes to git notes before opening a PR:

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
```

Workflow:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0

- uses: SSX360/matrixscroll/.github/actions/verify@action-v1
  with:
    head-ref: ${{ github.event.pull_request.head.sha }}
    base-ref: ${{ github.event.pull_request.base.sha }}
    source: notes
    notes-ref: refs/notes/matrixscroll
    fetch-notes: "true"
    matrixscroll-version: "0.7.0"
    summary-output: provenance-summary.json
    verify-agent-scope: "true"
```

Optional policy enforcement:

```yaml
    require-mode: emulated
    trusted-keys: .github/trusted-keys.json
```

The action verifies the same offline contract the SDK and the browser verifier
use: canonical manifest bytes signed with Ed25519, with no separate
hardware-only verification path.

## MCP manifest gate (reusable workflow)

Fail CI when an MCP server's signed tool-surface manifest is missing, unsigned,
or has drifted from a committed baseline (rug-pull detection). Call the reusable
workflow from any repo:

```yaml
jobs:
  mcp-gate:
    uses: SSX360/matrixscroll/.github/workflows/mcp-manifest-gate.yml@action-v1
    with:
      manifest: mcp/my-server.signed.json
      baseline: mcp/my-server.baseline.json
      matrixscroll_version: "0.7.0"
```

Produce the manifest and baseline once with the SDK:

```bash
pip install "matrixscroll[mcp]==0.7.0"
matrixscroll mcp scan --connect stdio --server-command "npx -y <server>" -o unsigned.json
matrixscroll mcp sign unsigned.json -o mcp/my-server.signed.json
cp mcp/my-server.signed.json mcp/my-server.baseline.json  # commit both
```

Exit 2 (build failure) on a bad signature or any added, removed or mutated tool
versus the baseline. The exact diff is printed and written to the job summary.

## Inputs

| Input | Mode | Default | Description |
|-------|------|---------|-------------|
| `manifest` | manifest | `""` | Path to signed manifest JSON |
| `head-ref` | range | `""` | Head ref, enables PR gate mode |
| `base-ref` | range | `""` | Base ref for the commit range |
| `source` | range | `notes` | Envelope source: `local`, `notes`, `bundle` |
| `bundle-dir` | range | `""` | Bundle directory when `source: bundle` |
| `notes-ref` | range | `refs/notes/matrixscroll` | Git notes ref for envelope transport |
| `fetch-notes` | range | `true` | Fetch the notes ref from origin first |
| `python-version` | both | `3.12` | Python version used to install the SDK |
| `matrixscroll-version` | both | `0.7.0` | SDK version pin |
| `require-mode` | both | `""` | Policy require-mode (v0.2.1+) |
| `trusted-keys` | both | `""` | Path to trusted public keys JSON (v0.2.1+) |
| `summary-output` | range | `""` | Path for the full range verification JSON |
| `allow-empty-range` | range | `false` | Explicitly accept a range holding no commits |
| `verify-agent-scope` | range | `false` | Verify linked `agent_scope` manifest signatures |

## Outputs

| Output | Mode | Description |
|--------|------|-------------|
| `ok` | both | Whether verification passed |
| `device_id` | manifest | Signer device id |
| `mode` | manifest | Signature mode |
| `verified_count` | range | Verified commits |
| `agent_count` | range | Agent-authored commits |
| `human_count` | range | Human-authored commits |
| `modes` | range | Comma-separated modes seen |
| `summary_path` | range | Path to the summary JSON when set |

## Exit codes

| Exit | Meaning |
|------|---------|
| 0 | Signature valid |
| 1 | Configuration error |
| 2 | Verification failed |

## How the action fails

Any state that is not an affirmative verified result writes `ok=False` and fails
the step. That covers a verifier that crashes with a Python traceback, a verifier
that prints nothing, JSON that claims success without the fields backing the
claim, a `require-mode` the parsed result does not satisfy, and a call that sets
neither `manifest` nor `head-ref`.

Range mode rejects an empty range by default. Set `allow-empty-range: true` only
when checking no commits is the intended result. An empty range still cannot
satisfy `require-mode`, because it carries no signature-mode evidence.

All eight outputs carry a value on every path. `ok` is `True` or `False`, spelled
the way Python prints a bool. `verified_count`, `agent_count` and `human_count`
default to `0`, and `device_id`, `mode`, `modes` and `summary_path` default to an
empty string. A caller never
reads a blank `ok`, which is the one value a workflow condition can quietly treat
as success.

When you set `continue-on-error: true` on the step, read the output rather than
the step result:

```yaml
- name: Block the merge unless provenance verified
  if: steps.verify.outputs.ok != 'True'
  run: exit 1
```

Output that is not JSON goes to the log and the job summary so you can read the
underlying error. Secret-shaped strings are masked first, and long output keeps
its tail, where a traceback puts the exception.
[`parse_verify_output.py`](parse_verify_output.py) holds this logic, and
`tests/test_verify_action_parser.py` plus `tests/test_verify_action_step.py` pin
it.

`require-mode` is checked twice: the SDK applies it during verification, and the
action rechecks the signature mode in the result it parsed. `verify-agent-scope`
is checked by the SDK alone, because the range summary carries no per-commit
scope field for the action to recheck. Both flags now fail closed when the pinned
SDK is too old to recognise them, which previously surfaced as an argparse usage
message and a blank output.

## Operator guidance

For reproducible runs, SHA-pin this action rather than tracking `action-v1`, and
set `matrixscroll-version` explicitly in every consumer instead of relying on the
default.

**Honest limits:** emulated and SE050-backed Ed25519 signing are available; physical
SSX360 USB signers are supplied through direct contact. Compliance language is
evidence mapping, not a certification claim. Illustrative profiles are not
customer endorsements.

## Proof links

- Protocol docs: <https://matrixscroll.com/docs/>
- Browser verifier: <https://matrixscroll.com/verify/>
- Envelope specification: <https://matrixscroll.com/spec/>
- PyPI release provenance: <https://pypi.org/project/matrixscroll/0.7.0/>

## License

Apache-2.0, the same terms as the rest of this repository. See
[`LICENSE`](../../../LICENSE). Originally published as
`SSX360/matrixscroll-verify-action` under Apache-2.0.
