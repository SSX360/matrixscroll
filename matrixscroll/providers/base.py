"""Identity provider abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod


class IdentityProvider(ABC):
    """A root-of-trust provider. Signing happens here; keys never escape."""

    mode: str = "unknown"

    @abstractmethod
    def public_key_bytes(self) -> bytes:
        ...

    @abstractmethod
    def sign(self, data: bytes) -> bytes:
        ...

    @property
    def created_at(self) -> str:
        return ""

    def is_available(self) -> tuple[bool, str | None]:
        return True, None
