# Pre-0.9 history signed-statement template

This file is the **text of a statement** an organisation can sign over a digest
of pre-0.9 git history. It is a template, not a signed artifact. The public
policy for which history is published lives in
[`PUBLIC_HISTORY.md`](../PUBLIC_HISTORY.md).

## Statement (sign over the digest below)

```text
Matrix Scroll pre-0.9 history acknowledgement

I acknowledge that:

1. The public git history for SSX360/matrixscroll was reset so that published
   trees match the supported product line described in PUBLIC_HISTORY.md.
2. Pre-0.7 releases are unsupported. Supported installs are matrixscroll==0.7.0
   and matrixscroll==0.9.0 on PyPI (and the 0.9.x development tree).
3. The digest below covers the pre-0.9 archive object set my organisation
   retains offline (or attests as unavailable). It is not a claim that the
   public remote still serves those objects.

Archive label: <ORG_LABEL>
Archive digest (SHA-256 hex): <DIGEST_OF_TAR_OR_BUNDLE>
Statement drafted at (UTC): <RFC3339>
Signer role: <security-officer | release-engineer | other>
```

## How to produce the digest

1. Assemble the offline archive (tarball, mirror bundle, or empty placeholder
   with an explicit `unavailable` marker file).
2. `sha256sum` (or equivalent) the archive bytes.
3. Substitute `<DIGEST_OF_TAR_OR_BUNDLE>` above.
4. Sign the filled statement with your org key (Ed25519 envelope or detached
   signature). Matrix Scroll does not require a specific signature format for
   this organisational acknowledgement.

## Evidence mapping hedge

This template supports supply-chain review of history continuity. It is an
**evidence mapping, not a certification claim**, and it does not assert NIST,
SSDF, or other framework compliance.
