"""Hash-linked ledger with domain separation and epoch checkpoints (SPEC §12).

Implements the NIST IR 8536-style hash-linked traceability chain described in
the gold-standard pipeline: domain-separated leaf hashes, previous-record
linking, and signed time-epoch checkpoints. Evidence mapping only; not a
certification claim.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .canonical import canonical_bytes
from .crypto_backend import sha256_hex
from .verdict import Verdict

LEDGER_RECORD_SCHEMA = "matrixscroll.ledger_record.v1"
LEDGER_EPOCH_SCHEMA = "matrixscroll.ledger_epoch.v1"
LEDGER_BUNDLE_SCHEMA = "matrixscroll.ledger_bundle.v1"

# Domain-separation tags (leaf/node style as in RFC 9162; named contexts).
TAG_RECORD = b"matrixscroll/v1/record\x00"
TAG_LEAF = b"matrixscroll/v1/leaf\x00"
TAG_NODE = b"matrixscroll/v1/node\x00"
TAG_EPOCH = b"matrixscroll/v1/epoch\x00"

GENESIS_PREV_HASH = "0" * 64


def domain_separated_hash(tag: bytes, data: bytes) -> str:
    """SHA-256(tag || data) as lowercase hex."""
    return sha256_hex(tag + data)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_payload_bytes(payload: dict[str, Any]) -> bytes:
    """Canonical bytes of a ledger record body (no signature fields)."""
    return canonical_bytes(payload)


def compute_record_hash(
    *,
    index: int,
    prev_hash: str,
    payload: dict[str, Any],
) -> str:
    """Hash one ledger record under the record domain tag."""
    body = {
        "index": index,
        "payload": payload,
        "prev_hash": prev_hash,
        "schema": LEDGER_RECORD_SCHEMA,
    }
    return domain_separated_hash(TAG_RECORD, record_payload_bytes(body))


def leaf_hash(record_hash: str) -> str:
    return domain_separated_hash(TAG_LEAF, bytes.fromhex(record_hash))


def node_hash(left: str, right: str) -> str:
    return domain_separated_hash(
        TAG_NODE,
        bytes.fromhex(left) + bytes.fromhex(right),
    )


def merkle_root(record_hashes: list[str]) -> str:
    """RFC 9162-style binary Merkle root over leaf-hashed record hashes.

    An empty list returns the genesis prev-hash sentinel. Odd nodes are
    duplicated (CT convention) so the tree is always complete.
    """
    if not record_hashes:
        return GENESIS_PREV_HASH
    level = [leaf_hash(h) for h in record_hashes]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [node_hash(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


@dataclass
class LedgerRecord:
    index: int
    prev_hash: str
    payload: dict[str, Any]
    record_hash: str
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": LEDGER_RECORD_SCHEMA,
            "index": self.index,
            "prev_hash": self.prev_hash,
            "payload": self.payload,
            "record_hash": self.record_hash,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LedgerRecord":
        return cls(
            index=int(data["index"]),
            prev_hash=str(data["prev_hash"]),
            payload=dict(data["payload"]),
            record_hash=str(data["record_hash"]),
            created_at=str(data.get("created_at") or _utc_now()),
        )


@dataclass
class EpochCheckpoint:
    epoch_id: str
    start_index: int
    end_index: int
    tip_hash: str
    root_hash: str
    record_count: int
    created_at: str = field(default_factory=_utc_now)
    signature: dict[str, Any] | None = None
    pqc_signatures: list[dict[str, Any]] | None = None

    def unsigned_body(self) -> dict[str, Any]:
        return {
            "schema": LEDGER_EPOCH_SCHEMA,
            "epoch_id": self.epoch_id,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "tip_hash": self.tip_hash,
            "root_hash": self.root_hash,
            "record_count": self.record_count,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        body = self.unsigned_body()
        if self.signature is not None:
            body["signature"] = self.signature
        if self.pqc_signatures:
            body["pqc_signatures"] = self.pqc_signatures
        return body

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EpochCheckpoint":
        return cls(
            epoch_id=str(data["epoch_id"]),
            start_index=int(data["start_index"]),
            end_index=int(data["end_index"]),
            tip_hash=str(data["tip_hash"]),
            root_hash=str(data["root_hash"]),
            record_count=int(data["record_count"]),
            created_at=str(data.get("created_at") or _utc_now()),
            signature=data.get("signature") if isinstance(data.get("signature"), dict) else None,
            pqc_signatures=(
                list(data["pqc_signatures"])
                if isinstance(data.get("pqc_signatures"), list)
                else None
            ),
        )


@dataclass
class Ledger:
    """In-memory append-only hash-linked record chain."""

    records: list[LedgerRecord] = field(default_factory=list)
    epochs: list[EpochCheckpoint] = field(default_factory=list)

    @property
    def tip_hash(self) -> str:
        if not self.records:
            return GENESIS_PREV_HASH
        return self.records[-1].record_hash

    def append(self, payload: dict[str, Any], *, created_at: str | None = None) -> LedgerRecord:
        index = len(self.records)
        prev = self.tip_hash
        record_hash = compute_record_hash(index=index, prev_hash=prev, payload=payload)
        record = LedgerRecord(
            index=index,
            prev_hash=prev,
            payload=payload,
            record_hash=record_hash,
            created_at=created_at or _utc_now(),
        )
        self.records.append(record)
        return record

    def create_epoch(
        self,
        *,
        epoch_id: str | None = None,
        start_index: int = 0,
        end_index: int | None = None,
        sign: bool = True,
        attach_pqc: bool = False,
    ) -> EpochCheckpoint:
        if not self.records:
            raise ValueError("cannot create epoch on empty ledger")
        end = len(self.records) - 1 if end_index is None else end_index
        if start_index < 0 or end >= len(self.records) or start_index > end:
            raise ValueError("invalid epoch range")
        slice_records = self.records[start_index : end + 1]
        hashes = [r.record_hash for r in slice_records]
        tip = slice_records[-1].record_hash
        root = merkle_root(hashes)
        eid = epoch_id or f"epoch-{start_index}-{end}"
        epoch = EpochCheckpoint(
            epoch_id=eid,
            start_index=start_index,
            end_index=end,
            tip_hash=tip,
            root_hash=root,
            record_count=len(slice_records),
        )
        if sign:
            from .manifest import sign_manifest
            from .pqc import attach_pqc_overlay

            signed = sign_manifest(epoch.unsigned_body())
            epoch.signature = signed.get("signature")
            if attach_pqc:
                signed = attach_pqc_overlay(signed)
                epoch.pqc_signatures = signed.get("pqc_signatures")
        self.epochs.append(epoch)
        return epoch

    def to_bundle(self) -> dict[str, Any]:
        return {
            "schema": LEDGER_BUNDLE_SCHEMA,
            "records": [r.to_dict() for r in self.records],
            "epochs": [e.to_dict() for e in self.epochs],
            "tip_hash": self.tip_hash,
        }

    @classmethod
    def from_bundle(cls, data: dict[str, Any]) -> "Ledger":
        ledger = cls()
        for item in data.get("records") or []:
            ledger.records.append(LedgerRecord.from_dict(item))
        for item in data.get("epochs") or []:
            ledger.epochs.append(EpochCheckpoint.from_dict(item))
        return ledger


def verify_record_link(record: LedgerRecord, *, expected_prev: str) -> Verdict:
    if record.prev_hash != expected_prev:
        return Verdict.INCONSISTENT
    expected = compute_record_hash(
        index=record.index,
        prev_hash=record.prev_hash,
        payload=record.payload,
    )
    if record.record_hash != expected:
        return Verdict.INCONSISTENT
    return Verdict.CONSISTENT


def verify_chain(records: list[LedgerRecord] | list[dict[str, Any]]) -> Verdict:
    """Verify hash links, ordering, and recomputed record hashes.

    Returns INCONSISTENT on reorder, omit-with-gap (non-contiguous indices),
    fork (wrong prev_hash), or tampered payload/hash. Empty chain is
    CONSISTENT (vacuous). Truncation of a suffix is CONSISTENT for the
    remaining prefix; callers compare tip hashes when checking against an
    epoch.
    """
    if not records:
        return Verdict.CONSISTENT
    normalized: list[LedgerRecord] = []
    for item in records:
        if isinstance(item, LedgerRecord):
            normalized.append(item)
        else:
            try:
                normalized.append(LedgerRecord.from_dict(item))
            except (KeyError, TypeError, ValueError):
                return Verdict.INDETERMINATE

    expected_prev = GENESIS_PREV_HASH
    for i, record in enumerate(normalized):
        if record.index != i:
            return Verdict.INCONSISTENT
        link = verify_record_link(record, expected_prev=expected_prev)
        if link is not Verdict.CONSISTENT:
            return link
        expected_prev = record.record_hash
    return Verdict.CONSISTENT


def verify_epoch(
    epoch: EpochCheckpoint | dict[str, Any],
    records: list[LedgerRecord] | list[dict[str, Any]],
    *,
    require_signature: bool = True,
) -> Verdict:
    """Verify epoch bounds, tip, Merkle root, and optional signatures."""
    if isinstance(epoch, dict):
        try:
            epoch = EpochCheckpoint.from_dict(epoch)
        except (KeyError, TypeError, ValueError):
            return Verdict.INDETERMINATE

    chain_verdict = verify_chain(records)
    if chain_verdict is not Verdict.CONSISTENT:
        return chain_verdict

    normalized: list[LedgerRecord] = [
        r if isinstance(r, LedgerRecord) else LedgerRecord.from_dict(r) for r in records
    ]
    if not normalized:
        return Verdict.INCONSISTENT
    if epoch.start_index < 0 or epoch.end_index >= len(normalized):
        return Verdict.INCONSISTENT
    if epoch.start_index > epoch.end_index:
        return Verdict.INCONSISTENT
    slice_records = normalized[epoch.start_index : epoch.end_index + 1]
    if epoch.record_count != len(slice_records):
        return Verdict.INCONSISTENT
    if epoch.tip_hash != slice_records[-1].record_hash:
        return Verdict.INCONSISTENT
    root = merkle_root([r.record_hash for r in slice_records])
    if epoch.root_hash != root:
        return Verdict.INCONSISTENT

    # Domain tag over unsigned epoch body (excluding signature fields).
    body = epoch.unsigned_body()
    _ = domain_separated_hash(TAG_EPOCH, canonical_bytes(body))

    if require_signature:
        if not isinstance(epoch.signature, dict):
            return Verdict.INCONSISTENT
        from .manifest import verify_manifest, verify_manifest_pqc

        signed = {**body, "signature": epoch.signature}
        if epoch.pqc_signatures:
            signed["pqc_signatures"] = epoch.pqc_signatures
        if not verify_manifest(signed):
            return Verdict.INCONSISTENT
        if epoch.pqc_signatures and not verify_manifest_pqc(signed):
            return Verdict.INCONSISTENT
    return Verdict.CONSISTENT


def verify_bundle(bundle: dict[str, Any], *, require_epoch_signature: bool = True) -> Verdict:
    """Verify a full ledger bundle: chain plus every attached epoch."""
    try:
        ledger = Ledger.from_bundle(bundle)
    except (KeyError, TypeError, ValueError):
        return Verdict.INDETERMINATE
    chain = verify_chain(ledger.records)
    if chain is not Verdict.CONSISTENT:
        return chain
    if bundle.get("tip_hash") != ledger.tip_hash:
        return Verdict.INCONSISTENT
    for epoch in ledger.epochs:
        ev = verify_epoch(
            epoch,
            ledger.records,
            require_signature=require_epoch_signature,
        )
        if ev is not Verdict.CONSISTENT:
            return ev
    return Verdict.CONSISTENT


def dump_bundle(ledger: Ledger, path: str) -> None:
    from pathlib import Path

    Path(path).write_text(
        json.dumps(ledger.to_bundle(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_bundle(path: str) -> dict[str, Any]:
    from pathlib import Path

    return json.loads(Path(path).read_text(encoding="utf-8-sig"))
