# SSX360 SE050 USB Protocol

Protocol version: `ssx360.se050.poc.v1`

This document locks the host/device interface for the SE050 proof of concept.
The goal is to keep the Matrix Scroll manifest schema and verification path
unchanged while standardizing the USB message framing for the RP2350 bridge.

## Transport

- USB CDC ACM serial
- UTF-8 JSON
- one request per line
- one response per line
- newline delimiter: `\n`

Requests and responses are single JSON objects with no surrounding framing.

## Commands

### `ping`

Request:

```json
{"cmd":"ping"}
```

Response:

```json
{"ok":true,"protocol":"ssx360.se050.poc.v1","result":"pong"}
```

### `pubkey`

Request:

```json
{"cmd":"pubkey"}
```

Response:

```json
{"ok":true,"public_key":"<base64 raw 32-byte Ed25519 public key>"}
```

### `sign`

Request:

```json
{"cmd":"sign","message":"<base64 canonical manifest bytes>"}
```

Response:

```json
{
  "ok": true,
  "public_key": "<base64 raw 32-byte Ed25519 public key>",
  "signature": "<base64 raw 64-byte Ed25519 signature>"
}
```

## Errors

All failures return:

```json
{"ok":false,"error":"human-readable reason"}
```

Examples:

- malformed JSON
- unsupported command
- key not provisioned
- signing denied by lifecycle state
- transport timeout to the secure element

## Matrix Scroll Constraints

- `message` is the canonical manifest bytes produced by Matrix Scroll
- the device signs those bytes directly with Ed25519
- the device does not accept a SHA-256 digest in place of manifest bytes
- the host constructs the normal Matrix Scroll `signature` block after the response
- `device_id` remains derived from `SHA256(public_key)` per `SPEC.md`

## Host Expectations

- `pubkey` and the `public_key` returned from `sign` must match for the same
  device session
- `signature` is verified through the existing Matrix Scroll SDK path
- no private key material or seed is ever returned
