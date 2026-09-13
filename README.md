# Matrix Scroll

Signed machine-action records with offline verification for MCP, Git, and CI.

[![ci-unit](https://github.com/SSX360/matrixscroll/actions/workflows/ci-unit.yml/badge.svg)](https://github.com/SSX360/matrixscroll/actions/workflows/ci-unit.yml)
[![PyPI](https://img.shields.io/pypi/v/matrixscroll)](https://pypi.org/project/matrixscroll/)
[![Python](https://img.shields.io/pypi/pyversions/matrixscroll)](https://pypi.org/project/matrixscroll/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/SSX360/matrixscroll/blob/main/LICENSE)

An MCP server can change its tool descriptions or input schemas after installation. A Git commit can also declare an actor or tool without carrying a signed authorization record. Matrix Scroll records both surfaces as Ed25519-signed evidence that reviewers can verify offline, with an optional ML-DSA-87 post-quantum overlay and ML-KEM-1024 sealed evidence packs on the CNSA 2.0 Category 5 track.

The `matrixscroll-mcp` stdio server exposes 13 tools for commit envelopes, action records, pull-request checks, Git notes, MCP surface manifests, and agent traces. Custody is device-agnostic: the default is a file-backed software provider, and any device or HSM plugs in through the `IdentityProvider` seam. Local signing and verification need no cloud account.

Matrix Scroll is an open protocol. The Python SDK is Apache-2.0 software, and the specification and vectors are CC0 1.0.

## Contents

- [Install the MCP server](#install-the-mcp-server)
- [MCP tools](#mcp-tools)
- [Detect MCP tool-surface changes](#detect-mcp-tool-surface-changes)
- [Device-agnostic custody](#device-agnostic-custody)
- [Sign and verify from the CLI](#sign-and-verify-from-the-cli)
- [Verification boundaries](#verification-boundaries)
- [Verify the release](#verify-the-release)
- [Ten-minute check for reviewers](#ten-minute-check-for-reviewers)
- [Security and license](#security-and-license)

## Install the MCP server

Install the current release from PyPI:

```bash
pip install "matrixscroll[mcp]==0.9.0"
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

The `0.9.0` server exposes these tools:

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
| `scan_mcp_server` | Fingerprints MCP tool names, descriptions, and input schemas | Read-only when tools are supplied |
| `sign_mcp_manifest` | Signs an MCP tool-surface manifest | Writes only when `save_path` is set |
| `verify_mcp_manifest` | Verifies a manifest and compares it with a signed baseline | Read-only and local |
| `sign_agent_trace` | Signs a browser-agent JSONL trace | Writes a signed envelope |
| `verify_agent_trace` | Verifies a signed trace and optionally checks the source bytes | Read-only and local |

An API key is optional. Local signing, offline verification, and MCP manifest checks do not require one. Hosted organization history and hosted range verification use `SSX360_API_KEY`.

## Detect MCP tool-surface changes

Matrix Scroll records an MCP server's tool names, descriptions, and input schemas in a signed manifest. Re-scan the server after an update and compare it with the install-time baseline.

```bash
pip install "matrixscroll[mcp]==0.9.0"

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

## Device-agnostic custody

Signing goes through an `IdentityProvider` (`public_key_bytes`, `sign`, `mode`). The default `emulated` provider stores an Ed25519 key under `~/.matrixscroll`. To adapt Matrix Scroll to any device or HSM, implement that interface and select it with `MATRIXSCROLL_MODE` (or pass a provider instance to the library APIs). Experimental `tpm` and `yubikey` previews remain available; they are not the Category 5 story and do not claim hardware ML-DSA.

Historical envelopes with `signature.mode` equal to `"hardware"` still verify. The USB/SE050 signing path was removed in 0.9.0; `MATRIXSCROLL_MODE=hardware` raises instead of opening a serial port.

Sealed evidence packs (`matrixscroll.sealed`) encrypt a payload to a recipient's ML-KEM-1024 key with a hybrid X25519 + ML-KEM-1024 agreement, AES-256-GCM for the body, and Ed25519 plus ML-DSA-87 signatures over the pack. Install `matrixscroll[pqc]`. This is parameter-set readiness through liboqs, not a CNSA certification or FIPS validation.

## Sign and verify from the CLI

The Python package includes a CLI and Git hooks for workflows that do not use MCP.

```bash
pip install "matrixscroll==0.9.0"
matrixscroll hook-install

export MATRIXSCROLL_ACTOR_TYPE=ci
export MATRIXSCROLL_TOOL=release-runner
git commit -m "feat: automate release"

matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

Sign a JSON manifest directly:

```bash
matrixscroll sign release.json > release.signed.json
matrixscroll verify release.signed.json
```

`matrixscroll verify` exits with code `0` for a valid signature and code `2` for invalid input, a failed signature, a mismatched device identity, or an unsupported schema or algorithm.

## Verification boundaries

<!-- vale ai-tells.ShipOveruse = NO -->

- Release: PyPI `matrixscroll==0.9.0` installs the 13-tool stdio MCP server and Git hooks, the MCP Trust Scanner, offline verification, sealed evidence packs, and device-agnostic custody.
- Hosted tools: `list_envelopes` and the hosted modes of `verify_pr_range` and `audit_export` require `SSX360_API_KEY` and a deployed SSX360 API. Local signing and verification remain available without a key.
- Post-quantum evaluation path: the optional `matrixscroll[pqc]` extra provides ML-DSA and SLH-DSA through liboqs, including Category 5 sets (`ml-dsa-87`, `slh-dsa-sha2-256s`/`256f`). Release `0.9.0` defaults new software keys to `ml-dsa-87` for CNSA 2.0 signature-parameter alignment (`0.7.0` and earlier default to `ml-dsa-65`; pass `--algorithm` or `MATRIXSCROLL_PQC` to choose a set explicitly). That is parameter-set readiness, not CNSA certification, FIPS CMVP validation, or NSA approval. This module has no CMVP validation. liboqs states that applications should not rely on it to protect sensitive data in production.
- CNSA 2.0 full-suite track: `matrixscroll.kem` provides ML-KEM-1024 primitives (ACVP-checked). Sealed evidence packs in `matrixscroll.sealed` use hybrid X25519 + ML-KEM-1024 with Ed25519 + ML-DSA-87. Same boundary as the signature overlay: evidence mapping against NIST vectors, not a validation. See `docs/CRYPTO_ROADMAP.md`.
- Verification scope: an Ed25519 signature proves that the signed bytes match and correspond to the included public key. A trusted-key and authorization policy establishes whether the declared `actor_type` can perform the action.
- Adjacent controls: identity and access management, sandboxing, prompt filtering, and agent runtime policy remain separate controls.

<!-- vale ai-tells.ShipOveruse = YES -->

## Verify the release

GitHub Actions publishes each Matrix Scroll release through PyPI Trusted Publishing. PyPI records a PEP 740 attestation for the wheel and source distribution.

Ask PyPI for the `0.9.0` wheel provenance:

```bash
curl -H "Accept: application/vnd.pypi.integrity.v1+json" \
  https://pypi.org/integrity/matrixscroll/0.9.0/matrixscroll-0.9.0-py3-none-any.whl/provenance
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

## Ten-minute check for reviewers

Five questions a programme manager or auditor asks first, each with the command that answers it. Everything below runs offline from a clone of this repository with `pip install "matrixscroll[pqc]==0.9.0"` (the `pqc` extra is needed only for the last two lines of question 3).

1. **Does it run in one command, offline?** `matrixscroll verify vectors/valid_simple.json` prints `"ok": true` and exits `0`; `matrixscroll verify vectors/tampered_field.json` prints `"ok": false` and exits `2`. Neither command opens a network connection. Exit codes are fixed in [docs/reference/exit-codes.md](https://github.com/SSX360/matrixscroll/blob/main/docs/reference/exit-codes.md).
2. **Is there a second implementation of the verifier?** `python tools/independent_verify.py vectors/` re-implements SPEC.md sections 3 to 6 from the text, with its own canonical serializer and a pure-Python RFC 8032 Ed25519, and imports nothing from the SDK. It must reach the same verdict as the SDK on every committed vector and on 500 randomly generated documents; `tests/test_independent_verifier.py` enforces that in CI on every change.
3. **Are the vectors committed?** `vectors/valid_*.json`, `tampered_*.json` and `unsigned_*.json` are the conformance set (CC0 1.0); `vectors/acvp-sigver-fips204-fips205.json` and `vectors/acvp-mlkem-fips203.json` are NIST ACVP sample vectors with source URLs and SHA-256 digests. `python -m pytest tests/test_vectors.py tests/test_independent_verifier.py -q` runs the conformance set; `python -m pytest tests/test_acvp_sigver.py tests/test_acvp_mlkem.py -q` runs the NIST vectors through liboqs.
4. **Is the boundary stated?** [Verification boundaries](#verification-boundaries) above, [docs/CRYPTO_ROADMAP.md](https://github.com/SSX360/matrixscroll/blob/main/docs/CRYPTO_ROADMAP.md) (Shipping now / In progress / Not, with policy dates) and [docs/COMPARISON.md](https://github.com/SSX360/matrixscroll/blob/main/docs/COMPARISON.md) (a dated landscape and the claims Matrix Scroll does not make). Compliance language everywhere is evidence mapping, not a certification claim.
5. **Are the design rules checked by a model checker?** `formal/tla/` holds TLA+ models of the canonical bytes, the dual signature and the Scroll Gate range rules; `.github/workflows/formal-verify.yml` runs TLC on all seven configurations on every change to them. The models check the design, not the Python implementation; the tests above check the implementation. [docs/WHITEPAPER.md](https://github.com/SSX360/matrixscroll/blob/main/docs/WHITEPAPER.md) is the written account of the protocol.

## Security and license

Read the [security policy](https://github.com/SSX360/matrixscroll/blob/main/SECURITY.md) and [security properties](https://github.com/SSX360/matrixscroll/blob/main/docs/SECURITY_PROPERTIES.md). Report vulnerabilities privately to `security@matrixscroll.com` or through a GitHub Security Advisory.

Matrix Scroll code is licensed under Apache-2.0. [`SPEC.md`](https://github.com/SSX360/matrixscroll/blob/main/SPEC.md) and [`vectors/`](https://github.com/SSX360/matrixscroll/tree/main/vectors/) are released under CC0 1.0.

| Resource | Link |
| --- | --- |
| Tombstone / schemas | [matrixscroll.com](https://matrixscroll.com/) |
| Documentation | [GitHub docs](https://github.com/SSX360/matrixscroll/tree/main/docs) |
| Where Matrix Scroll fits (dated comparison) | [docs/COMPARISON.md](https://github.com/SSX360/matrixscroll/blob/main/docs/COMPARISON.md) |
| Cryptographic roadmap (Ed25519, ML-DSA-87 overlay, policy dates) | [docs/CRYPTO_ROADMAP.md](https://github.com/SSX360/matrixscroll/blob/main/docs/CRYPTO_ROADMAP.md) |
| Offline verification | [CLI guide](https://github.com/SSX360/matrixscroll#sign-and-verify-from-the-cli) |
| Protocol specification | [SPEC.md](https://github.com/SSX360/matrixscroll/blob/main/SPEC.md) |
| Source repository | [github.com/SSX360/matrixscroll](https://github.com/SSX360/matrixscroll) |
| SSX360 contact | [Contact SSX360](https://ssx360.com/contact) |
