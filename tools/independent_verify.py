#!/usr/bin/env python3
"""Independent verifier for Matrix Scroll signed manifests.

This program shares no code with the ``matrixscroll`` package and imports nothing
outside the Python standard library. It re-implements, from ``SPEC.md`` alone:

* section 4, the canonical encoding (its own serializer, not ``json.dumps``);
* section 3, the device identifier derivation;
* sections 5 and 6, the signature block rules and the verification procedure;
* RFC 8032 Ed25519 verification, in pure Python, from the reference algorithm.

It exists so that a reviewer can check the SDK against a second implementation:
run it over ``vectors/`` and compare its verdicts with ``matrixscroll verify``.
``tests/test_independent_verifier.py`` does that comparison in CI on every change.

Usage::

    python tools/independent_verify.py vectors/            # verdict per file
    python tools/independent_verify.py --json vectors/     # machine-readable
    python tools/independent_verify.py --canonical FILE    # hex of the canonical signing bytes

The exit status is 0 when every verdict matches the expectation in its file name
(``valid_*``, ``tampered_*``, ``unsigned_*``) and every file without such a name
verifies; it is 1 when a verdict contradicts its name or an unnamed file is
invalid or unreadable, and 2 when no files were given.

The optional post-quantum overlay (SPEC.md section 11) is checked when
``liboqs-python`` is importable; otherwise it is reported as not checked. Nothing
here is a certification claim; the program is evidence that two independent
readings of the specification agree on the committed vectors.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import math
import sys
from pathlib import Path

SIGNATURE_SCHEMA = "matrixscroll.signature.v1"
PQC_SCHEMA = "matrixscroll.pqc_signature.v1"
ALGORITHM = "ed25519"
PQC_MECHANISMS = {
    "ml-dsa-44": ("ML-DSA-44",),
    "ml-dsa-65": ("ML-DSA-65",),
    "ml-dsa-87": ("ML-DSA-87",),
    "slh-dsa-sha2-128s": ("SLH_DSA_PURE_SHA2_128S", "SLH-DSA-SHA2-128s"),
    "slh-dsa-sha2-128f": ("SLH_DSA_PURE_SHA2_128F", "SLH-DSA-SHA2-128f"),
    "slh-dsa-sha2-256s": ("SLH_DSA_PURE_SHA2_256S", "SLH-DSA-SHA2-256s"),
    "slh-dsa-sha2-256f": ("SLH_DSA_PURE_SHA2_256F", "SLH-DSA-SHA2-256f"),
}

# --- SPEC.md section 4: canonical encoding, written without json.dumps ---------

_ESCAPES = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f"}


def canonical_string(value: str) -> str:
    out = ['"']
    for ch in value:
        code = ord(ch)
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif code < 0x20:
            out.append("\\u%04x" % code)
        elif code < 0x7F:
            out.append(ch)
        elif code <= 0xFFFF:
            out.append("\\u%04x" % code)
        else:
            # Astral code points become a UTF-16 surrogate pair, as ensure_ascii does.
            code -= 0x10000
            out.append("\\u%04x\\u%04x" % (0xD800 | (code >> 10), 0xDC00 | (code & 0x3FF)))
    out.append('"')
    return "".join(out)


def canonical_value(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("NaN and Infinity have no canonical form (SPEC.md section 4, rule 5)")
        return repr(value)
    if isinstance(value, str):
        return canonical_string(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_value(item) for item in value) + "]"
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise TypeError("object keys must be strings")
        parts = []
        for key in sorted(value):  # ascending by Unicode code point, as Python's sort_keys
            parts.append(canonical_string(key) + ":" + canonical_value(value[key]))
        return "{" + ",".join(parts) + "}"
    raise TypeError(f"unsupported JSON value type {type(value).__name__}")


def canonical_bytes(manifest: dict) -> bytes:
    """Rules 1 to 6: drop the signature blocks, then encode; section 11.2 drops both."""
    body = {k: v for k, v in manifest.items() if k not in ("signature", "pqc_signatures")}
    return canonical_value(body).encode("utf-8")


# --- SPEC.md section 3: device identifier -------------------------------------


def device_id(public_key: bytes) -> str:
    digest = hashlib.sha256(public_key).hexdigest().upper()
    return "MS-" + digest[0:4] + "-" + digest[4:8]


# --- RFC 8032 Ed25519 verification, pure Python (reference algorithm) ----------

_P = 2**255 - 19
_Q = 2**252 + 27742317777372353535851937790883648493


def _inv(x: int) -> int:
    return pow(x, _P - 2, _P)


_D = (-121665 * _inv(121666)) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)


def _point_add(a, b):
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    e = ((y1 - x1) * (y2 - x2)) % _P
    f = ((y1 + x1) * (y2 + x2)) % _P
    g = (2 * t1 * t2 * _D) % _P
    h = (2 * z1 * z2) % _P
    return ((f - e) * (h - g) % _P, (f + e) * (h + g) % _P, (h - g) * (h + g) % _P, (f - e) * (f + e) % _P)


def _point_mul(s: int, point):
    q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            q = _point_add(q, point)
        point = _point_add(point, point)
        s >>= 1
    return q


def _point_equal(a, b) -> bool:
    x1, y1, z1, _ = a
    x2, y2, z2, _ = b
    return (x1 * z2 - x2 * z1) % _P == 0 and (y1 * z2 - y2 * z1) % _P == 0


def _recover_x(y: int, sign: int):
    if y >= _P:
        return None
    x2 = (y * y - 1) * _inv(_D * y * y + 1) % _P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = x * _SQRT_M1 % _P
    if (x * x - x2) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


def _point_decompress(raw: bytes):
    if len(raw) != 32:
        return None
    y = int.from_bytes(raw, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % _P)


_G_Y = 4 * _inv(5) % _P
_G_X = _recover_x(_G_Y, 0)
_G = (_G_X, _G_Y, 1, _G_X * _G_Y % _P)
_IDENTITY = (0, 1, 1, 0)


def _has_small_order(point) -> bool:
    """True for the eight points of the torsion subgroup, the identity included.

    A public key of small order makes the verification equation hold for a
    signature that needs no private key (R the identity, S zero), so such keys
    and such R values are rejected, as libsodium does. The SDK keeps the same
    rule as a blocklist of encodings (``crypto_backend.ed25519_point_is_acceptable``).
    """
    return _point_equal(_point_mul(8, point), _IDENTITY)


def ed25519_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    if len(public_key) != 32 or len(signature) != 64:
        return False
    a = _point_decompress(public_key)
    if a is None or _has_small_order(a):
        return False
    r = _point_decompress(signature[:32])
    if r is None or _has_small_order(r):
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= _Q:
        return False
    h = int.from_bytes(hashlib.sha512(signature[:32] + public_key + message).digest(), "little") % _Q
    return _point_equal(_point_mul(s, _G), _point_add(r, _point_mul(h, a)))


# --- SPEC.md sections 5, 6 and 11: the verification procedure -----------------


def _b64(value) -> bytes | None:
    if not isinstance(value, str):
        return None
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, binascii.Error, UnicodeEncodeError):
        return None


def verify_ed25519_block(manifest: object) -> tuple[bool, str]:
    """Return (valid, reason) for the required Ed25519 signature block."""
    if not isinstance(manifest, dict):
        return False, "manifest is not a JSON object"
    block = manifest.get("signature")
    if not isinstance(block, dict):
        return False, "no signature block"
    if block.get("schema") != SIGNATURE_SCHEMA:
        return False, "signature.schema is not " + SIGNATURE_SCHEMA
    if block.get("algorithm", ALGORITHM) != ALGORITHM:
        return False, "signature.algorithm is not ed25519"
    public_key = _b64(block.get("public_key"))
    signature = _b64(block.get("value"))
    if public_key is None or signature is None:
        return False, "public_key or value is not strict base64"
    if block.get("device_id") != device_id(public_key):
        return False, "device_id does not derive from public_key"
    try:
        message = canonical_bytes(manifest)
    except (TypeError, ValueError) as exc:
        return False, f"canonical encoding failed: {exc}"
    if ed25519_verify(public_key, message, signature):
        return True, "ed25519 signature verifies over the canonical bytes"
    return False, "ed25519 signature does not verify"


def verify_pqc_blocks(manifest: dict) -> tuple[str, str]:
    """Return (status, detail): 'absent', 'valid', 'invalid' or 'not-checked'.

    The structural rules of SPEC.md section 11 (schema, allowed algorithm, strict
    base64 fields, a canonical encoding that exists) are checked first and without
    liboqs, so a malformed block is 'invalid' whether or not the backend is
    installed; only the signature check itself can be 'not-checked'.
    """
    blocks = manifest.get("pqc_signatures")
    if blocks is None:
        return "absent", "no pqc_signatures array"
    if not isinstance(blocks, list) or not blocks:
        return "invalid", "pqc_signatures is not a non-empty array"
    decoded: list[tuple[str, bytes, bytes]] = []
    for index, block in enumerate(blocks):
        if not isinstance(block, dict) or block.get("schema") != PQC_SCHEMA:
            return "invalid", f"block {index}: schema is not {PQC_SCHEMA}"
        algorithm = block.get("algorithm")
        if algorithm not in PQC_MECHANISMS:
            return "invalid", f"block {index}: algorithm {algorithm!r} is not allowed"
        public_key = _b64(block.get("public_key"))
        signature = _b64(block.get("value"))
        if public_key is None or signature is None:
            return "invalid", f"block {index}: public_key or value is not strict base64"
        decoded.append((algorithm, public_key, signature))
    try:
        message = canonical_bytes(manifest)
    except (TypeError, ValueError) as exc:
        return "invalid", f"canonical encoding failed: {exc}"
    try:
        import oqs  # type: ignore[import-untyped]
    except Exception:
        return "not-checked", "liboqs-python is not importable"
    try:
        enabled = set(oqs.get_enabled_sig_mechanisms())
    except Exception:
        return "not-checked", "liboqs mechanism list unavailable"
    for index, (algorithm, public_key, signature) in enumerate(decoded):
        mechanism = next((name for name in PQC_MECHANISMS[algorithm] if name in enabled), None)
        if mechanism is None:
            return "not-checked", f"block {index}: {algorithm} is not enabled in this liboqs build"
        try:
            with oqs.Signature(mechanism) as sig:
                ok = bool(sig.verify(message, signature, public_key))
        except Exception as exc:
            return "invalid", f"block {index}: verifier error {exc.__class__.__name__}"
        if not ok:
            return "invalid", f"block {index}: {algorithm} signature does not verify"
    return "valid", f"{len(blocks)} pqc block(s) verify over the canonical bytes"


# --- command line ---------------------------------------------------------------


def expected_from_name(path: Path) -> bool | None:
    name = path.name
    if name.startswith("valid_"):
        return True
    if name.startswith("tampered_") or name.startswith("unsigned_"):
        return False
    return None


def collect(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(f for f in p.glob("*.json") if not f.name.startswith(("_", "acvp-"))))
        else:
            files.append(p)
    return files


def check_file(path: Path) -> dict:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"file": str(path), "valid": False, "reason": f"unreadable: {exc}", "pqc": "not-checked", "pqc_detail": "", "expected": expected_from_name(path), "agrees": None}
    valid, reason = verify_ed25519_block(manifest)
    pqc_status, pqc_detail = ("absent", "") if not isinstance(manifest, dict) else verify_pqc_blocks(manifest)
    if pqc_status == "invalid":
        valid = False
    expected = expected_from_name(path)
    return {
        "file": str(path),
        "valid": valid,
        "reason": reason,
        "pqc": pqc_status,
        "pqc_detail": pqc_detail,
        "expected": expected,
        "agrees": None if expected is None else (valid == expected),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="+", help="manifest files or directories of *.json fixtures")
    parser.add_argument("--json", action="store_true", help="print one JSON document with every verdict")
    parser.add_argument("--canonical", action="store_true", help="print the canonical signing bytes as hex instead of verifying")
    args = parser.parse_args(argv)
    files = collect(args.paths)
    if not files:
        print("no files", file=sys.stderr)
        return 2
    if args.canonical:
        for path in files:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            print(f"{path}\t{canonical_bytes(manifest).hex()}")
        return 0
    results = [check_file(path) for path in files]
    if args.json:
        print(json.dumps({"results": results}, indent=1))
    else:
        for r in results:
            flag = "" if r["agrees"] is None else ("  (matches its name)" if r["agrees"] else "  (DOES NOT match its name)")
            pqc = "" if r["pqc"] == "absent" else f"; pqc {r['pqc']}"
            print(f"{'VALID  ' if r['valid'] else 'INVALID'}  {r['file']}: {r['reason']}{pqc}{flag}")
    failures = [r for r in results if r["agrees"] is False or (r["agrees"] is None and not r["valid"])]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
