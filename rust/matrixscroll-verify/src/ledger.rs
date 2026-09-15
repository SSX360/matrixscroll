//! Hash-linked ledger verification matching `matrixscroll.ledger` (SPEC §12).
//!
//! Domain tags and genesis sentinel mirror the Python SDK. Evidence mapping
//! only; not a certification claim against NIST IR 8536 or related guidance.

use crate::canonical::encode_value;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

/// Domain-separation tags (NUL-terminated contexts).
pub const TAG_RECORD: &[u8] = b"matrixscroll/v1/record\0";
pub const TAG_LEAF: &[u8] = b"matrixscroll/v1/leaf\0";
pub const TAG_NODE: &[u8] = b"matrixscroll/v1/node\0";
pub const TAG_EPOCH: &[u8] = b"matrixscroll/v1/epoch\0";

/// Genesis previous-hash sentinel (64 zero hex digits).
pub const GENESIS_PREV_HASH: &str =
    "0000000000000000000000000000000000000000000000000000000000000000";

pub const LEDGER_RECORD_SCHEMA: &str = "matrixscroll.ledger_record.v1";

/// Three-valued fail-closed verdict (exit codes 0 / 1 / 2).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ChainVerdict {
    Consistent,
    Indeterminate,
    Inconsistent,
}

impl ChainVerdict {
    pub fn label(self) -> &'static str {
        match self {
            ChainVerdict::Consistent => "CONSISTENT",
            ChainVerdict::Indeterminate => "INDETERMINATE",
            ChainVerdict::Inconsistent => "INCONSISTENT",
        }
    }

    pub fn exit_code(self) -> i32 {
        match self {
            ChainVerdict::Consistent => 0,
            ChainVerdict::Indeterminate => 1,
            ChainVerdict::Inconsistent => 2,
        }
    }
}

/// SHA-256(tag || data) as a 32-byte digest.
pub fn domain_separated_hash(tag: &[u8], data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(tag);
    hasher.update(data);
    hasher.finalize().into()
}

/// SHA-256(tag || data) as lowercase hex (Python `domain_separated_hash`).
pub fn domain_separated_hash_hex(tag: &[u8], data: &[u8]) -> String {
    hex_encode(&domain_separated_hash(tag, data))
}

fn hex_encode(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push(HEX[(b >> 4) as usize] as char);
        s.push(HEX[(b & 0xf) as usize] as char);
    }
    s
}

/// One ledger record (dict form).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerRecord {
    pub schema: Option<String>,
    pub index: u64,
    pub prev_hash: String,
    pub payload: Value,
    pub record_hash: String,
    #[serde(default)]
    pub created_at: Option<String>,
}

/// Recompute record hash under TAG_RECORD.
pub fn compute_record_hash(index: u64, prev_hash: &str, payload: &Value) -> Result<String, String> {
    let body = json!({
        "index": index,
        "payload": payload,
        "prev_hash": prev_hash,
        "schema": LEDGER_RECORD_SCHEMA,
    });
    let encoded = encode_value(&body).map_err(|e| e.to_string())?;
    Ok(domain_separated_hash_hex(TAG_RECORD, encoded.as_bytes()))
}

/// Verify hash links, contiguous indices, and recomputed record hashes.
///
/// Empty chain is `Consistent` (vacuous). Bad shape yields `Indeterminate`.
pub fn verify_chain(records: &[LedgerRecord]) -> ChainVerdict {
    if records.is_empty() {
        return ChainVerdict::Consistent;
    }

    let mut expected_prev = GENESIS_PREV_HASH.to_string();
    for (i, record) in records.iter().enumerate() {
        if record.index != i as u64 {
            return ChainVerdict::Inconsistent;
        }
        if record.prev_hash != expected_prev {
            return ChainVerdict::Inconsistent;
        }
        match compute_record_hash(record.index, &record.prev_hash, &record.payload) {
            Ok(expected) if expected == record.record_hash => {}
            Ok(_) => return ChainVerdict::Inconsistent,
            Err(_) => return ChainVerdict::Indeterminate,
        }
        expected_prev = record.record_hash.clone();
    }
    ChainVerdict::Consistent
}

/// Parse a JSON array of ledger records and verify the chain.
pub fn verify_chain_json(value: &Value) -> ChainVerdict {
    let arr = match value.as_array() {
        Some(a) => a,
        None => return ChainVerdict::Indeterminate,
    };
    let mut records = Vec::with_capacity(arr.len());
    for item in arr {
        match serde_json::from_value::<LedgerRecord>(item.clone()) {
            Ok(r) => records.push(r),
            Err(_) => return ChainVerdict::Indeterminate,
        }
    }
    verify_chain(&records)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn empty_chain_is_consistent() {
        assert_eq!(verify_chain(&[]), ChainVerdict::Consistent);
    }

    #[test]
    fn domain_hash_differs_by_tag() {
        let data = b"payload";
        let a = domain_separated_hash(TAG_RECORD, data);
        let b = domain_separated_hash(TAG_LEAF, data);
        assert_ne!(a, b);
        assert_eq!(a.len(), 32);
    }

    #[test]
    fn genesis_link_and_rehash() {
        let payload = json!({"event": "hello"});
        let hash = compute_record_hash(0, GENESIS_PREV_HASH, &payload).unwrap();
        let rec = LedgerRecord {
            schema: Some(LEDGER_RECORD_SCHEMA.to_string()),
            index: 0,
            prev_hash: GENESIS_PREV_HASH.to_string(),
            payload,
            record_hash: hash,
            created_at: None,
        };
        assert_eq!(verify_chain(&[rec]), ChainVerdict::Consistent);
    }

    #[test]
    fn detects_bad_prev() {
        let payload = json!({"event": "hello"});
        let hash = compute_record_hash(0, GENESIS_PREV_HASH, &payload).unwrap();
        let rec = LedgerRecord {
            schema: Some(LEDGER_RECORD_SCHEMA.to_string()),
            index: 0,
            prev_hash: "1111111111111111111111111111111111111111111111111111111111111111"
                .to_string(),
            payload,
            record_hash: hash,
            created_at: None,
        };
        assert_eq!(verify_chain(&[rec]), ChainVerdict::Inconsistent);
    }

}
