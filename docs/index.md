# Matrix Scroll

Signed machine-action records for Git commits, with offline Ed25519
verification.

Matrix Scroll attaches a signed envelope to each commit. The envelope names the
declared actor as `human`, `agent` or `ci`, plus the tool that produced the change
and an optional scope. Anyone can verify that envelope later from the CLI or from
CI. Verification needs no network and no trust in the session that produced the
commit.

Matrix Scroll is an open protocol. The SDK remains Apache-2.0 software; SSX360
supplies the physical signer and scoped cybersecurity services separately.

```bash
pip install "matrixscroll==0.7.0"
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

- **[Explanation](explanation/commit-time-vs-artifact-time.md)**

    Why commit-time provenance, how this relates to AP2, and exactly what the
    trust boundaries are.

</div>

## How the four sections differ

This documentation follows [Diátaxis](https://diataxis.fr/). The tutorial teaches
and guarantees success. The how-to guides assume you already have a goal. The
reference describes and does not explain. The explanation is where the arguments
and comparisons live.

If you are evaluating whether to adopt Matrix Scroll, read the explanation
section. If you are trying to get something working, read the how-to guides.

<!-- CLAUDE.md requires the honest-limits block to carry a "Shipping now" label,
     and ai-tells.ShipOveruse flags that word. The rule is off for this block
     only and back on immediately after it. -->
<!-- vale ai-tells.ShipOveruse = NO -->

## Verification boundaries

- **Shipping now.** PyPI `matrixscroll==0.7.0`, Git post-commit hooks,
  `sign-action`, `scroll commit`, `envelope-verify`, Scroll Gate pull-request
  verification, the browser verifier, the GitHub Action, and
  the `matrixscroll-mcp` stdio server. Emulated mode is the default provider.
- **Direct-contact hardware.** SSX360 produces the RP2350 and NXP SE050 USB
  signer and supplies it through `ssx360.com/contact`. PyPI distributes the USB
  CDC host transport. See [Trust boundaries](explanation/trust-boundaries.md).
- **Roadmap.** External Ed25519-capable hardware key backends and
  transparency-log integration.
- **Not.** Identity and access management, sandboxing, prompt filtering, or an
  agent runtime.

<!-- vale ai-tells.ShipOveruse = YES -->

Compliance language throughout is evidence mapping, not a certification claim.
