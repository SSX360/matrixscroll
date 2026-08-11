# Formal property registry

Machine-readable IDs link TLA+ invariants, Hypothesis tests, and production code.

Properties whose name begins with `Prop_` are temporal action properties, declared
with `PROPERTY` in the `.cfg`. They constrain the step in which something happens
rather than every reachable state, which is the correct form for a guarantee about
an event: revoking an authority, or switching the gate to enforce mode, must not
retroactively invalidate an action that was legitimate when it was taken.
Names beginning with `Inv_` are state invariants declared with `INVARIANT`.

## Cryptographic core (`CanonicalBytes.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-P1** | Safety | `Inv_VerifyImpliesUntampered` | P1 Sign-verify roundtrip |
| **F-P2** | Safety | `Inv_TamperBreaksVerify` | P2 Tamper detection |
| **F-P3** | Safety | `Inv_WrongKeyRejects` | P3 Wrong-key rejection |
| **F-P4** | Safety | `Inv_NoVerifyWhileUnsigned` | P4 Canonical determinism |
| **F-L1** | Liveness | `Live_EventuallyVerifyAfterSign` | Post-sign verify succeeds (finite model) |

## Scroll Gate (`ScrollGate.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-G1** | Safety | `Prop_EnforceNoMergeUnlessAllValid` | `verify_envelope_range`, enforce CI |
| **F-G2** | Safety | `Inv_WarnAllowsAdvisoryMerge` | `continue-on-error` warn workflows |
| **F-G3** | Safety | `Inv_ValidRangeImpliesPass` | Gate `ok: true` semantics |
| **F-G4** | Safety | `Inv_TamperFailsGate` | Tampered envelope in range → fail |
| **F-G5** | Safety | `Inv_EmptyRangeNeverPasses` | Empty range → `ok: false`, `empty_range: true` |
| **F-L2** | Liveness | `Live_FullySignedEventuallyPass` | All valid → gate pass reachable |

`Inv_ValidRangeImpliesPass` carries a `~RangeEmpty` guard. `AllValid` quantifies
over `Commits` and is vacuously true when that set is empty, so without the guard
the model would license the fail-open that `gate.verify_envelope_range` just
stopped doing.

## Five authorities (`AuthorityFive.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-A1** | Safety | `Prop_NoPurchaseWithoutGrant` | Mandate purchase bit |
| **F-A2** | Safety | `Prop_NoPaymentWithoutPaymentGrant` | Separate payment authority |
| **F-A3** | Safety | `Prop_NoSubstitutionWithoutGrant` | Vendor swap policy |
| **F-A4** | Safety | `Prop_NoRenewalWithoutGrant` | Repeat/escalate bounds |
| **F-A5** | Safety | `Prop_SearchNeverImpliesPurchase` | Search ⊄ purchase escalation |
| **F-L3** | Liveness | `Live_GrantedSearchPossible` | Granted action can fire |

`AuthorityFive.tla` also carries two supporting invariants that are checked in CI
but are not registry entries: `Inv_NoPaymentWithoutPurchaseContext` and
`Inv_SpendWithinMax`.

## Org plan sync (`OrgPlanSync.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-O1** | Safety | `Inv_OrgNeverBelowEntitlement` | `syncOrganizationFromEntitlement` |
| **F-O2** | Safety | `Prop_OrgMonotonic` | `higherPlan` lattice |
| **F-O3** | Safety | `Inv_ScopesMatchPlan` | `defaultScopesForPlan` |
| **F-L4** | Liveness | `Live_EventuallySyncedAfterWebhook` | Post-webhook sync action |

## Dual signature / PQC overlay (`DualSignature.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-D1** | Safety | `Inv_Ed25519Required` | Gate pass requires the Ed25519 signature |
| **F-D2** | Safety | `Prop_PqcOverlayNeverSkipsEd25519` | PQC overlay attaches only over a valid Ed25519 signature |
| **F-D3** | Safety | `Inv_RequirePqcImpliesVerified` | `policyRequirePqc` gate pass implies PQC verified |
| **F-D4** | Safety | `Inv_TamperBreaksGate` | Broken Ed25519 signature fails the gate |

## Status

| Module | TLC default config | CI |
|--------|-------------------|-----|
| CanonicalBytes | ✅ finite | `formal-verify.yml` |
| ScrollGate | ✅ finite | `formal-verify.yml` |
| AuthorityFive | ✅ finite (`actionLog` bounded by `StateConstraint`) | `formal-verify.yml` |
| OrgPlanSync | ✅ finite | `formal-verify.yml` |
| DualSignature | ✅ finite | `formal-verify.yml` |
