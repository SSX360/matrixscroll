//! Matrix Scroll Rust verifier library (ledger + Ed25519).
//!
//! Shipping start for a second-language verifier. Lean 4 / F\* extraction remains
//! the bar. Python conformance vectors stay authoritative for canonical bytes.

pub mod canonical;
pub mod ledger;
pub mod verify_ed25519;

pub use canonical::{canonical_bytes, sha256_hex, CanonicalError};
pub use ledger::{
    compute_record_hash, domain_separated_hash, domain_separated_hash_hex, verify_chain,
    verify_chain_json, ChainVerdict, LedgerRecord, GENESIS_PREV_HASH, TAG_EPOCH, TAG_LEAF,
    TAG_NODE, TAG_RECORD,
};
pub use verify_ed25519::{verify_ed25519, VerifyError};
