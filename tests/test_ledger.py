"""Tests for matrixscroll.ledger (SPEC §12 hash-linked chain)."""

from __future__ import annotations

import copy

import pytest

from matrixscroll.ledger import (
    GENESIS_PREV_HASH,
    Ledger,
    compute_record_hash,
    domain_separated_hash,
    merkle_root,
    verify_bundle,
    verify_chain,
    verify_epoch,
)
from matrixscroll.verdict import Verdict


def test_domain_separated_hash_differs_by_tag():
    data = b"payload"
    a = domain_separated_hash(b"matrixscroll/v1/record\x00", data)
    b = domain_separated_hash(b"matrixscroll/v1/leaf\x00", data)
    assert a != b
    assert len(a) == 64


def test_append_links_prev_hash():
    ledger = Ledger()
    r0 = ledger.append({"event": "a"})
    r1 = ledger.append({"event": "b"})
    assert r0.prev_hash == GENESIS_PREV_HASH
    assert r1.prev_hash == r0.record_hash
    assert r1.index == 1
    assert verify_chain(ledger.records) is Verdict.CONSISTENT


def test_verify_chain_detects_reorder():
    ledger = Ledger()
    ledger.append({"n": 1})
    ledger.append({"n": 2})
    ledger.append({"n": 3})
    swapped = [ledger.records[0], ledger.records[2], ledger.records[1]]
    assert verify_chain(swapped) is Verdict.INCONSISTENT


def test_verify_chain_detects_omission_gap():
    ledger = Ledger()
    ledger.append({"n": 1})
    ledger.append({"n": 2})
    ledger.append({"n": 3})
    omitted = [ledger.records[0], ledger.records[2]]
    assert verify_chain(omitted) is Verdict.INCONSISTENT


def test_verify_chain_detects_fork():
    ledger = Ledger()
    ledger.append({"n": 1})
    r1 = ledger.append({"n": 2})
    forked = copy.deepcopy(r1.to_dict())
    forked["prev_hash"] = "ab" * 32
    forked["record_hash"] = compute_record_hash(
        index=1,
        prev_hash=forked["prev_hash"],
        payload=forked["payload"],
    )
    assert verify_chain([ledger.records[0].to_dict(), forked]) is Verdict.INCONSISTENT


def test_verify_chain_detects_tampered_payload():
    ledger = Ledger()
    ledger.append({"n": 1})
    bad = ledger.records[0].to_dict()
    bad["payload"] = {"n": 99}
    assert verify_chain([bad]) is Verdict.INCONSISTENT


def test_truncated_prefix_is_consistent():
    ledger = Ledger()
    ledger.append({"n": 1})
    ledger.append({"n": 2})
    ledger.append({"n": 3})
    assert verify_chain(ledger.records[:2]) is Verdict.CONSISTENT


def test_epoch_checkpoint_verifies():
    ledger = Ledger()
    for i in range(4):
        ledger.append({"i": i})
    epoch = ledger.create_epoch(epoch_id="e1", sign=True)
    assert verify_epoch(epoch, ledger.records) is Verdict.CONSISTENT
    assert verify_bundle(ledger.to_bundle()) is Verdict.CONSISTENT


def test_epoch_detects_wrong_root():
    ledger = Ledger()
    ledger.append({"i": 0})
    ledger.append({"i": 1})
    epoch = ledger.create_epoch(sign=True)
    bad = epoch.to_dict()
    bad["root_hash"] = "cd" * 32
    # Signature still present but root wrong — fail before or after sig check.
    assert verify_epoch(bad, ledger.records) is Verdict.INCONSISTENT


def test_merkle_root_stable():
    hashes = ["aa" * 32, "bb" * 32, "cc" * 32]
    assert merkle_root(hashes) == merkle_root(hashes)
    assert merkle_root([]) == GENESIS_PREV_HASH


def test_verdict_to_dict():
    d = Verdict.INCONSISTENT.to_dict(detail="fork")
    assert d["exit_code"] == 2
    assert d["ok"] is False
    assert d["verdict"] == "INCONSISTENT"
