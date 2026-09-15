//! Deterministic JSON encoding for Matrix Scroll signing and ledger bodies.
//!
//! Goal: match the Python reference (`matrixscroll.canonical` /
//! `tools/independent_verify.py`) on common fixtures: sorted object keys,
//! compact separators, ASCII-style escapes for non-ASCII, reject NaN/Infinity.
//!
//! Full RFC 8785 (JCS) remains next. When this walk and the Python vectors
//! disagree, treat the Python vectors and independent verifier as authoritative.
//! Callers that already hold SPEC-canonical bytes may hash them directly via
//! [`sha256_hex`] without re-encoding.

use serde_json::Value;
use sha2::{Digest, Sha256};

/// Keys excluded from Ed25519 / overlay signing input (SPEC §4 / SDK canonical).
const EXCLUDE_FROM_SIGNING: &[&str] = &["signature", "pqc_signatures", "timestamp", "receipt"];

/// SHA-256 of pre-supplied canonical bytes as lowercase hex.
///
/// Use this when Python (or another authoritative encoder) already produced the
/// signing input. Prefer this path for cross-language vector checks until the
/// Rust walk is proven bit-identical on the full fixture set.
pub fn sha256_hex(data: &[u8]) -> String {
    let digest = Sha256::digest(data);
    hex_encode(&digest)
}

/// Drop signature and informational overlay keys, then encode.
pub fn canonical_bytes(payload: &Value) -> Result<Vec<u8>, CanonicalError> {
    let body = signing_body(payload)?;
    Ok(encode_value(&body)?.into_bytes())
}

/// Body used for signing: object without excluded keys.
pub fn signing_body(payload: &Value) -> Result<Value, CanonicalError> {
    let obj = payload
        .as_object()
        .ok_or(CanonicalError::NotObject)?;
    let mut out = serde_json::Map::new();
    for (k, v) in obj {
        if EXCLUDE_FROM_SIGNING.contains(&k.as_str()) {
            continue;
        }
        out.insert(k.clone(), v.clone());
    }
    Ok(Value::Object(out))
}

/// Encode a JSON value with sorted object keys and compact separators.
pub fn encode_value(value: &Value) -> Result<String, CanonicalError> {
    match value {
        Value::Null => Ok("null".to_string()),
        Value::Bool(b) => Ok(if *b { "true" } else { "false" }.to_string()),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                return Ok(i.to_string());
            }
            if let Some(u) = n.as_u64() {
                return Ok(u.to_string());
            }
            if let Some(f) = n.as_f64() {
                if !f.is_finite() {
                    return Err(CanonicalError::NonFiniteNumber);
                }
                // Best-effort; Python `json.dumps` / `repr` edge cases may differ.
                // Prefer sha256_hex over pre-supplied canonical bytes for vectors.
                Ok(format_finite_float(f))
            } else {
                Err(CanonicalError::UnsupportedNumber)
            }
        }
        Value::String(s) => Ok(canonical_string(s)),
        Value::Array(items) => {
            let mut parts = Vec::with_capacity(items.len());
            for item in items {
                parts.push(encode_value(item)?);
            }
            Ok(format!("[{}]", parts.join(",")))
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let mut parts = Vec::with_capacity(keys.len());
            for key in keys {
                let encoded_key = canonical_string(key);
                let encoded_val = encode_value(&map[key])?;
                parts.push(format!("{encoded_key}:{encoded_val}"));
            }
            Ok(format!("{{{}}}", parts.join(",")))
        }
    }
}

fn format_finite_float(f: f64) -> String {
    // Prefer an integer-looking form when exact, else shortest round-trip-ish.
    if f.fract() == 0.0 && f.abs() < (i64::MAX as f64) {
        format!("{}", f as i64)
    } else {
        let s = format!("{}", f);
        if s.contains('e') || s.contains('E') || s.contains('.') {
            s
        } else {
            format!("{s}.0")
        }
    }
}

fn canonical_string(value: &str) -> String {
    let mut out = String::from("\"");
    for ch in value.chars() {
        let code = ch as u32;
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{0008}' => out.push_str("\\b"),
            '\u{000c}' => out.push_str("\\f"),
            _ if code < 0x20 => {
                out.push_str(&format!("\\u{code:04x}"));
            }
            _ if code < 0x7F => out.push(ch),
            _ if code <= 0xFFFF => {
                out.push_str(&format!("\\u{code:04x}"));
            }
            _ => {
                // Astral → UTF-16 surrogate pair (Python ensure_ascii style).
                let adj = code - 0x10000;
                let high = 0xD800 | (adj >> 10);
                let low = 0xDC00 | (adj & 0x3FF);
                out.push_str(&format!("\\u{high:04x}\\u{low:04x}"));
            }
        }
    }
    out.push('"');
    out
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

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CanonicalError {
    NotObject,
    NonFiniteNumber,
    UnsupportedNumber,
}

impl std::fmt::Display for CanonicalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CanonicalError::NotObject => write!(f, "canonical payload must be a JSON object"),
            CanonicalError::NonFiniteNumber => {
                write!(f, "NaN and Infinity have no canonical form (SPEC.md section 4)")
            }
            CanonicalError::UnsupportedNumber => write!(f, "unsupported JSON number"),
        }
    }
}

impl std::error::Error for CanonicalError {}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn sorts_keys_and_compacts() {
        let v = json!({"b": 1, "a": {"y": 2, "x": 1}});
        let bytes = canonical_bytes(&v).unwrap();
        assert_eq!(bytes, br#"{"a":{"x":1,"y":2},"b":1}"#);
    }

    #[test]
    fn excludes_signature_keys() {
        let v = json!({"release": "v1", "signature": {"value": "x"}});
        let bytes = canonical_bytes(&v).unwrap();
        assert_eq!(bytes, br#"{"release":"v1"}"#);
    }

    #[test]
    fn sha256_over_presupplied_bytes() {
        let dig = sha256_hex(b"abc");
        assert_eq!(
            dig,
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }
}
