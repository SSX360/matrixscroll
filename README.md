# Matrix Scroll

**Open protocol for hardware-signed AI-assisted code.**

Every AI-generated change in your IDE gets cryptographically signed by an
Ed25519 key sealed in a hardware root of trust. Anyone can verify the result
offline with a public key and one command.

- 📜 **Spec:** [`SPEC.md`](SPEC.md) — wire format, canonical encoding, schemas.
- 🛡 **Agentic AI controls:** [`docs/AGENTIC_AI_SECURITY.md`](docs/AGENTIC_AI_SECURITY.md)
  maps Matrix Scroll to the joint *Careful Adoption of Agentic AI Services* guidance.
- 🔐 **Algorithm:** Ed25519 (RFC 8032). Keys never leave the provider.
- 🧪 **Conformance vectors:** [`vectors/`](vectors/) — for non-Python implementations.
- 🌐 **Site:** <https://matrixscroll.com>
- 🔧 **Reference device:** [SSX360](https://ssx360-3d-pipeline.vercel.app/) (NXP SE050).

```bash
pip install matrixscroll
```

## Quickstart

```python
import matrixscroll

# What identity is active on this machine?
print(matrixscroll.status())
# {'schema': 'matrixscroll.identity.v1', 'available': True,
#  'mode': 'emulated', 'device_id': 'MS-A3F2-9C81', ...}

# Sign anything (a release manifest, a commit envelope, a SBOM, an evidence pack)
signed = matrixscroll.sign_manifest({"release": "v1.0.0", "artifacts": [...]})

# Verify, anywhere, offline
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
            │  manifest (release, commit, evidence pack, SBOM, anything)
            ▼
   matrixscroll.sign_manifest(...)
            │
            │  canonical JSON  (sorted keys, ASCII-escaped, no NaN,
            │                   signature block excluded from input)
            ▼
   IdentityProvider          ──►  Ed25519 signature
   (Emulated today,
    SSX360 / SE050 tomorrow)
            │
            ▼
   signed manifest  ──►  matrixscroll.verify_manifest(...)
                         (anyone, anywhere, offline)
```

The same Python API serves the local software emulator and the physical
SSX360 device. Switch with the `MATRIXSCROLL_MODE` environment variable.

## Compliance levels

| Level | Provider | Backed by | Status |
| ----- | -------- | --------- | ------ |
| **L1** Emulated | `EmulatedProvider` | Software key, file-backed (0600) | ✅ Shipping |
| **L2** Hardware | `HardwareProvider` | NXP SE050 secure element (SSX360) | 🛠 Stage-0 prototype |
| **L3** Attested | future | L2 + remote attestation | 🗺 Roadmap |

`status()` exposes the active level via the `mode` and `available` fields so
read-only dashboards can render before the hardware path is wired.

## Storage and trust boundaries

- Emulated key store: `~/.matrixscroll/device.json`
  (override with `MATRIXSCROLL_HOME`).
- The directory is created `0700`; the seed file is opened `0600` with
  `O_CREAT|O_EXCL` so the private seed is never momentarily world-readable and
  a race cannot silently clobber an existing key store.
- A corrupt or truncated store **fails loud** (`IdentityError`) rather than
  silently minting a fresh identity. Identity rotation is an explicit operation.
- The hardware path holds nothing private on disk — the seed is sealed in the
  secure element.

## Reference implementation, not the only one

Matrix Scroll is a protocol. This Python package is the reference. We welcome
implementations in Rust, Go, TypeScript, and embedded C — run them against
[`vectors/`](vectors/) to self-certify. See `CONTRIBUTING.md`.

## Agentic AI guidance proof

The repo includes a machine-readable control matrix at
[`controls/agentic_ai_controls.json`](controls/agentic_ai_controls.json), an
example bounded-agent evidence manifest at
[`examples/agentic_ai_evidence_manifest.json`](examples/agentic_ai_evidence_manifest.json),
and executable checks in `tests/test_agentic_guidance.py`. These prove each
claim maps to repo evidence and that signed agent scope changes fail verify.

## License

- Code: **Apache-2.0** (`LICENSE`).
- Specification text (`SPEC.md`, `vectors/`): **CC0 1.0** — public domain.

## Security

See [`SECURITY.md`](SECURITY.md). Report vulnerabilities privately to
**security@matrixscroll.com** or via a GitHub Security Advisory.
