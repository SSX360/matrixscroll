# Matrix Scroll

**Signed provenance for agent-assisted Git commits — verify offline, one command.**

Matrix Scroll is a cryptographic evidence layer: when an AI agent (Cursor, Claude Code, Copilot, etc.) produces a commit, a signed **commit envelope** records actor, tool, and optional scope. Verify locally or in CI without trusting the IDE. The v0.2.x reference SDK ships an emulated Ed25519 root of trust with Git hooks; SSX360/NXP SE050 hardware signing is the compatible reference-device path in progress.

**Honest limits**

- **Shipping now:** L1 emulated Ed25519 software key; Git post-commit hooks; PyPI `matrixscroll` 0.2.1+
- **In progress:** SSX360 SE050 hardware provider; YubiKey PKCS#11 bridge
- **Not:** IAM, sandbox, prompt-injection filter, or agent runtime

- 📜 **Spec:** [`SPEC.md`](SPEC.md) — wire format, canonical encoding, document types.
- 📋 **Commit envelope schema:** [`schemas/commit-envelope.v1.json`](schemas/commit-envelope.v1.json)
- 📄 **Whitepaper:** [`docs/WHITEPAPER.md`](docs/WHITEPAPER.md) — why Git commits, implementation guide.
- 🛡 **Agentic AI controls:** [`docs/AGENTIC_AI_SECURITY.md`](docs/AGENTIC_AI_SECURITY.md)
  maps Matrix Scroll to the joint *Careful Adoption of Agentic AI Services* guidance.
- 🔐 **Algorithm:** Ed25519 (RFC 8032). Private keys are never exposed by the SDK API.
- 🧪 **Conformance vectors:** [`vectors/`](vectors/) — for non-Python implementations.
- 🌐 **Site:** <https://matrixscroll.com>
- 🔧 **Reference device:** [SSX360](https://matrixscroll.com/device) (NXP SE050 hardware path in progress).

## Agent provenance for Git commits

```bash
pip install "matrixscroll>=0.2.1"
matrixscroll hook-install

export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=cursor
git commit -m "feat: agent-assisted change"

matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

See [`docs/quickstart-git.md`](docs/quickstart-git.md) and run
[`examples/demo/agent-commit-demo.sh`](examples/demo/agent-commit-demo.sh).

### CI verify

```yaml
- uses: SSX360/matrixscroll-verify-action@v1
  with:
    manifest: examples/agentic_ai_evidence_manifest.signed.json
    matrixscroll-version: "0.2.2"
    require-mode: emulated
```

Policy flags (`--require-mode`, `--trusted-keys`) ship in **0.2.2+**.

## Quickstart (Python API)

```bash
pip install "matrixscroll>=0.2.1"
```

```python
import matrixscroll

print(matrixscroll.status())
# {'schema': 'matrixscroll.identity.v1', 'available': True,
#  'mode': 'emulated', 'device_id': 'MS-A3F2-9C81', ...}

# Sign a release manifest, commit envelope, evidence pack, or SBOM
signed = matrixscroll.sign_manifest({"release": "v1.0.0", "artifacts": [...]})

assert matrixscroll.verify_manifest(signed)
```

## CLI

```bash
$ matrixscroll status
{
  "available": true,
  "device_id": "MS-A3F2-9C81",
  "mode": "emulated",
  "public_key": "...",
  "schema": "matrixscroll.identity.v1"
}

$ matrixscroll sign release.json > release.signed.json
$ matrixscroll verify release.signed.json
{"device_id": "MS-A3F2-9C81", "mode": "emulated", "ok": true, "signed_at": "..."}
```

`matrixscroll verify` exits **0** on a valid signature, **2** on any failure
(tampered manifest, missing signature block, wrong schema/algorithm, mismatched
device id, malformed public key, unreadable file). Pipe it from CI without
parsing the output.

## How it works

```
   your IDE / agent / CI
            │
            │  commit envelope, release manifest, evidence pack, SBOM
            ▼
   matrixscroll.sign_manifest(...)  /  post-commit hook
            │
            │  canonical JSON  (sorted keys, ASCII-escaped, no NaN,
            │                   signature block excluded from input)
            ▼
   IdentityProvider          ──►  Ed25519 signature
   (L1 emulated today,
    SSX360 / SE050 roadmap)
            │
            ▼
   signed document  ──►  matrixscroll.verify_manifest(...)
                         (anyone, anywhere, offline)
```

Switch providers with `MATRIXSCROLL_MODE`. Hardware mode reports unavailable
until the SE050 transport ships.

## Compliance levels

| Level | Provider | Backed by | Status |
| ----- | -------- | --------- | ------ |
| **L1** Emulated | `EmulatedProvider` | Software key, file-backed (0600) | ✅ Shipping |
| **L2** Hardware | `HardwareProvider` | NXP SE050 secure element (SSX360) | 🛠 In progress |
| **L3** Attested | future | L2 + remote attestation | 🗺 Roadmap |

`status()` exposes the active level via the `mode` and `available` fields.

## Storage and trust boundaries

- Emulated key store: `~/.matrixscroll/device.json`
  (override with `MATRIXSCROLL_HOME`).
- The directory is created `0700`; the seed file is opened `0600` with
  `O_CREAT|O_EXCL` so the private seed is never momentarily world-readable.
- A corrupt or truncated store **fails loud** (`IdentityError`) rather than
  silently minting a fresh identity.
- The planned hardware path holds nothing private on disk — the seed is sealed
  in the secure element.

## Reference implementation, not the only one

Matrix Scroll is a protocol. This Python package is the reference. We welcome
implementations in Rust, Go, TypeScript, and embedded C — run them against
[`vectors/`](vectors/) to self-certify. See `CONTRIBUTING.md`.

## Agentic AI guidance proof

The repo includes a machine-readable control matrix at
[`controls/agentic_ai_controls.json`](controls/agentic_ai_controls.json), an
example bounded-agent evidence manifest at
[`examples/agentic_ai_evidence_manifest.json`](examples/agentic_ai_evidence_manifest.json),
and executable checks in `tests/test_agentic_guidance.py`.

## License

- Code: **Apache-2.0** (`LICENSE`).
- Specification text (`SPEC.md`, `vectors/`): **CC0 1.0** — public domain.

## Security

See [`SECURITY.md`](SECURITY.md). Report vulnerabilities privately to
**security@matrixscroll.com** or via a GitHub Security Advisory.
