# SSX360 SE050 Paid PoC Scope

Fixed-fee proposal placeholder: **[FIXED_FEE_USD] USD**

Hardware, shipping, import, and taxes remain reimbursable pass-through costs.

## Objective

Deliver a paid proof of concept for the SSX360 USB security device where:

- Raspberry Pi Pico 2 (`RP2350`) handles USB CDC ACM and the host bridge
- NXP `SE050` generates and retains a non-exportable Ed25519 keypair
- the host sends canonical Matrix Scroll manifest bytes
- the device returns an Ed25519 signature over those bytes
- the host verifies through the existing Matrix Scroll verification path

The PoC preserves the current Matrix Scroll v1 trust model:

- signing input: canonical JSON manifest bytes
- signing algorithm: Ed25519
- digest use: SHA-256 only for `device_id` derivation, not for signatures
- SDK compatibility: no new manifest schema and no alternate verify path

## In Scope

- bring-up on `RP2350 + SE050` using a Pico 2 and `OM-SE050ARD-E` or equivalent
  SE050 breakout
- SE050 in-chip Ed25519 key generation with the private key remaining inside
  the secure element
- USB CDC ACM request/response transport between host and RP2350
- documented newline-delimited JSON protocol: `ping`, `pubkey`, `sign`
- host harness that sends canonical manifest bytes, receives `signature` plus
  `public_key`, constructs a normal Matrix Scroll `signature` block, and
  verifies with the current SDK path
- provisioning and locking plan for the PoC device state
- measured signing latency on real hardware

## Out of Scope

- LCD, mascot, or other UI polish
- production enclosure or industrial design
- production PCB spin
- fleet provisioning backend
- touch-gate UX or end-user interaction model
- Matrix Scroll packaging or SDK integration beyond the PoC harness and
  hardware transport
- final production SE051 migration work

## Deliverables

- firmware source for the RP2350 USB bridge and SE050 command path
- minimal Python host harness for `ping`, `pubkey`, `sign`, vector generation,
  and latency checks
- reproducible flash and wiring instructions
- 10 signed test manifests produced by the device
- short demo video showing keygen, sign, and verify
- provisioning and locking notes with explicit cautions around irreversible states
- all firmware, documentation, and PoC work product assigned to SSX360

## Acceptance Criteria

1. The device generates a non-exportable Ed25519 keypair inside the SE050.
2. The private key is never returned over USB, logged to disk, or exposed by
   the host harness.
3. `ping`, `pubkey`, and `sign` work over USB CDC ACM on a clean machine using
   the documented steps.
4. The host sends canonical manifest bytes directly, not a SHA-256 pre-hash.
5. Returned signatures verify through the current Matrix Scroll SDK and produce
   the expected `mode: "hardware"` signature block.
6. The public key yields the same `device_id` derivation format as the current
   spec.
7. Ten signed manifest fixtures verify locally with the existing verify path.
8. A latency report is included for representative 1 KB and 4 KB manifests.

## Timeline

Assumes hardware is in hand before day 0.

- Days 0-2: Pico 2 + SE050 bring-up, I2C path, Plug & Trust flow, in-chip
  keygen, public-key retrieval
- Days 3-7: USB CDC protocol, device-side sign flow, host harness, end-to-end
  verify against current canonicalization
- Days 8-12: vectors, 10 signed manifests, latency benchmark, provisioning
  notes, demo recording
- Days 13-15: buffer, acceptance review, handoff

## Provisioning and Locking Constraints

- demonstrate one non-exportable in-chip key path on SE050
- do not irreversibly lock the primary demo board without explicit SSX360 approval
- use the spare SE050 board for one-way lifecycle or lock-state experiments
- record the exact lifecycle state and recovery implications for each step
