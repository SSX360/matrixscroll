# Matrix Scroll

Model Context Protocol server for signed agent provenance and offline MCP tool-surface verification.

[![ci-unit](https://github.com/SSX360/matrixscroll/actions/workflows/ci-unit.yml/badge.svg)](https://github.com/SSX360/matrixscroll/actions/workflows/ci-unit.yml)
[![PyPI](https://img.shields.io/pypi/v/matrixscroll)](https://pypi.org/project/matrixscroll/)
[![Python](https://img.shields.io/pypi/pyversions/matrixscroll)](https://pypi.org/project/matrixscroll/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/SSX360/matrixscroll/blob/main/LICENSE)

An MCP server can change its tool descriptions or input schemas after you install it. A Git commit can also name an agent without carrying proof of what signed the record. Matrix Scroll addresses both gaps with Ed25519-signed evidence that you can verify offline.

The `matrixscroll-mcp` stdio server exposes 14 tools for commit envelopes, action records, pull-request checks, Git notes, MCP surface manifests, agent traces, and the SSX360 USB signer. Local signing and verification need no cloud account.

SSX360 has completed and produced the USB signer shown below. The device uses an RP2350 USB bridge and an NXP SE050 secure element. SSX360 supplies the signer by direct inquiry through [SSX360 contact](https://ssx360.com/contact) or `mission@ssx360.com`.

Matrix Scroll is an open protocol. The Python SDK is Apache-2.0 software, and the specification and vectors are CC0 1.0.

## Contents

- [Install the MCP server](#install-the-mcp-server)
- [MCP tools](#mcp-tools)
- [Detect MCP tool-surface changes](#detect-mcp-tool-surface-changes)
- [Use the SSX360 USB signer](#use-the-ssx360-usb-signer)
- [Sign and verify from the CLI](#sign-and-verify-from-the-cli)
- [Honest limits](#honest-limits)
- [Verify the release](#verify-the-release)
- [Security and license](#security-and-license)

## Install the MCP server

Install the current release from PyPI:

```bash
pip install "matrixscroll[mcp]==0.6.4"
```

Register the stdio server in your MCP client:

```json
{
  "mcpServers": {
    "matrixscroll": {
      "command": "matrixscroll-mcp",
      "args": []
    }
  }
}
```

On Windows, use the full path to `matrixscroll-mcp.exe` inside the active virtual environment if the command is not on `PATH`.

Start the executable directly when you want to inspect the server over stdio:

```bash
matrixscroll-mcp
```

After your client connects, call `status`. The server reports the local identity, hook state, and envelope count.

## MCP tools

The `0.6.4` server exposes these tools:

| Tool | What it does | Network or write behavior |
| --- | --- | --- |
| `status` | Reports local identity, hook state, and envelope count | Read-only and local |
| `create_envelope` | Creates an Ed25519-signed Git commit envelope | Writes a local envelope by default |
| `verify_envelope` | Verifies one signed envelope and its policy fields | Read-only and local |
| `sign_action` | Signs provenance for CI, infrastructure changes, migrations, API calls, or other actions | Writes only when `save_path` is set |
| `verify_pr_range` | Checks every commit in a Git range | Local for `local`, `notes`, or `bundle`. Hosted mode requires an API key |
| `publish_notes` | Publishes local envelopes to `refs/notes/matrixscroll` | Writes local Git notes |
| `audit_export` | Exports evidence for review | Writes a local bundle or uses the hosted API when configured |
| `list_envelopes` | Lists organization envelopes | Requires `SSX360_API_KEY` and the hosted API |
| `connect_card` | Probes the SSX360 USB signer over USB CDC | Opens the configured serial port |
| `scan_mcp_server` | Fingerprints MCP tool names, descriptions, and input schemas | Read-only when tools are supplied |
| `sign_mcp_manifest` | Signs an MCP tool-surface manifest | Writes only when `save_path` is set |
| `verify_mcp_manifest` | Verifies a manifest and compares it with a signed baseline | Read-only and local |
| `sign_agent_trace` | Signs a browser-agent JSONL trace | Writes a signed envelope |
| `verify_agent_trace` | Verifies a signed trace and optionally checks the source bytes | Read-only and local |

An API key is optional. Local signing, offline verification, MCP manifest checks, and USB signer access do not require one. Hosted organization history and hosted range verification use `SSX360_API_KEY`.

## Detect MCP tool-surface changes

Matrix Scroll records an MCP server's tool names, descriptions, and input schemas in a signed manifest. Re-scan the server after an update and compare it with the install-time baseline.

```bash
pip install "matrixscroll[mcp]==0.6.4"

matrixscroll mcp scan \
  --connect stdio \
  --server-command "npx -y some-mcp-server" \
  --output manifest.json \
  --pretty

matrixscroll mcp sign manifest.json \
  --output baseline.signed.json

matrixscroll mcp scan \
  --connect stdio \
  --server-command "npx -y some-mcp-server" \
  --output current.json

matrixscroll mcp sign current.json \
  --output current.signed.json

matrixscroll mcp verify current.signed.json \
  --baseline baseline.signed.json \
  --pretty
```

The verify command exits with code `2` when the signature is invalid or the current tool surface differs from the signed baseline. You can also scan an exported `tools/list` response without starting a server:

```bash
matrixscroll mcp scan --tools tools.json --output manifest.json --pretty
```

## Use the SSX360 USB signer

![Completed SSX360 USB signer](https://raw.githubusercontent.com/SSX360/matrixscroll/main/docs/images/ssx360-usb-signer.jpg)

Install the hardware and MCP extras:

```bash
pip install "matrixscroll[mcp,hardware]==0.6.4"
```

Set the hardware provider and USB CDC port before starting the MCP server.

Windows PowerShell:

```powershell
$env:MATRIXSCROLL_MODE = "hardware"
$env:MATRIXSCROLL_SE050_PORT = "COM3"
matrixscroll status
matrixscroll-mcp
```

Linux:

```bash
export MATRIXSCROLL_MODE=hardware
export MATRIXSCROLL_SE050_PORT=/dev/ttyACM0
matrixscroll status
matrixscroll-mcp
```

You can also pass the hardware settings through the MCP client configuration:

```json
{
  "mcpServers": {
    "matrixscroll": {
      "command": "matrixscroll-mcp",
      "args": [],
      "env": {
        "MATRIXSCROLL_MODE": "hardware",
        "MATRIXSCROLL_SE050_PORT": "COM3"
      }
    }
  }
}
```

Call `connect_card` to confirm that the signer responds. Then call `status` to inspect the active provider before creating an envelope.

SSX360 supplies the finished signer through direct contact. Ask for the Matrix Scroll USB signer through [SSX360 contact](https://ssx360.com/contact). The hardware is not distributed through PyPI or listed for self-service purchase.

### How hardware signing works

![USB signing round trip](https://raw.githubusercontent.com/SSX360/matrixscroll/main/docs/images/ssx360-usb-signer-round-trip.jpg)

1. The host sends `GEN_KEY` through the RP2350 USB bridge.
2. The SE050 creates an Ed25519 key pair in the secure element. The private key is non-exportable.
3. The host reads the 32-byte public key.
4. The host sends canonical bytes with a `SIGN` request.
5. The SE050 returns a 64-byte Ed25519 signature.
6. Matrix Scroll assembles the signed record and verifies it with the same offline verifier used for software signing.

The host receives the public key and signature. The private key stays inside the SE050.

![USB signer architecture](https://raw.githubusercontent.com/SSX360/matrixscroll/main/docs/images/ssx360-usb-signer-architecture.jpg)

## Sign and verify from the CLI

The Python package includes a CLI and Git hooks for workflows that do not use MCP.

```bash
pip install "matrixscroll==0.6.4"
matrixscroll hook-install

export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-runner
git commit -m "feat: agent-assisted change"

matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

Sign a JSON manifest directly:

```bash
matrixscroll sign release.json > release.signed.json
matrixscroll verify release.signed.json
```

`matrixscroll verify` exits with code `0` for a valid signature and code `2` for invalid input, a failed signature, a mismatched device identity, or an unsupported schema or algorithm.

## Honest limits

<!-- vale ai-tells.ShipOveruse = NO -->

- Shipping now: PyPI `matrixscroll==0.6.4` installs the 14-tool stdio MCP server and Git hooks. The release also includes the MCP Trust Scanner, offline verification, and USB CDC integration for the SSX360 signer.
- Hardware availability: SSX360 produces the USB signer and supplies it after a direct inquiry. PyPI distributes the host software only.
- Hosted tools: `list_envelopes` and the hosted modes of `verify_pr_range` and `audit_export` require `SSX360_API_KEY` and a deployed SSX360 API. Local alternatives remain available without a key.
- Post-quantum overlay: the optional `matrixscroll[pqc]` extra provides ML-DSA and SLH-DSA through liboqs. This module has no CMVP validation. liboqs states that applications should not rely on it to protect sensitive data in production.
- Verification scope: an Ed25519 signature proves that the signed bytes match and correspond to the included public key. The declared `actor_type` still requires a trusted-key and authorization policy.
- Not included: identity and access management, sandboxing, prompt filtering, or an agent runtime.

<!-- vale ai-tells.ShipOveruse = YES -->

## Verify the release

GitHub Actions publishes each Matrix Scroll release through PyPI Trusted Publishing. PyPI records a PEP 740 attestation for the wheel and source distribution.

Ask PyPI for the `0.6.4` wheel provenance:

```bash
curl -H "Accept: application/vnd.pypi.integrity.v1+json" \
  https://pypi.org/integrity/matrixscroll/0.6.4/matrixscroll-0.6.4-py3-none-any.whl/provenance
```

The response names the GitHub publisher:

```json
{
  "kind": "GitHub",
  "repository": "SSX360/matrixscroll",
  "workflow": "publish.yml",
  "environment": "pypi"
}
```

Compare the attested `subject[].digest.sha256` value with the SHA-256 digest of the file you downloaded. Stop if the repository, workflow, or digest differs.

## Security and license

Read the [security policy](https://github.com/SSX360/matrixscroll/blob/main/SECURITY.md) and [security properties](https://github.com/SSX360/matrixscroll/blob/main/docs/SECURITY_PROPERTIES.md). Report vulnerabilities privately to `security@matrixscroll.com` or through a GitHub Security Advisory.

Matrix Scroll code is licensed under Apache-2.0. [`SPEC.md`](https://github.com/SSX360/matrixscroll/blob/main/SPEC.md) and [`vectors/`](https://github.com/SSX360/matrixscroll/tree/main/vectors/) are released under CC0 1.0.

| Resource | Link |
| --- | --- |
| Documentation | [matrixscroll.com/docs](https://matrixscroll.com/docs/) |
| MCP Trust Scanner | [matrixscroll.com/scan](https://matrixscroll.com/scan/) |
| Offline verifier | [matrixscroll.com/verify](https://matrixscroll.com/verify/) |
| Protocol specification | [matrixscroll.com/spec](https://matrixscroll.com/spec/) |
| Source repository | [github.com/SSX360/matrixscroll](https://github.com/SSX360/matrixscroll) |
| SSX360 contact | [Contact SSX360](https://ssx360.com/contact) |
