---- MODULE AuthorityFive ----
\* Formal model: five separate commercial authorities (Search, Purchase, Payment,
\* Substitution, Renewal) — aligned with autonomous commerce governance essays.
\* Maps F-A1..F-A5; target implementation: matrixscroll mandate schemas (roadmap).

\* Naturals is required explicitly: the standard Sequences module only takes a
\* LOCAL INSTANCE of it, so Nat and the arithmetic operators are not re-exported.
EXTENDS FiniteSets, Sequences, Naturals

CONSTANTS MaxSpend

VARIABLES
    grants,          \* authority flags granted to agent
    spent,           \* cumulative spend in session
    purchaseOpen,    \* agent has an open purchase context
    vendor,          \* active vendor id
    altVendor,       \* substitution target
    actionLog        \* audit trail

vars == <<grants, spent, purchaseOpen, vendor, altVendor, actionLog>>

AuthorityFields == {"search", "purchase", "payment", "substitution", "renewal"}

EmptyGrants ==
    [a \in AuthorityFields |-> FALSE]

TypeOK ==
    /\ grants \in [AuthorityFields -> BOOLEAN]
    /\ spent \in Nat
    /\ spent <= MaxSpend
    /\ purchaseOpen \in BOOLEAN
    /\ vendor \in {"none", "v1", "v2"}
    /\ altVendor \in {"none", "v1", "v2"}
    /\ actionLog \in Seq(AuthorityFields \cup {"pay", "substitute", "renew"})

Init ==
    /\ grants = EmptyGrants
    /\ spent = 0
    /\ purchaseOpen = FALSE
    /\ vendor = "none"
    /\ altVendor = "none"
    /\ actionLog = <<>>

Grant(a) ==
    /\ a \in AuthorityFields
    /\ grants' = [grants EXCEPT ![a] = TRUE]
    /\ UNCHANGED <<spent, purchaseOpen, vendor, altVendor, actionLog>>

Revoke(a) ==
    /\ a \in AuthorityFields
    /\ grants' = [grants EXCEPT ![a] = FALSE]
    /\ UNCHANGED <<spent, purchaseOpen, vendor, altVendor, actionLog>>

DoSearch ==
    /\ grants["search"]
    /\ actionLog' = Append(actionLog, "search")
    /\ UNCHANGED <<grants, spent, purchaseOpen, vendor, altVendor>>

DoPurchase ==
    /\ grants["purchase"]
    /\ purchaseOpen' = TRUE
    /\ vendor' = "v1"
    /\ actionLog' = Append(actionLog, "purchase")
    /\ UNCHANGED <<grants, spent, altVendor>>

DoPayment ==
    /\ grants["payment"]
    /\ purchaseOpen
    /\ spent < MaxSpend
    /\ spent' = spent + 1
    /\ actionLog' = Append(actionLog, "pay")
    /\ UNCHANGED <<grants, purchaseOpen, vendor, altVendor>>

DoSubstitution ==
    /\ grants["substitution"]
    /\ purchaseOpen
    /\ vendor = "v1"
    /\ altVendor' = "v2"
    /\ vendor' = "v2"
    /\ actionLog' = Append(actionLog, "substitute")
    /\ UNCHANGED <<grants, spent, purchaseOpen>>

DoRenewal ==
    /\ grants["renewal"]
    /\ purchaseOpen
    /\ actionLog' = Append(actionLog, "renew")
    /\ UNCHANGED <<grants, spent, purchaseOpen, vendor, altVendor>>

\* Escalation bugs: action without explicit grant
EscalatePurchaseFromSearch ==
    /\ ~grants["purchase"]
    /\ purchaseOpen' = TRUE
    /\ actionLog' = Append(actionLog, "purchase")
    /\ UNCHANGED <<grants, spent, vendor, altVendor>>

EscalatePaymentWithoutGrant ==
    /\ ~grants["payment"]
    /\ purchaseOpen
    /\ spent' = spent + 1
    /\ actionLog' = Append(actionLog, "pay")
    /\ UNCHANGED <<grants, purchaseOpen, vendor, altVendor>>

Next ==
    \/ \E a \in AuthorityFields : Grant(a)
    \/ \E a \in AuthorityFields : Revoke(a)
    \/ DoSearch
    \/ DoPurchase
    \/ DoPayment
    \/ DoSubstitution
    \/ DoRenewal

\* Bug exploration (disabled in CI — enable in Toolbox to generate counterexamples):
\*   \/ EscalatePurchaseFromSearch
\*   \/ EscalatePaymentWithoutGrant

Spec ==
    /\ Init
    /\ [][Next]_vars

\* Finite-model bound: actionLog is an append-only audit trail, so the reachable
\* state space is infinite. Cap the trace length for TLC.
StateConstraint ==
    Len(actionLog) <= 4

\* --- Safety: nothing bad (unauthorized commerce) ---
\*
\* An authority governs the moment an action is *taken*, not every state that
\* follows it. Revoking a grant after an authorized action must not retroactively
\* make the earlier action illegal, so F-A1..F-A5 constrain steps, not states.

Inv_TypeOK == TypeOK

\* F-A1: a purchase context only ever opens while the purchase authority is held
Prop_NoPurchaseWithoutGrant ==
    [][ (~purchaseOpen /\ purchaseOpen') => grants["purchase"] ]_vars

\* F-A2: spend only ever increases while the payment authority is held
Prop_NoPaymentWithoutPaymentGrant ==
    [][ (spent' > spent) => grants["payment"] ]_vars

Inv_NoPaymentWithoutPurchaseContext ==
    (spent > 0) => purchaseOpen

\* F-A3: the vendor is only ever swapped while the substitution authority is held
Prop_NoSubstitutionWithoutGrant ==
    [][ (vendor # "v2" /\ vendor' = "v2") => grants["substitution"] ]_vars

\* F-A4: a renewal is only ever recorded while the renewal authority is held.
\* DoRenewal is the only action that appends "renew" to the audit trail.
Prop_NoRenewalWithoutGrant ==
    [][ (actionLog' = Append(actionLog, "renew")) => grants["renewal"] ]_vars

\* F-A5: no authority other than purchase escalates into a purchase. In this model
\* that is the contrapositive of F-A1, stated from the escalation side.
Prop_SearchNeverImpliesPurchase ==
    [][ (~grants["purchase"] /\ ~purchaseOpen) => ~purchaseOpen' ]_vars

Inv_SpendWithinMax ==
    spent <= MaxSpend

\* --- Liveness: granted actions can occur ---

Live_GrantedSearchPossible ==
    [](grants["search"] => <>(Len(actionLog) > 0))

====
