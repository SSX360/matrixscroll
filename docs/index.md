# Matrix Scroll

Signed machine-action records for Git commits, with offline Ed25519
verification and optional post-quantum overlays.

Matrix Scroll attaches a signed envelope to each commit. The envelope names the
declared actor as `human`, `agent` or `ci`, plus the tool that produced the change
and an optional scope. Anyone can verify that envelope later from the CLI or from
CI. Verification needs no network and no trust in the session that produced the
commit.

The programme gold standard is
[The formal mathematics of accountability](explanation/gold-standard.md):
post-quantum proofs, offline verification, fail-closed CONSISTENT /
INCONSISTENT / INDETERMINATE verdicts, and the Rule of Refusal.

Matrix Scroll is an open protocol. The SDK is Apache-2.0. SSX360 supplies hosted
verification and scoped cybersecurity services separately. Custody is
device-agnostic: implement `IdentityProvider` for your HSM or secure element, or
use the default file-backed emulated provider.

```bash
pip install "matrixscroll==0.10.0"
```

## Start here

<div class="grid cards" markdown>

- **[Tutorial](tutorial/first-commit.md)**

    Sign and verify your first commit in 5 minutes. One guaranteed path,
    emulated mode, nothing to configure.

- **[How-to guides](how-to/gate-protected-branch.md)**

    Gate a protected branch, publish envelopes to git notes, scan an MCP server
    for drift.

- **[Reference](reference/cli.md)**

    CLI commands, exit codes, the commit-envelope schema, and the Python API
    generated from source.

- **[Explanation](explanation/gold-standard.md)**

    Gold standard, commit-time provenance, AP2, and trust boundaries.

</div>

## How the four sections differ

This documentation follows [Diátaxis](https://diataxis.fr/). The tutorial teaches
and guarantees success. The how-to guides assume you already have a goal. The
reference describes and does not explain. The explanation is where the arguments
and comparisons live.

If you are evaluating whether to adopt Matrix Scroll, read the explanation
section. If you are trying to get something working, read the how-to guides.

<!-- vale ai-tells.ShipOveruse = NO -->

## Verification boundaries

- **Shipping now.** PyPI `matrixscroll==0.10.0`, Git post-commit hooks,
  `sign-action`, `scroll commit`, `envelope-verify`, Scroll Gate pull-request
  verification, the GitHub Action, the `matrixscroll-mcp` stdio server (13 tools),
  and sealed evidence packs (`matrixscroll[pqc]`). Emulated mode is the default
  provider. Supported install line: **0.7.0–0.10.0**.
- **In progress.** External hardware key backends via `IdentityProvider`;
  transparency-log integration; hosted verification as a required CI check.
- **Not.** Identity and access management, sandboxing, prompt filtering, or an
  agent runtime. Not a CNSA, FIPS, or NSA certification claim.

<!-- vale ai-tells.ShipOveruse = YES -->
