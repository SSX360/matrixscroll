# Matrix Scroll

Signed provenance for agent-assisted Git commits with offline verification.

Matrix Scroll is a cryptographic evidence layer for Git. When an agent, CI
workflow, or human operator produces a commit, a signed commit envelope can
record the actor, tool, and optional bounded scope. Anyone can verify that
envelope locally, in CI, or in the browser without trusting the editor session
that produced it.

The reference SDK ships an emulated Ed25519 root of trust today. The SSX360 /
NXP SE050 hardware path is the compatible next trust layer and remains in
progress.

## Honest limits

- Shipping now: `matrixscroll==0.2.5`, Git post-commit hooks,
  `matrixscroll envelope-verify`, Scroll Gate PR verification, browser
  verifier, and the GitHub Action.
- In progress: SSX360 SE050 hardware provider, YubiKey PKCS#11 bridge, and
  transparency-log integrations.
- Not: IAM, sandboxing, prompt filtering, or an agent runtime.

## Quickstart

```bash
pip install "matrixscroll==0.2.5"
matrixscroll hook-install

export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-cli
git commit -m "feat: agent-assisted change"

matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

See [`docs/quickstart-git.md`](docs/quickstart-git.md) and run
[`examples/demo/agent-commit-demo.sh`](examples/demo/agent-commit-demo.sh).

## CI verify

### Single manifest

```yaml
- uses: SSX360/matrixscroll-verify-action@v1
  with:
    manifest: examples/agentic_ai_evidence_manifest.signed.json
    matrixscroll-version: "0.2.5"
    require-mode: emulated
```

### Scroll Gate for a PR commit range

Publish envelopes to git notes before review:

```bash
matrixscroll envelope-publish-notes --base origin/main --head HEAD
git push origin refs/notes/matrixscroll
```

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
- uses: SSX360/matrixscroll-verify-action@v1
  with:
    head-ref: ${{ github.event.pull_request.head.sha }}
    base-ref: ${{ github.event.pull_request.base.sha }}
    source: notes
    matrixscroll-version: "0.2.5"
    summary-output: provenance-summary.json
```

Policy flags such as `--require-mode`, `--trusted-keys`, and actor or
delegation checks ship in the `0.2.x` line. Public examples in this README pin
the current PyPI release, `0.2.5`.

## Why it is different from Sigstore

Sigstore, GitHub artifact attestations, and SLSA answer "what was built in CI?"
Matrix Scroll answers "who signed this commit before push?" The systems are
complementary: Matrix Scroll signs commit envelopes at commit time, while
artifact-attestation systems sign build outputs later in the delivery chain.

## Public proof links

- Browser verifier: <https://matrixscroll.com/verify/>
- Compare page: <https://matrixscroll.com/compare/>
- Specification: [`SPEC.md`](SPEC.md)
- Commit envelope schema: [`schemas/commit-envelope.v1.json`](schemas/commit-envelope.v1.json)
- Whitepaper: [`docs/WHITEPAPER.md`](docs/WHITEPAPER.md)
- Conformance vectors: [`vectors/`](vectors/)
- GitHub Action: <https://github.com/SSX360/matrixscroll-verify-action>
- Agentic AI controls: [`docs/AGENTIC_AI_SECURITY.md`](docs/AGENTIC_AI_SECURITY.md)
- Site: <https://matrixscroll.com>
- Reference device path: <https://matrixscroll.com/device/>

## Python API

```bash
pip install "matrixscroll==0.2.5"
```

```python
import matrixscroll

print(matrixscroll.status())
# {'schema': 'matrixscroll.identity.v1', 'available': True,
#  'mode': 'emulated', 'device_id': 'MS-A3F2-9C81', ...}

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

`matrixscroll verify` exits `0` on a valid signature and `2` on failure
(tampered manifest, missing signature block, wrong schema or algorithm,
mismatched device ID, malformed public key, unreadable file).

## How it works

```text
your IDE / agent / CI
         |
         |  commit envelope, release manifest, evidence pack, SBOM
         v
matrixscroll.sign_manifest(...)  /  post-commit hook
         |
         |  canonical JSON (sorted keys, ASCII-escaped, no NaN,
         |  signature block excluded from input)
         v
IdentityProvider          -->  Ed25519 signature
(L1 emulated today,
 SSX360 / SE050 roadmap)
         |
         v
signed document  -->  matrixscroll.verify_manifest(...)
                      (anyone, anywhere, offline)
```

Switch providers with `MATRIXSCROLL_MODE`. Hardware mode remains unavailable
until the SE050 transport ships.

## Compliance levels

| Level | Provider | Backed by | Status |
| ----- | -------- | --------- | ------ |
| L1 Emulated | `EmulatedProvider` | Software key, file-backed (0600) | Shipping |
| L2 Hardware | `HardwareProvider` | NXP SE050 secure element (SSX360) | In progress |
| L3 Attested | future | L2 + remote attestation | Roadmap |

`status()` exposes the active level via the `mode` and `available` fields.

## Storage and trust boundaries

- Emulated key store: `~/.matrixscroll/device.json`
  (override with `MATRIXSCROLL_HOME`).
- The directory is created `0700`; the seed file is opened `0600` with
  `O_CREAT|O_EXCL` so the private seed is never momentarily world-readable.
- A corrupt or truncated store fails loud (`IdentityError`) rather than
  silently minting a fresh identity.
- The planned hardware path holds nothing private on disk. The seed is sealed
  inside the secure element.

## Reference implementation

Matrix Scroll is a protocol. This Python package is the reference
implementation. Implementations in Rust, Go, TypeScript, and embedded C can use
[`vectors/`](vectors/) to self-certify. See `CONTRIBUTING.md`.

## Agentic AI guidance proof

The repo includes a machine-readable control matrix at
[`controls/agentic_ai_controls.json`](controls/agentic_ai_controls.json), an
example bounded-agent evidence manifest at
[`examples/agentic_ai_evidence_manifest.json`](examples/agentic_ai_evidence_manifest.json),
and executable checks in `tests/test_agentic_guidance.py`.

## License

- Code: Apache-2.0 (`LICENSE`)
- Specification text (`SPEC.md`, `vectors/`): CC0 1.0

## Security

See [`SECURITY.md`](SECURITY.md). Report vulnerabilities privately to
`security@matrixscroll.com` or via a GitHub Security Advisory.
