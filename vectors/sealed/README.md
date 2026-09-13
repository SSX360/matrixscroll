# Sealed evidence packs

Format: `matrixscroll.sealed-evidence-pack.v1` — see
[`schemas/sealed-evidence-pack.v1.json`](../../schemas/sealed-evidence-pack.v1.json).

Hybrid seal (0.9.0):

1. ML-KEM-1024 encapsulate to the recipient encapsulation key.
2. Ephemeral X25519 Diffie–Hellman with the recipient's long-term X25519 public key.
3. `AES-256-GCM` key = `HKDF-SHA256(ikm = ss_mlkem || ss_x25519, salt = "matrixscroll-sealed-v1", info = "aes-256-gcm", length = 32)`.
4. Sign canonical pack bytes (including ciphertext) with Ed25519, then attach ML-DSA-87.

Round-trip and tamper cases live in `tests/test_sealed.py` (requires
`matrixscroll[pqc]`). Fixed ciphertext vectors are not checked in here: the
KEM encapsulation and X25519 ephemeral are fresh each seal; the ML-KEM half is
covered by `vectors/acvp-mlkem-fips203.json`.
