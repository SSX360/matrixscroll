"""Matrix Scroll exceptions."""

from __future__ import annotations


class IdentityError(Exception):
    """Raised when the device key store cannot be read or is untrustworthy."""


class VerificationError(Exception):
    """Raised when policy-aware verification fails with an explicit reason."""
