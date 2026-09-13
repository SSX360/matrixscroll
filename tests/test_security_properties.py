"""Hypothesis property tests for P1–P3 security properties."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given, settings

import matrixscroll
from matrixscroll import EmulatedProvider


def _provider(directory: Path) -> EmulatedProvider:
    return EmulatedProvider.load_or_create(directory)


class SecurityPropertyTests(unittest.TestCase):
    @given(st.binary(min_size=0, max_size=4096))
    @settings(max_examples=50, deadline=None)
    def test_p1_sign_verify_roundtrip(self, message: bytes) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            provider = _provider(Path(tmp))
            pub = matrixscroll.public_key_b64(provider)
            sig = matrixscroll.sign(message, provider)
            self.assertTrue(matrixscroll.verify(pub, message, sig))

    @given(st.binary(min_size=1, max_size=4096))
    @settings(max_examples=50, deadline=None)
    def test_p2_tampered_message_rejected(self, message: bytes) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            provider = _provider(Path(tmp))
            pub = matrixscroll.public_key_b64(provider)
            sig = matrixscroll.sign(message, provider)
            tampered = message + b"\x00"
            self.assertFalse(matrixscroll.verify(pub, tampered, sig))

    @given(st.binary(min_size=1, max_size=4096))
    @settings(max_examples=50, deadline=None)
    def test_p2_tampered_signature_rejected(self, message: bytes) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            provider = _provider(Path(tmp))
            pub = matrixscroll.public_key_b64(provider)
            sig = bytearray(matrixscroll.sign(message, provider))
            sig[0] ^= 0x01
            self.assertFalse(matrixscroll.verify(pub, message, bytes(sig)))

    @given(st.binary(min_size=1, max_size=4096))
    @settings(max_examples=50, deadline=None)
    def test_p3_wrong_key_rejected(self, message: bytes) -> None:
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            signer = _provider(Path(a))
            other_pub = matrixscroll.public_key_b64(_provider(Path(b)))
            sig = matrixscroll.sign(message, signer)
            self.assertFalse(matrixscroll.verify(other_pub, message, sig))
