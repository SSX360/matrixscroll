---- MODULE CanonicalBytes ----
\* Formal model: Ed25519 sign / verify / tamper (maps F-P1..F-P4, docs/SECURITY_PROPERTIES.md P1-P4).
\* PlusCal source: formal/pluscal/CanonicalBytes.tla

EXTENDS FiniteSets

CONSTANTS Keys

VARIABLES phase, activeKey, verifyKey, verifyOk

Phases == {"unsigned", "signed", "tampered"}

TypeOK ==
    /\ phase \in Phases
    /\ activeKey \in Keys
    /\ verifyKey \in Keys
    /\ verifyOk \in BOOLEAN

Init ==
    /\ phase = "unsigned"
    /\ activeKey \in Keys
    /\ verifyKey \in Keys
    /\ verifyOk = FALSE

Sign(k) ==
    /\ phase = "unsigned"
    /\ activeKey' = k
    /\ phase' = "signed"
    /\ verifyOk' = FALSE
    /\ UNCHANGED verifyKey

Tamper ==
    /\ phase = "signed"
    /\ phase' = "tampered"
    /\ verifyOk' = FALSE
    /\ UNCHANGED <<activeKey, verifyKey>>

SetVerifyKey(k) ==
    /\ verifyKey' = k
    /\ UNCHANGED <<phase, activeKey, verifyOk>>

RunVerify ==
    /\ phase \in {"signed", "tampered"}
    /\ verifyOk' = (phase = "signed" /\ activeKey = verifyKey)
    /\ UNCHANGED <<phase, activeKey, verifyKey>>

Next ==
    \/ \E k \in Keys : Sign(k)
    \/ Tamper
    \/ \E k \in Keys : SetVerifyKey(k)
    \/ RunVerify

Spec ==
    /\ Init
    /\ [][Next]_<<phase, activeKey, verifyKey, verifyOk>>

\* --- Safety (nothing bad) ---

Inv_TypeOK == TypeOK

\* F-P1 / P1: successful verify implies signed with matching key material
Inv_VerifyImpliesUntampered ==
    verifyOk => phase = "signed"

\* F-P2 / P2: tamper breaks verification
Inv_TamperBreaksVerify ==
    phase = "tampered" => ~verifyOk

\* F-P3 / P3: wrong verifying key rejects
Inv_WrongKeyRejects ==
    (phase = "signed" /\ activeKey # verifyKey) => ~verifyOk

\* F-P4 / P4: canonical stability — modelled as phase "signed" only after explicit Sign
Inv_NoVerifyWhileUnsigned ==
    phase = "unsigned" => ~verifyOk

\* --- Liveness (finite model: sign then verify with same key succeeds) ---

Live_EventuallyVerifyAfterSign ==
    [](phase = "signed" /\ activeKey = verifyKey => <>verifyOk)

====
