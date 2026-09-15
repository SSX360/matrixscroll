"""Three-valued verification verdict (gold-standard fail-closed contract)."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class Verdict(IntEnum):
    """Fail-closed result. Matches CLI exit codes in docs/reference/exit-codes.md."""

    CONSISTENT = 0
    INDETERMINATE = 1
    INCONSISTENT = 2

    @property
    def label(self) -> str:
        return self.name

    def to_dict(self, *, detail: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "verdict": self.label,
            "exit_code": int(self),
            "ok": self is Verdict.CONSISTENT,
        }
        if detail is not None:
            payload["detail"] = detail
        return payload


def verdict_from_ok(ok: bool, *, indeterminate: bool = False) -> Verdict:
    if indeterminate:
        return Verdict.INDETERMINATE
    return Verdict.CONSISTENT if ok else Verdict.INCONSISTENT
