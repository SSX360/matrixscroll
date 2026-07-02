---- MODULE DualSignature ----
\* Formal model: Ed25519 verify path independent of optional PQC overlay (POC 2 / Q-Day design).
\* Maps to canonical_bytes excluding pqc_signatures (commit b4d743e).

EXTENDS FiniteSets

VARIABLES ed25519Ok, pqcAttached, pqcVerified, policyRequirePqc, gateOk

Init ==
    /\ ed25519Ok = FALSE
    /\ pqcAttached = FALSE
    /\ pqcVerified = FALSE
    /\ policyRequirePqc \in BOOLEAN
    /\ gateOk = FALSE

SignEd25519 ==
    /\ ed25519Ok' = TRUE
    /\ UNCHANGED <<pqcAttached, pqcVerified, policyRequirePqc, gateOk>>

AttachPqc ==
    /\ ed25519Ok
    /\ pqcAttached' = TRUE
    /\ pqcVerified' = FALSE
    /\ UNCHANGED <<ed25519Ok, policyRequirePqc, gateOk>>

VerifyPqc ==
    /\ pqcAttached
    /\ pqcVerified' = TRUE
    /\ UNCHANGED <<ed25519Ok, pqcAttached, policyRequirePqc, gateOk>>

EvalGate ==
    /\ gateOk' = IF policyRequirePqc
                  THEN ed25519Ok /\ pqcAttached /\ pqcVerified
                  ELSE ed25519Ok
    /\ UNCHANGED <<ed25519Ok, pqcAttached, pqcVerified, policyRequirePqc>>

TamperEd25519 ==
    /\ ed25519Ok
    /\ ed25519Ok' = FALSE
    /\ gateOk' = FALSE
    /\ UNCHANGED <<pqcAttached, pqcVerified, policyRequirePqc>>

TogglePolicy ==
    /\ policyRequirePqc' = ~policyRequirePqc
    /\ UNCHANGED <<ed25519Ok, pqcAttached, pqcVerified, gateOk>>

Next ==
    \/ SignEd25519
    \/ AttachPqc
    \/ VerifyPqc
    \/ EvalGate
    \/ TamperEd25519
    \/ TogglePolicy

Spec ==
    /\ Init
    /\ [][Next]_<<ed25519Ok, pqcAttached, pqcVerified, policyRequirePqc, gateOk>>

Inv_Ed25519Required ==
    gateOk => ed25519Ok

Inv_PqcOverlayNeverSkipsEd25519 ==
    pqcAttached => ed25519Ok

Inv_RequirePqcImpliesVerified ==
    (policyRequirePqc /\ gateOk) => (pqcAttached /\ pqcVerified)

Inv_TamperBreaksGate ==
    ~ed25519Ok => ~gateOk

====
