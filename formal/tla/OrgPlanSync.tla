---- MODULE OrgPlanSync ----
\* Formal model: Stripe entitlement → organization plan lattice (SSX360).
\* Maps F-O1..F-O3; implementation: lib/platform-service.ts syncOrganizationFromEntitlement.

EXTENDS FiniteSets, Naturals

CONSTANTS Plans, PlanRank

VARIABLES entitlement, orgPlan, scopesLevel, webhookPending

vars == <<entitlement, orgPlan, scopesLevel, webhookPending>>

\* Plans = {community, trial, team, enterprise}
\* PlanRank maps plan name -> 0..3
\*
\* A TLC .cfg cannot assign a record literal to a CONSTANT, so the concrete
\* values live here and OrgPlanSync.cfg binds them with a definition override.
\* Plan names are TLA+ strings, not model values, because Init and ScopesForPlan
\* compare against string literals such as "community".
PlansDef == {"community", "trial", "team", "enterprise"}

PlanRankDef == [community |-> 0, trial |-> 1, team |-> 2, enterprise |-> 3]

PlanAtLeast(p, minimum) ==
    PlanRank[p] >= PlanRank[minimum]

HigherPlan(a, b) ==
    IF PlanRank[a] >= PlanRank[b] THEN a ELSE b

ScopesForPlan(p) ==
    IF PlanRank[p] >= PlanRank["team"] THEN 3 ELSE IF PlanRank[p] >= PlanRank["trial"] THEN 2 ELSE 1

TypeOK ==
    /\ entitlement \in Plans
    /\ orgPlan \in Plans
    /\ scopesLevel \in 1..3
    /\ webhookPending \in BOOLEAN

Init ==
    /\ entitlement = "community"
    /\ orgPlan = "community"
    /\ scopesLevel = ScopesForPlan("community")
    /\ webhookPending = FALSE

StripeWebhook(newPlan) ==
    /\ newPlan \in Plans
    /\ entitlement' = HigherPlan(entitlement, newPlan)
    /\ webhookPending' = TRUE
    /\ UNCHANGED <<orgPlan, scopesLevel>>

SyncOrganization ==
    /\ webhookPending
    /\ orgPlan' = HigherPlan(orgPlan, entitlement)
    /\ scopesLevel' = ScopesForPlan(orgPlan')
    /\ webhookPending' = FALSE
    /\ UNCHANGED entitlement

EnsureOrg(plan) ==
    /\ orgPlan' = HigherPlan(orgPlan, plan)
    /\ scopesLevel' = ScopesForPlan(orgPlan')
    /\ UNCHANGED <<entitlement, webhookPending>>

DriftBug ==
    \* Bug we fixed: entitlement team but org stays community
    /\ entitlement = "team"
    /\ orgPlan' = "community"
    /\ UNCHANGED <<entitlement, scopesLevel, webhookPending>>

Next ==
    \/ \E p \in Plans : StripeWebhook(p)
    \/ SyncOrganization
    \/ \E p \in Plans : EnsureOrg(p)

\* Regression bug (org plan drift) — enable in Toolbox only:
\*   \/ DriftBug

Spec ==
    /\ Init
    /\ [][Next]_vars

Inv_TypeOK == TypeOK

\* F-O1: org plan never below entitlement after sync
Inv_OrgNeverBelowEntitlement ==
    ~webhookPending => PlanAtLeast(orgPlan, entitlement)

\* F-O2: sync is monotonic — no step ever downgrades the organization plan.
\* Previously stated as the vacuous literal TRUE, which asserted nothing.
Prop_OrgMonotonic ==
    [][ PlanRank[orgPlan'] >= PlanRank[orgPlan] ]_vars

\* F-O3: scopes track plan tier
Inv_ScopesMatchPlan ==
    scopesLevel = ScopesForPlan(orgPlan)

Live_EventuallySyncedAfterWebhook ==
    [](webhookPending => <>~webhookPending)

====
