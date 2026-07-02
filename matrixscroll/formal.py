"""Formal property registry — links TLA+ models to Python implementation.

See formal/PROPERTIES.md and formal/tla/*.tla. Hypothesis tests cover runtime;
TLC covers design-level state exploration before code changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PropertyKind = Literal["safety", "liveness"]


@dataclass(frozen=True, slots=True)
class FormalProperty:
    id: str
    kind: PropertyKind
    module: str
    invariant: str
    implementation: str
    hypothesis_id: str | None = None


FORMAL_PROPERTIES: tuple[FormalProperty, ...] = (
    FormalProperty("F-P1", "safety", "CanonicalBytes.tla", "Inv_VerifyImpliesUntampered", "crypto_backend.verify", "P1"),
    FormalProperty("F-P2", "safety", "CanonicalBytes.tla", "Inv_TamperBreaksVerify", "crypto_backend.verify", "P2"),
    FormalProperty("F-P3", "safety", "CanonicalBytes.tla", "Inv_WrongKeyRejects", "crypto_backend.verify", "P3"),
    FormalProperty("F-P4", "safety", "CanonicalBytes.tla", "Inv_NoVerifyWhileUnsigned", "canonical JSON encode", "P4"),
    FormalProperty("F-G1", "safety", "ScrollGate.tla", "Inv_EnforceNoMergeUnlessAllValid", "gate.verify_envelope_range"),
    FormalProperty("F-G3", "safety", "ScrollGate.tla", "Inv_ValidRangeImpliesPass", "gate.verify_envelope_range"),
    FormalProperty("F-G4", "safety", "ScrollGate.tla", "Inv_TamperFailsGate", "gate.verify_commit_envelope_for_sha"),
    FormalProperty("F-A1", "safety", "AuthorityFive.tla", "Inv_NoPurchaseWithoutGrant", "mandate.intent (roadmap)"),
    FormalProperty("F-A2", "safety", "AuthorityFive.tla", "Inv_NoPaymentWithoutPaymentGrant", "mandate.cart (roadmap)"),
    FormalProperty("F-A5", "safety", "AuthorityFive.tla", "Inv_SearchNeverImpliesPurchase", "mandate grants"),
    FormalProperty("F-O1", "safety", "OrgPlanSync.tla", "Inv_OrgNeverBelowEntitlement", "syncOrganizationFromEntitlement"),
    FormalProperty("F-O3", "safety", "OrgPlanSync.tla", "Inv_ScopesMatchPlan", "defaultScopesForPlan"),
)


def property_ids() -> list[str]:
    return [p.id for p in FORMAL_PROPERTIES]


def by_hypothesis_id(hypothesis_id: str) -> list[FormalProperty]:
    return [p for p in FORMAL_PROPERTIES if p.hypothesis_id == hypothesis_id]
