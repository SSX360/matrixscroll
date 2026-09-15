//! Optional Kani proofs for ledger invariants.
//!
//! These modules compile under normal `cargo test` as empty (cfg(kani) off).
//! When Kani is installed, run:
//!
//! ```text
//! cargo kani
//! ```
//!
//! CI runs `cargo test` only and does not require Kani.

#![cfg(kani)]

use matrixscroll_verify::{
    domain_separated_hash, verify_chain, ChainVerdict, TAG_RECORD,
};

#[kani::proof]
fn proof_domain_hash_length_is_32_bytes() {
    let tag = TAG_RECORD;
    // Symbolic data length bounded for the harness.
    let len: usize = kani::any();
    kani::assume(len <= 64);
    let mut data = vec![0u8; len];
    for i in 0..len {
        data[i] = kani::any();
    }
    let digest = domain_separated_hash(tag, &data);
    assert_eq!(digest.len(), 32);
}

#[kani::proof]
fn proof_empty_chain_is_consistent() {
    let records: [matrixscroll_verify::LedgerRecord; 0] = [];
    assert_eq!(verify_chain(&records), ChainVerdict::Consistent);
}
