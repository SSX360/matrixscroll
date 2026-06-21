"""Hardware provider for SSX360 / NXP SE050.

Integration checklist (SSX-7):

1. Pico 2 + OM-SE050ARD-E wired per NXP AN12570 (I2C).
2. Sign canonical manifest bytes with Ed25519 on SE050 (not SHA-256 pre-hash).
3. Map SE050 public key to Matrix Scroll device_id per SPEC.md.
4. Pass all vectors in ``matrixscroll/vectors/`` via ``matrixscroll verify``.
5. Wire ``HardwareProvider.sign`` / ``public_key_bytes`` behind ``MATRIXSCROLL_MODE=hardware``.
6. Mock transport via ``MATRIXSCROLL_SE050_MOCK=1`` before CI hardware runners.

Procurement: ``launch/poc-bom-procurement.md`` in SSX360_90D workspace.
"""

from __future__ import annotations

from typing import Any

from ..errors import IdentityError
from .base import IdentityProvider
from .emulated import device_id as ms_device_id
from .se050_transport import MockSE050Transport, SE050Transport, open_transport


class HardwareProvider(IdentityProvider):
    mode = "hardware"
    UNAVAILABLE_REASON = (
        "Matrix Scroll hardware provider is not available yet. "
        "Use MATRIXSCROLL_MODE=emulated (default) or MATRIXSCROLL_SE050_MOCK=1 for mock transport."
    )

    def __init__(self) -> None:
        self._transport: SE050Transport | None = open_transport()
        self._public_key: bytes | None = None

    def is_available(self) -> tuple[bool, str | None]:
        if self._transport is None:
            return False, self.UNAVAILABLE_REASON
        if not self._transport.ping():
            reason = getattr(self._transport, "reason", None)
            return False, reason or "SE050 transport did not respond to ping"
        return True, None

    def _require_transport(self) -> SE050Transport:
        available, reason = self.is_available()
        if not available or self._transport is None:
            raise IdentityError(reason or self.UNAVAILABLE_REASON)
        return self._transport

    def public_key_bytes(self) -> bytes:
        if self._public_key is not None:
            return self._public_key
        transport = self._require_transport()
        self._public_key = transport.public_key_bytes()
        return self._public_key

    def sign(self, data: bytes) -> bytes:
        transport = self._require_transport()
        return transport.sign(data)

    def status_detail(self) -> dict[str, Any]:
        available, reason = self.is_available()
        detail: dict[str, Any] = {
            "mode": self.mode,
            "available": available,
            "reason": reason,
            "mock": isinstance(self._transport, MockSE050Transport),
            "transport": type(self._transport).__name__ if self._transport is not None else None,
            "device_id": ms_device_id(self.public_key_bytes()) if available else None,
        }
        return detail
