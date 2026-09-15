//! Ed25519 verification over raw message bytes (RFC 8032).
//!
//! Public key is the 32-byte compressed encoding. Signature is 64 bytes.

use ed25519_dalek::{Signature, Verifier, VerifyingKey};

/// Verify an Ed25519 signature over `message` with a raw 32-byte public key.
///
/// Returns `Ok(true)` on success, `Ok(false)` on cryptographic failure, and
/// `Err` when key or signature lengths are wrong (caller maps to INDETERMINATE).
pub fn verify_ed25519(
    public_key: &[u8],
    message: &[u8],
    signature: &[u8],
) -> Result<bool, VerifyError> {
    if public_key.len() != 32 {
        return Err(VerifyError::BadPublicKeyLength(public_key.len()));
    }
    if signature.len() != 64 {
        return Err(VerifyError::BadSignatureLength(signature.len()));
    }

    let vk = VerifyingKey::from_bytes(public_key.try_into().unwrap())
        .map_err(|_| VerifyError::InvalidPublicKey)?;
    let sig = Signature::from_bytes(signature.try_into().unwrap());

    match vk.verify(message, &sig) {
        Ok(()) => Ok(true),
        Err(_) => Ok(false),
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VerifyError {
    BadPublicKeyLength(usize),
    BadSignatureLength(usize),
    InvalidPublicKey,
}

impl std::fmt::Display for VerifyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            VerifyError::BadPublicKeyLength(n) => {
                write!(f, "public key must be 32 bytes, got {n}")
            }
            VerifyError::BadSignatureLength(n) => {
                write!(f, "signature must be 64 bytes, got {n}")
            }
            VerifyError::InvalidPublicKey => {
                write!(
                    f,
                    "public key bytes are not a valid Ed25519 point encoding"
                )
            }
        }
    }
}

impl std::error::Error for VerifyError {}
