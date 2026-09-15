# Rust verifiers

Shipping and bar language for the Matrix Scroll Rust track. Hold claims to
[`docs/explanation/gold-standard.md`](../docs/explanation/gold-standard.md).

## Shipping now

| Surface | Status | Notes |
| --- | --- | --- |
| `matrixscroll-verify` crate | Start | Domain-separated ledger hash links, Ed25519 verify over message bytes, CLI `verify --envelope` |
| `cargo test` in CI | Optional workflow | [`.github/workflows/rust-verify.yml`](../.github/workflows/rust-verify.yml) runs `cargo test` only |
| Deterministic JSON walk | Best-effort | Sorted object keys, compact separators, ASCII-style escapes; full RFC 8785 remains next |
| Python conformance vectors | Authoritative | When Rust and Python diverge on encoding edge cases, treat `vectors/` plus `tools/independent_verify.py` as the reference |

## Bar (not claimed until present)

| Surface | Status | Notes |
| --- | --- | --- |
| Kani proofs of selected invariants | Optional local | Domain-hash digest length; empty chain is `Consistent`. Run `cargo kani` when Kani is installed. Not a substitute for a full proof of the verifier |
| Lean 4 / F\* extracted verifier | Bar | Machine-checked core with an extracted executable remains the gold-standard bar per `AGENTS.md` and `formal/README.md`. Do not write copy that implies that extraction ships today |

## Layout

```text
rust/
  Cargo.toml                 workspace root
  README.md                  this file
  matrixscroll-verify/       library + CLI + optional Kani proofs
```

## Quick start

```bash
cd rust
cargo test -p matrixscroll-verify
cargo run -p matrixscroll-verify --bin verify -- --envelope ../vectors/valid_simple.json
```

Kani (optional, not required for CI):

```bash
# after installing cargo-kani
cd rust/matrixscroll-verify
cargo kani
```

See [`matrixscroll-verify/README.md`](matrixscroll-verify/README.md) for crate
details.
