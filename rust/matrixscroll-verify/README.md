# matrixscroll-verify

Minimal Rust verifier for Matrix Scroll ledger chain checks and Ed25519
signature verification. This is a language-port start, not a claim that Rust
replaces the Python reference (`matrixscroll==0.10.0`).

## What it ships

- `canonical`: recursive sorted-key compact JSON (best-effort Python/SPEC §4
  alignment). Full RFC 8785 remains next. Python `vectors/` and
  `tools/independent_verify.py` stay authoritative when encodings disagree.
- `ledger`: `GENESIS` prev-hash, domain-separated SHA-256 with tags
  `matrixscroll/v1/record\0` (and leaf/node/epoch), `verify_chain` returning
  `Consistent` / `Inconsistent` / `Indeterminate`.
- `verify_ed25519`: verify a signature over a message with a raw 32-byte public
  key.
- CLI: `verify --envelope path.json` prints a JSON verdict object.

## Build and test

From the `rust/` workspace:

```bash
cargo test -p matrixscroll-verify
cargo run -p matrixscroll-verify --bin verify -- --envelope ../vectors/valid_simple.json
```

## Kani (optional)

Proofs live in `tests/ledger_kani.rs` behind `#[cfg(kani)]`:

- domain-separated hash digest length is 32 bytes
- empty chain is `Consistent`

When [Kani](https://model-checking.github.io/kani/) is installed:

```bash
cargo kani
```

CI (`.github/workflows/rust-verify.yml`) runs `cargo test` only and skips Kani.
Absence of a green Kani job is not a failure of the shipping crate.

## Verification boundaries

- Fail closed: three-valued verdicts only.
- No silent pass on missing evidence.
- Lean 4 / F\* extraction remains the bar, not a shipping claim.
- Naming NIST or SSDF here is evidence mapping, not a certification claim.
