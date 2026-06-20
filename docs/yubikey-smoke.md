# YubiKey manual smoke test

Requires a YubiKey 5 with PIV EC key and [Yubico PKCS#11 module](https://www.yubico.com/support/download/yubikey-manager/) installed.

## Linux / macOS

```bash
export MATRIXSCROLL_MODE=yubikey
export MATRIXSCROLL_YKCS11_MODULE=/usr/lib/x86_64-linux-gnu/libykcs11.so  # adjust path
export MATRIXSCROLL_PIV_PIN='your-pin'

matrixscroll status
matrixscroll sign vectors/valid_simple.json
matrixscroll verify vectors/valid_simple.json
```

## Windows

```powershell
$env:MATRIXSCROLL_MODE = "yubikey"
$env:MATRIXSCROLL_YKCS11_MODULE = "C:\Program Files\Yubico\Yubico PIV Tool\bin\ykcs11.dll"
$env:MATRIXSCROLL_PIV_PIN = "your-pin"

matrixscroll status
```

## Mock (no hardware)

```powershell
$env:MATRIXSCROLL_MODE = "yubikey"
$env:MATRIXSCROLL_YKCS11_MOCK = "1"
python -m pytest tests/test_yubikey_provider.py -q
```

Expected: `algorithm: ecdsa-p256`, `mode: yubikey`, verify passes.
