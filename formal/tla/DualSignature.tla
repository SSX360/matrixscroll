---- MODULE DualSignature ----
\* Formal model: Ed25519 verify path independent of optional PQC overlay (POC 2 / Q-Day design).
\* Maps to canonical_bytes excluding pqc_signatures (commit b4d743e).

EXTENDS FiniteSets

VARIABLES ed25519Ok, pqcAttached, pqcVerified, policyRequirePqc, gateOk

vars == <<ed25519Ok, pqcAttached, pqcVerified, policyRequirePqc, gateOk>>

TypeOK ==
    /\ ed25519Ok \in BOOLEAN
    /\ pqcAttached \in BOOLEAN
    /\ pqcVerified \in BOOLEAN
    /\ policyRequirePqc \in BOOLEAN
    /\ gateOk \in BOOLEAN

Init ==
    /\ ed25519Ok = FALSE
    /\ pqcAttached = FALSE
    /\ pqcVerified = FALSE
    /\ policyRequirePqc \in BOOLEAN
    /\ gateOk = FALSE

\* gateOk caches the outcome of the last gate run. Every action below mutates an
\* input to that decision — a signature, the overlay, or the policy itself — so
\* each one invalidates the cache, as Tamper does in CanonicalBytes.
SignEd25519 ==
    /\ ed25519Ok' = TRUE
    /\ gateOk' = FALSE
    /\ UNCHANGED <<pqcAttached, pqcVerified, policyRequirePqc>>

AttachPqc ==
    /\ ed25519Ok
    /\ pqcAttached' = TRUE
    /\ pqcVerified' = FALSE
    /\ gateOk' = FALSE
    /\ UNCHANGED <<ed25519Ok, policyRequirePqc>>

VerifyPqc ==
    /\ pqcAttached
    /\ pqcVerified' = TRUE
    /\ gateOk' = FALSE
    /\ UNCHANGED <<ed25519Ok, pqcAttached, policyRequirePqc>>

EvalGate ==
    /\ gateOk' = IF policyRequirePqc
                  THEN ed25519Ok /\ pqcAttached /\ pqcVerified
                  ELSE ed25519Ok
    /\ UNCHANGED <<ed25519Ok, pqcAttached, pqcVerified, policyRequirePqc>>

\* Tampering rewrites the canonical bytes, so both signatures over them stop
\* verifying. The overlay stays structurally attached to the envelope.
TamperEd25519 ==
    /\ ed25519Ok
    /\ ed25519Ok' = FALSE
    /\ pqcVerified' = FALSE
    /\ gateOk' = FALSE
    /\ UNCHANGED <<pqcAttached, policyRequirePqc>>

TogglePolicy ==
    /\ policyRequirePqc' = ~policyRequirePqc
    /\ gateOk' = FALSE
    /\ UNCHANGED <<ed25519Ok, pqcAttached, pqcVerified>>

Next ==
    \/ SignEd25519
    \/ AttachPqc
    \/ VerifyPqc
    \/ EvalGate
    \/ TamperEd25519
    \/ TogglePolicy

Spec ==
    /\ Init
    /\ [][Next]_vars

Inv_TypeOK == TypeOK

Inv_Ed25519Required ==
    gateOk => ed25519Ok

\* A PQC overlay is only ever attached to an envelope that already carries a
\* verifying Ed25519 signature. Attachment is structural and survives later
\* tampering, so this constrains the attach step rather than every state.
Prop_PqcOverlayNeverSkipsEd25519 ==
    [][ (~pqcAttached /\ pqcAttached') => ed25519Ok ]_vars

Inv_RequirePqcImpliesVerified ==
    (policyRequirePqc /\ gateOk) => (pqcAttached /\ pqcVerified)

Inv_TamperBreaksGate ==
    ~ed25519Ok => ~gateOk

====
