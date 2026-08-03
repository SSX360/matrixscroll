# Trust boundaries and the hardware roadmap

This page states what Matrix Scroll can prove, what it cannot, and how far the
hardware path actually got. It is written to be quotable by someone trying to
catch us overclaiming.

## What a commit envelope proves

An envelope proves that the holder of a specific Ed25519 private key asserted a
specific actor, tool, and scope for a specific commit, and that the assertion has
not been altered since.

That is the whole claim. It is narrow on purpose.

## What it does not prove

- **Not that the actor is who they say.** In emulated mode the key sits in a file
  the operator can read. Anyone with that file can sign as that identity. The
  envelope binds an assertion to a key, not a key to a human.
- **Not that the code is safe.** Matrix Scroll has no opinion on the diff.
  Scanners, review, and branch protection remain necessary.
- **Not that the build is reproducible.** That is a different question, answered
  by Sigstore, SLSA, and artifact attestations. See
  [Why commit-time provenance](commit-time-vs-artifact-time.md).
- **Not that an agent stayed in scope.** The envelope records a declared scope.
  It does not enforce one. Matrix Scroll is not a sandbox, an IAM system, a
  prompt filter, or an agent runtime.

## The emulated-mode trust boundary

The private seed lives at `~/.matrixscroll/device.json`, or wherever
`MATRIXSCROLL_HOME` points. The directory is created `0700`. The seed file is
opened `0600` with `O_CREAT|O_EXCL`, so it is never momentarily world-readable.
A corrupt or truncated store raises `IdentityError` rather than silently minting
a fresh identity, because a silently rotated identity is worse than a loud
failure.

Anyone with host root, or with the operator's account, can read the seed. That
is the boundary. Emulated mode raises the cost of forging attribution; it does
not make forging impossible.

## The hardware path, stated honestly

Hardware was intended to close that boundary by sealing the seed in a secure
element so the host cannot export it. Here is exactly how far it got.

| Component | Actual status as of July 2026 |
| --- | --- |
| NXP SE050 M1 signing | Proof of concept accepted on contractor firmware. Bench only. |
| Pico 2 W / RP2350 + GMT130 display bring-up | Prototype locked 2026-07-21. Bench only. |
| Live SE050 signing on the display bring-up UF2 | Fail-closed. `pubkey` and `sign` do not work pending an NXP Plug and Trust restore. |
| USB CDC host transport | Ships in the Python package. |
| Generally available hardware product | Does not exist. |

Two things follow.

First, any sentence describing hardware as validated, shipping, or available is
wrong. The correct phrasing is "bench prototype, not generally available", and
the display bring-up cannot currently sign at all.

Second, hardware is deprioritized. The strategy does not depend on it. Treating
the hardware roadmap as imminent misrepresents both the engineering state and
the commercial plan, and for a vendor selling independent assessments that is a
self-inflicted wound.

## Why the verifier contract is the thing that matters

The public contract is pure Ed25519 over canonical manifest bytes. A verifier
written against `vectors/` today keeps working whether the signer was a software
key, a secure element, or an implementation nobody has written yet. That
stability is what makes the protocol worth adopting before the hardware exists,
and it is why external key backends stay out of the mainline until they can sign
the same canonical bytes.

Software signers may attach ML-DSA or SLH-DSA overlays via `matrixscroll[pqc]`.
Those overlays are additive: they never change the required `signature` block,
so a verifier that ignores them still succeeds.

## Compliance boundary

Matrix Scroll maps to and produces evidence for DORA, PCI DSS 4.0, the US
Treasury FS-AI RMF, the NIST SSDF, and EU AI Act Article 12 record-keeping
readiness. That is evidence mapping, not a certification claim, and not an audit
opinion. No control here is "required by" any of those frameworks. Nothing in
this repository certifies anything.
