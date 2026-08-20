# Matrix Scroll public roadmap

Published June 21, 2026. Updated August 11, 2026.

Matrix Scroll stabilizes the verifier contract before adding new signing providers or hosted features.

## Current release

- PyPI release: `matrixscroll==0.7.0`
- MCP transport: stdio through `matrixscroll-mcp`
- Public trust contract: Ed25519 over canonical manifest bytes
- Software provider: file-backed key under `MATRIXSCROLL_HOME`
- Hardware provider: SSX360 RP2350 and SE050 USB signer, supplied through direct inquiry

## Completed hardware work

- The RP2350 USB CDC bridge carries `GEN_KEY`, `GET_PUBKEY`, and `SIGN` requests.
- The SE050 creates a non-exportable Ed25519 key and returns detached signatures.
- The GMT130 display and status controls are assembled with the signer.
- `matrixscroll[hardware]` connects the Python SDK and MCP server to the USB CDC port.

## Next work

- Publish device provisioning and trusted-key registration instructions.
- Add physical approval policy for deployments that require user presence.
- Define revocation and offboarding records for a replaced signer.
- Evaluate external Ed25519-capable key backends against the same verifier contract.

## Stable contracts

- Commit-envelope schema
- CLI exit codes
- Offline verification behavior
- MCP tool names for the `0.7.x` release line

## Release rule

Every release keeps `pyproject.toml`, `matrixscroll.__version__`, install examples, the GitHub release, and PyPI metadata on the same version. PyPI publishes through `.github/workflows/publish.yml` with Trusted Publishing.
