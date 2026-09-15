//! CLI: verify a Matrix Scroll envelope JSON file and print a JSON verdict.
//!
//! Usage: verify --envelope path.json

use std::env;
use std::fs;
use std::process::ExitCode;

use base64::{engine::general_purpose::STANDARD as B64, Engine};
use matrixscroll_verify::{canonical_bytes, verify_ed25519, ChainVerdict};
use serde_json::{json, Value};

fn usage() -> ! {
    eprintln!("usage: verify --envelope <path.json>");
    std::process::exit(1);
}

fn main() -> ExitCode {
    let mut args = env::args().skip(1);
    let mut envelope_path: Option<String> = None;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--envelope" => {
                envelope_path = args.next();
            }
            "-h" | "--help" => usage(),
            other => {
                eprintln!("unknown argument: {other}");
                usage();
            }
        }
    }
    let path = match envelope_path {
        Some(p) => p,
        None => usage(),
    };

    let raw = match fs::read_to_string(&path) {
        Ok(s) => s,
        Err(e) => {
            print_verdict(
                ChainVerdict::Indeterminate,
                &format!("failed to read envelope: {e}"),
            );
            return ExitCode::from(1);
        }
    };

    let doc: Value = match serde_json::from_str(&raw) {
        Ok(v) => v,
        Err(e) => {
            print_verdict(
                ChainVerdict::Indeterminate,
                &format!("invalid JSON: {e}"),
            );
            return ExitCode::from(1);
        }
    };

    let (verdict, detail) = verify_envelope(&doc);
    print_verdict(verdict, &detail);
    ExitCode::from(verdict.exit_code() as u8)
}

fn verify_envelope(doc: &Value) -> (ChainVerdict, String) {
    let obj = match doc.as_object() {
        Some(o) => o,
        None => return (ChainVerdict::Indeterminate, "document must be a JSON object".into()),
    };

    let sig = match obj.get("signature") {
        Some(Value::Object(s)) => s,
        Some(_) => {
            return (
                ChainVerdict::Indeterminate,
                "signature must be an object".into(),
            )
        }
        None => {
            return (
                ChainVerdict::Inconsistent,
                "missing signature block".into(),
            )
        }
    };

    let algorithm = sig.get("algorithm").and_then(|v| v.as_str()).unwrap_or("");
    if algorithm != "ed25519" {
        return (
            ChainVerdict::Indeterminate,
            format!("unsupported algorithm for this Rust CLI: {algorithm:?} (ed25519 only)"),
        );
    }

    let pk_b64 = match sig.get("public_key").and_then(|v| v.as_str()) {
        Some(s) => s,
        None => {
            return (
                ChainVerdict::Indeterminate,
                "signature.public_key missing".into(),
            )
        }
    };
    let sig_b64 = match sig.get("value").and_then(|v| v.as_str()) {
        Some(s) => s,
        None => {
            return (
                ChainVerdict::Indeterminate,
                "signature.value missing".into(),
            )
        }
    };

    let pk = match B64.decode(pk_b64) {
        Ok(b) => b,
        Err(e) => {
            return (
                ChainVerdict::Indeterminate,
                format!("public_key base64 decode failed: {e}"),
            )
        }
    };
    let signature = match B64.decode(sig_b64) {
        Ok(b) => b,
        Err(e) => {
            return (
                ChainVerdict::Indeterminate,
                format!("signature.value base64 decode failed: {e}"),
            )
        }
    };

    let message = match canonical_bytes(doc) {
        Ok(b) => b,
        Err(e) => {
            return (
                ChainVerdict::Indeterminate,
                format!("canonical encoding failed: {e}"),
            )
        }
    };

    match verify_ed25519(&pk, &message, &signature) {
        Ok(true) => (
            ChainVerdict::Consistent,
            "ed25519 signature verifies over the canonical bytes".into(),
        ),
        Ok(false) => (
            ChainVerdict::Inconsistent,
            "ed25519 signature verification failed".into(),
        ),
        Err(e) => (ChainVerdict::Indeterminate, e.to_string()),
    }
}

fn print_verdict(verdict: ChainVerdict, detail: &str) {
    let payload = json!({
        "verdict": verdict.label(),
        "exit_code": verdict.exit_code(),
        "ok": matches!(verdict, ChainVerdict::Consistent),
        "detail": detail,
    });
    println!("{payload}");
}
