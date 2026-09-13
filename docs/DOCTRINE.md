# Publishing doctrine: SSX360 and Matrix Scroll

This document defines the public claims and technical boundaries shared by the
Matrix Scroll package, matrixscroll.com, PyPI, GitHub, and SSX360.

## The thesis

Software changes code, infrastructure, and business records at machine speed.
Matrix Scroll signs a declared authorization record for those actions and lets
reviewers verify the record offline. SSX360 maintains the protocol, produces the
USB signer, and delivers scoped cybersecurity services.

## Rules

### 1. Describe evidence, not trust

Matrix Scroll verifies that signed bytes match and correspond to a key. It does
not establish who was authorized to use that key. Trusted-key policy, access
control, key custody, revocation, and review remain deployment responsibilities.

### 2. Keep the protocol portable

The envelope format, schemas, conformance vectors, and verifier must work
without a Matrix Scroll account. Integrations may target GitHub, GitLab,
Forgejo, Gitea, or other systems, but the wire format must not depend on one
platform.

### 3. Make every claim checkable

Software signing is described as software signing. The completed SSX360 USB
signer is described as an RP2350 and NXP SE050 device supplied through direct
contact. PyPI distributes the host software, not the physical device. Compliance
references are evidence mappings, not certifications.

### 4. Apply the same controls to releases

Release examples use explicit version pins. PyPI artifacts are built from the
tagged repository state and published through Trusted Publishing with
attestations. The changelog, support policy, action defaults, site, and package
metadata must identify the same current release.

### 5. Separate open software from commercial delivery

Matrix Scroll remains Apache-2.0 software with CC0 specification text and
vectors. SSX360 earns revenue from cybersecurity products and scoped services,
including the physical USB signer and compliance-aligned assessment work.

## Publication check

Before publishing, confirm that:

1. The capability exists in the referenced release or deployed service.
2. The evidence and limitations appear beside the claim.
3. Version numbers and install commands agree across every public surface.
4. Hardware availability distinguishes host software from physical units.
5. Standards references do not imply certification or third-party validation.
