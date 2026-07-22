# Matrix Scroll Public Roadmap

_Published: June 21, 2026 · Updated: July 21, 2026_

This roadmap is intentionally narrow. Matrix Scroll earns trust by stabilizing
what ships now before widening the story.

## Baseline on June 21, 2026

- GitHub: early public repo, product-first docs, and offline verification
- Current public release: `matrixscroll==0.6.1`
- Public trust contract: pure Ed25519 over canonical manifest bytes
- Hardware path: SSX360 SE050 reference implementation in progress

## Update — July 21, 2026 (L2 Hardware prototype)

- Pico 2 W / RP2350 USB CDC + CYW43 LED + GMT130 ST7789 pixels locked
- SE050 M1 signing PoC remains bench-validated (contractor firmware); display
  bring-up UF2 keeps live SE050 fail-closed until NXP backend restore
- Public claim: **Prototype (bench)** — not GA

## Next 7 days

- keep install pins on `matrixscroll==0.6.1` unless a docs-only `0.6.1` publish
- align site, README, action docs, and PyPI around one honest hardware ladder
- remove broken links and stale release drift from public copy

## Next 30 days

- restore NXP Plug & Trust on the bring-up UF2 for live `pubkey`/`sign`
- physical-approval gate (button/touch) after continuity
- secure one public adopter, pilot repo, or testimonial
- publish rollout criteria for external Ed25519-capable key backends

## What will stay stable

- commit-envelope schema
- CLI exit-code contract
- offline verification behavior

## What will raise trust fastest

1. one public user proof asset
2. stable release cadence
3. clean docs and reproducible verification
4. honest hardware status (prototype ≠ GA)

Matrix Scroll will earn trust by making those signals obvious, not by claiming
hardware GA before the NXP backend is restored on the shipping UF2.
