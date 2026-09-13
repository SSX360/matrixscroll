# Trust boundaries

Matrix Scroll signs claims about commits and actions. This page states what the signature proves and where the system still depends on operator policy.

## What a signed envelope proves

An envelope proves that the holder of a specific Ed25519 private key signed a specific actor, tool, scope, and commit or action. Verification also shows whether those signed bytes changed afterward.

The `actor_type` field is a declaration. Bind the public key to an approved actor before treating that declaration as authorization.

## What remains outside the proof

- Matrix Scroll does not inspect whether code is safe. Keep scanners, review, and branch protection.
- Matrix Scroll records a declared agent scope. It does not enforce that scope.
- Matrix Scroll does not reproduce a build. Use artifact attestations for build provenance.
- Matrix Scroll does not replace identity and access management, sandboxing, prompt filtering, or an agent runtime.

## File-backed provider boundary

The file-backed provider stores its private seed at `~/.matrixscroll/device.json`, or under `MATRIXSCROLL_HOME`. The directory uses mode `0700`, and the seed file uses mode `0600` with `O_CREAT|O_EXCL`.

Anyone with host root or the operator account can read that seed. The provider detects later record changes, but host compromise can still produce a new valid signature.

## SSX360 USB signer boundary

The SSX360 USB signer moves the Ed25519 private key into an NXP SE050 secure element. The SE050 creates the key pair and returns the public key and signature through the RP2350 USB bridge without sending the private key to the host.

SSX360 produces the signer and supplies completed units through [SSX360 contact](https://ssx360.com/contact). PyPI distributes `matrixscroll[hardware]`, which provides the host transport. The physical device is not a PyPI artifact or a self-service listing.

Hardware key custody does not identify the operator. A deployment still needs trusted-key registration, physical access control, revocation, and offboarding.

## Stable verifier contract

The public contract is Ed25519 over canonical manifest bytes. The same verifier checks signatures from the file-backed provider and the SSX360 signer. Ports can run [`vectors/`](https://github.com/SSX360/matrixscroll/tree/main/vectors/) to check compatibility.

Software signers may attach ML-DSA or SLH-DSA overlays through `matrixscroll[pqc]`. These overlays do not replace the required Ed25519 `signature` block.

## Compliance boundary

Matrix Scroll maps evidence to DORA, PCI DSS 4.0, the US Treasury FS-AI RMF, the NIST SSDF, and EU AI Act Article 12 record-keeping readiness. This is evidence mapping, not a certification claim or an audit opinion.
