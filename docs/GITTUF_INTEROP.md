# gittuf Interop Design

## Goal

Compose Matrix Scroll commit envelopes with **gittuf** repository metadata and Reference State Log (RSL) integrity without replacing either system.

## Division of labor

| System | Proves |
|--------|--------|
| gittuf | Repository history integrity, protected refs, multi-party signing on Git metadata |
| Matrix Scroll | Agent/human declared origin on commits, offline Ed25519 verify, assessor export |

## Interop shape

1. Matrix Scroll envelope attaches to commit (notes/bundle transport).
2. gittuf RSL records ref updates and policy for the same repository.
3. Assessor export references both:
   - envelope signature validity
   - gittuf policy satisfaction for the protected branch

## Implementation phases

| Phase | Deliverable |
|-------|-------------|
| P1 | Design doc + sample repo showing envelope + gittuf side by side |
| P2 | CI example verifying both gates on protected `main` |
| P3 | Evidence pack section linking gittuf attestation IDs |

## OpenSSF alignment

- Target WG: Supply Chain Integrity
- Reference path: gittuf sandbox → incubating (Jan 2024 → Jun 2025)
- Matrix Scroll participates in WG; protocol IP transfer decision tracked separately in `OPENSSF_SANDBOX_DECISION.md`

## Non-goals

- Replacing gittuf RSL with Matrix Scroll envelopes
- Claiming gittuf or OpenSSF endorsement before contribution lands
