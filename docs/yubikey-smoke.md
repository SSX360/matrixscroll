# YubiKey research smoke notes

The PIV prototype is intentionally **not** part of the public Matrix Scroll
rollout because the current path does not preserve the v1 Ed25519 signing
contract.

Use these notes only for local prototype work.

## Mock research boundary

```powershell
$env:MATRIXSCROLL_MODE = "yubikey"
$env:MATRIXSCROLL_ENABLE_EXPERIMENTAL_PIV = "1"
$env:MATRIXSCROLL_YKCS11_MOCK = "1"
python -m pytest tests/test_yubikey_provider.py -q
```

Expected:

- provider availability can be inspected in experimental mode
- `sign_manifest()` rejects the provider for public use because it is not
  Ed25519-compatible
