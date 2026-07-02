---- MODULE AuthorityFive ----
\* Formal model: five separate commercial authorities (Search, Purchase, Payment,
\* Substitution, Renewal) — aligned with autonomous commerce governance essays.
\* Maps F-A1..F-A5; target implementation: matrixscroll mandate schemas (roadmap).

EXTENDS FiniteSets, Sequences

CONSTANTS MaxSpend

VARIABLES
    grants,          \* authority flags granted to agent
    spent,           \* cumulative spend in session
    purchaseOpen,    \* agent has an open purchase context
    vendor,          \* active vendor id
    altVendor,       \* substitution target
    actionLog        \* audit trail

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
    /\ [][Next]_<<grants, spent, purchaseOpen, vendor, altVendor, actionLog>>

\* --- Safety: nothing bad (unauthorized commerce) ---

Inv_TypeOK == TypeOK

Inv_NoPurchaseWithoutGrant ==
    purchaseOpen => grants["purchase"]

Inv_NoPaymentWithoutPaymentGrant ==
    (spent > 0) => grants["payment"]

Inv_NoPaymentWithoutPurchaseContext ==
    (spent > 0) => purchaseOpen

Inv_NoSubstitutionWithoutGrant ==
    vendor = "v2" => grants["substitution"]

Inv_SearchNeverImpliesPurchase ==
    ~grants["purchase"] => ~purchaseOpen

Inv_SpendWithinMax ==
    spent <= MaxSpend

\* --- Liveness: granted actions can occur ---

Live_GrantedSearchPossible ==
    [](grants["search"] => <>(Len(actionLog) > 0))

====
