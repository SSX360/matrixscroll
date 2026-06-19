"""Hardware provider stub for SSX360 / NXP SE050."""

from __future__ import annotations

from .base import IdentityProvider


class HardwareProvider(IdentityProvider):
    mode = "hardware"
    UNAVAILABLE_REASON = (
        "Matrix Scroll hardware provider is not available yet. "
        "Use MATRIXSCROLL_MODE=emulated (default) for the software key."
    )

    def is_available(self) -> tuple[bool, str | None]:
        return False, self.UNAVAILABLE_REASON

    def public_key_bytes(self) -> bytes:  # pragma: no cover
        raise NotImplementedError(self.UNAVAILABLE_REASON)

    def sign(self, data: bytes) -> bytes:  # pragma: no cover
        raise NotImplementedError(self.UNAVAILABLE_REASON)
