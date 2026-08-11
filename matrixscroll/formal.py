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
    FormalProperty("F-G1", "safety", "ScrollGate.tla", "Prop_EnforceNoMergeUnlessAllValid", "gate.verify_envelope_range"),
    FormalProperty("F-G3", "safety", "ScrollGate.tla", "Inv_ValidRangeImpliesPass", "gate.verify_envelope_range"),
    FormalProperty("F-G4", "safety", "ScrollGate.tla", "Inv_TamperFailsGate", "gate.verify_commit_envelope_for_sha"),
    FormalProperty("F-G5", "safety", "ScrollGate.tla", "Inv_EmptyRangeFailsClosed", "gate.verify_envelope_range (default allow_empty=False)"),
    FormalProperty("F-A1", "safety", "AuthorityFive.tla", "Prop_NoPurchaseWithoutGrant", "mandate.intent (roadmap)"),
    FormalProperty("F-A2", "safety", "AuthorityFive.tla", "Prop_NoPaymentWithoutPaymentGrant", "mandate.cart (roadmap)"),
    FormalProperty("F-A3", "safety", "AuthorityFive.tla", "Prop_NoSubstitutionWithoutGrant", "vendor swap policy (roadmap)"),
    FormalProperty("F-A4", "safety", "AuthorityFive.tla", "Prop_NoRenewalWithoutGrant", "renewal bounds (roadmap)"),
    FormalProperty("F-A5", "safety", "AuthorityFive.tla", "Prop_SearchNeverImpliesPurchase", "mandate grants"),
    FormalProperty("F-O1", "safety", "OrgPlanSync.tla", "Inv_OrgNeverBelowEntitlement", "syncOrganizationFromEntitlement"),
    FormalProperty("F-O2", "safety", "OrgPlanSync.tla", "Prop_OrgMonotonic", "higherPlan lattice"),
    FormalProperty("F-O3", "safety", "OrgPlanSync.tla", "Inv_ScopesMatchPlan", "defaultScopesForPlan"),
    FormalProperty("F-D1", "safety", "DualSignature.tla", "Inv_Ed25519Required", "canonical_bytes ed25519 path"),
    FormalProperty("F-D2", "safety", "DualSignature.tla", "Prop_PqcOverlayNeverSkipsEd25519", "crypto_backend.pqc_sign overlay"),
    FormalProperty("F-D3", "safety", "DualSignature.tla", "Inv_RequirePqcImpliesVerified", "crypto_backend.pqc_verify"),
    FormalProperty("F-D4", "safety", "DualSignature.tla", "Inv_TamperBreaksGate", "gate.verify_commit_envelope_for_sha"),
)


def property_ids() -> list[str]:
    return [p.id for p in FORMAL_PROPERTIES]


def by_hypothesis_id(hypothesis_id: str) -> list[FormalProperty]:
    return [p for p in FORMAL_PROPERTIES if p.hypothesis_id == hypothesis_id]
