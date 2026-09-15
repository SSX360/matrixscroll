//! Fix unused import in verify_ed25519 tests.
use ed25519_dalek::{Signer, SigningKey};
use matrixscroll_verify::verify_ed25519;

#[test]
fn roundtrip_fixed_seed() {
    let seed = [7u8; 32];
    let sk = SigningKey::from_bytes(&seed);
    let vk = sk.verifying_key();
    let msg = b"matrixscroll-verify";
    let sig = sk.sign(msg);
    assert!(verify_ed25519(vk.as_bytes(), msg, &sig.to_bytes()).unwrap());
    assert!(!verify_ed25519(vk.as_bytes(), b"tampered", &sig.to_bytes()).unwrap());
}

#[test]
fn rejects_bad_lengths() {
    assert!(verify_ed25519(&[0u8; 31], b"m", &[0u8; 64]).is_err());
    assert!(verify_ed25519(&[0u8; 32], b"m", &[0u8; 63]).is_err());
}
