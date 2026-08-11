# Formal property registry

Machine-readable IDs link TLA+ invariants, Hypothesis tests, and production code.

Names beginning with `Prop_` identify temporal action properties declared with
`PROPERTY` in the `.cfg`. Each property constrains one event transition.
Reachable-state guarantees use invariants instead. This distinction preserves
the legitimacy of actions taken before a later authority revocation or gate-mode
change.
Names beginning with `Inv_` are state invariants declared with `INVARIANT`.

## Cryptographic core (`CanonicalBytes.tla`)

| ID | Type | Invariant / property | Code path |
|----|------|----------------------|----------------|
| **F-P1** | Safety | `Inv_VerifyImpliesUntampered` | P1 Sign-verify roundtrip |
| **F-P2** | Safety | `Inv_TamperBreaksVerify` | P2 Tamper detection |
| **F-P3** | Safety | `Inv_WrongKeyRejects` | P3 Wrong-key rejection |
| **F-P4** | Safety | `Inv_NoVerifyWhileUnsigned` | P4 Canonical determinism |
| **F-L1** | Liveness | `Live_EventuallyVerifyAfterSign` | Post-sign verify succeeds (finite model) |

## Scroll Gate (`ScrollGate.tla`)

| ID | Type | Invariant / property | Code path |
|----|------|----------------------|----------------|
| **F-G1** | Safety | `Prop_EnforceNoMergeUnlessAllValid` | `verify_envelope_range`, enforce CI |
| **F-G2** | Safety | `Inv_WarnAllowsAdvisoryMerge` | `continue-on-error` warn workflows |
| **F-G3** | Safety | `Inv_ValidRangeImpliesPass` | Gate `ok: true` semantics |
| **F-G4** | Safety | `Inv_TamperFailsGate` | Tampered envelope in range → fail |
| **F-G5** | Safety | `Inv_EmptyRangeFailsClosed` | Empty range → `ok: false`, `empty_range: true` unless the caller explicitly allows it |
| **F-L2** | Liveness | `Live_FullySignedEventuallyPass` | All valid → gate pass reachable |

`Inv_ValidRangeImpliesPass` carries a `~RangeEmpty` guard. `AllValid` quantifies
over `Commits` and is vacuously true when that set is empty, so without the guard
the model would license the fail-open that `gate.verify_envelope_range` just
stopped doing.

`AllowEmpty` models the public API's explicit `allow_empty=True` opt-in. The
default model and code path fail closed; a separate TLC configuration
checks that the opt-in remains labelled and does not contradict F-G5.
`Spec` gives `EvalGate` weak fairness, so a stable, fully signed range cannot
wait forever without evaluation.

## Five authorities (`AuthorityFive.tla`)

| ID | Type | Invariant / property | Code path |
|----|------|----------------------|----------------|
| **F-A1** | Safety | `Prop_NoPurchaseWithoutGrant` | Mandate buy permission |
| **F-A2** | Safety | `Prop_NoPaymentWithoutPaymentGrant` | Separate payment authority |
| **F-A3** | Safety | `Prop_NoSubstitutionWithoutGrant` | Vendor swap policy |
| **F-A4** | Safety | `Prop_NoRenewalWithoutGrant` | Repeat/escalate bounds |
| **F-A5** | Safety | `Prop_SearchNeverImpliesPurchase` | Search never grants buying |
| **F-L3** | Liveness | `Live_GrantedSearchPossible` | Granted action can fire |

CI also checks two supporting invariants in `AuthorityFive.tla` that are not
registry entries: `Inv_NoPaymentWithoutPurchaseContext` and
`Inv_SpendWithinMax`.

## Org plan sync (`OrgPlanSync.tla`)

| ID | Type | Invariant / property | Code path |
|----|------|----------------------|----------------|
| **F-O1** | Safety | `Inv_OrgNeverBelowEntitlement` | `syncOrganizationFromEntitlement` |
| **F-O2** | Safety | `Prop_OrgMonotonic` | `higherPlan` lattice |
| **F-O3** | Safety | `Inv_ScopesMatchPlan` | `defaultScopesForPlan` |
| **F-L4** | Liveness | `Live_EventuallySyncedAfterWebhook` | Post-webhook sync action |

## Dual signature / PQC overlay (`DualSignature.tla`)

| ID | Type | Invariant / property | Code path |
|----|------|----------------------|----------------|
| **F-D1** | Safety | `Inv_Ed25519Required` | Gate pass requires the Ed25519 signature |
| **F-D2** | Safety | `Prop_PqcOverlayNeverSkipsEd25519` | PQC overlay attaches only over a valid Ed25519 signature |
| **F-D3** | Safety | `Inv_RequirePqcImpliesVerified` | `policyRequirePqc` gate pass implies PQC verified |
| **F-D4** | Safety | `Inv_TamperBreaksGate` | Broken Ed25519 signature fails the gate |

## Status

| Module | TLC default config | CI |
|--------|-------------------|-----|
| CanonicalBytes | ✅ finite | `formal-verify.yml` |
| ScrollGate | ✅ finite (default, empty, allow-empty) | `formal-verify.yml` |
| AuthorityFive | ✅ finite (`actionLog` bounded by `StateConstraint`) | `formal-verify.yml` |
| OrgPlanSync | ✅ finite | `formal-verify.yml` |
| DualSignature | ✅ finite | `formal-verify.yml` |
