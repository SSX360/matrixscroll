# Formal property registry

Machine-readable IDs link TLA+ invariants, Hypothesis tests, and production code.

## Cryptographic core (`CanonicalBytes.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-P1** | Safety | `Inv_VerifyImpliesUntampered` | P1 Sign–verify roundtrip |
| **F-P2** | Safety | `Inv_TamperBreaksVerify` | P2 Tamper detection |
| **F-P3** | Safety | `Inv_WrongKeyRejects` | P3 Wrong-key rejection |
| **F-P4** | Safety | `Inv_CanonicalStable` | P4 Canonical determinism |
| **F-L1** | Liveness | `Live_EventuallyVerifyAfterSign` | Post-sign verify succeeds (finite model) |

## Scroll Gate (`ScrollGate.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-G1** | Safety | `Inv_EnforceNoMergeUnlessAllValid` | `verify_envelope_range`, enforce CI |
| **F-G2** | Safety | `Inv_WarnMayMergeDespiteFail` | `continue-on-error` warn workflows |
| **F-G3** | Safety | `Inv_ValidRangeImpliesPass` | Gate `ok: true` semantics |
| **F-G4** | Safety | `Inv_TamperFailsGate` | Tampered envelope in range → fail |
| **F-L2** | Liveness | `Live_FullySignedEventuallyPass` | All valid → gate pass reachable |

## Five authorities (`AuthorityFive.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-A1** | Safety | `Inv_NoPurchaseWithoutGrant` | Mandate purchase bit |
| **F-A2** | Safety | `Inv_NoPaymentWithoutPaymentGrant` | Separate payment authority |
| **F-A3** | Safety | `Inv_NoSubstitutionWithoutGrant` | Vendor swap policy |
| **F-A4** | Safety | `Inv_NoRenewalWithoutGrant` | Repeat/escalate bounds |
| **F-A5** | Safety | `Inv_SearchNeverImpliesPurchase` | Search ⊄ purchase escalation |
| **F-L3** | Liveness | `Live_GrantedActionEventuallyAllowed` | Granted action can fire |

## Org plan sync (`OrgPlanSync.tla`)

| ID | Type | Invariant / property | Implementation |
|----|------|----------------------|----------------|
| **F-O1** | Safety | `Inv_OrgNeverBelowEntitlement` | `syncOrganizationFromEntitlement` |
| **F-O2** | Safety | `Inv_SyncMonotonic` | `higherPlan` lattice |
| **F-O3** | Safety | `Inv_ScopesMatchPlan` | `defaultScopesForPlan` |
| **F-L4** | Liveness | `Live_EventuallySyncedAfterWebhook` | Post-webhook sync action |

## Status

| Module | TLC default config | CI |
|--------|-------------------|-----|
| CanonicalBytes | ✅ finite | `formal-verify.yml` |
| ScrollGate | ✅ finite | `formal-verify.yml` |
| AuthorityFive | ✅ finite | `formal-verify.yml` |
| OrgPlanSync | ✅ finite | `formal-verify.yml` |
