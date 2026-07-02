---- MODULE ScrollGate ----
\* Formal model: Scroll Gate PR merge semantics (maps F-G1..F-G4, matrixscroll/gate.py).
\* PlusCal source: formal/pluscal/ScrollGate.tla

EXTENDS FiniteSets

CONSTANTS Commits

VARIABLES status, gateMode, gatePass, merged

CommitStates == {"missing", "valid", "invalid", "tampered"}

TypeOK ==
    /\ status \in [Commits -> CommitStates]
    /\ gateMode \in {"warn", "enforce"}
    /\ gatePass \in BOOLEAN
    /\ merged \in BOOLEAN

AllValid ==
    \A c \in Commits : status[c] = "valid"

Init ==
    /\ status = [c \in Commits |-> "missing"]
    /\ gateMode \in {"warn", "enforce"}
    /\ gatePass = FALSE
    /\ merged = FALSE

Sign(c) ==
    /\ status[c] \in {"missing", "invalid"}
    /\ status' = [status EXCEPT ![c] = "valid"]
    /\ UNCHANGED <<gateMode, gatePass, merged>>

Invalidate(c) ==
    /\ status[c] = "missing"
    /\ status' = [status EXCEPT ![c] = "invalid"]
    /\ UNCHANGED <<gateMode, gatePass, merged>>

Tamper(c) ==
    /\ status[c] = "valid"
    /\ status' = [status EXCEPT ![c] = "tampered"]
    /\ UNCHANGED <<gateMode, gatePass, merged>>

EvalGate ==
    /\ gatePass' = AllValid
    /\ IF gateMode = "enforce"
       THEN merged' = gatePass'
       ELSE IF AllValid
            THEN merged' = TRUE
            ELSE UNCHANGED merged
    /\ UNCHANGED <<status, gateMode>>

\* Warn mode: operator may merge despite failure (advisory CI)
WarnMergeDespiteFail ==
    /\ gateMode = "warn"
    /\ ~gatePass
    /\ merged' = TRUE
    /\ UNCHANGED <<status, gateMode, gatePass>>

ToggleMode ==
    /\ gateMode' = IF gateMode = "warn" THEN "enforce" ELSE "warn"
    /\ UNCHANGED <<status, gatePass, merged>>

Next ==
    \/ \E c \in Commits : Sign(c)
    \/ \E c \in Commits : Invalidate(c)
    \/ \E c \in Commits : Tamper(c)
    \/ EvalGate
    \/ WarnMergeDespiteFail
    \/ ToggleMode

Spec ==
    /\ Init
    /\ [][Next]_<<status, gateMode, gatePass, merged>>

\* --- Safety ---

Inv_TypeOK == TypeOK

\* F-G1: enforce mode never merges unless every commit envelope is valid
Inv_EnforceNoMergeUnlessAllValid ==
    (gateMode = "enforce" /\ merged) => AllValid

\* F-G3: all valid => gate passes
Inv_ValidRangeImpliesPass ==
    AllValid => gatePass

\* F-G4: any tampered commit in range prevents pass
Inv_TamperFailsGate ==
    (\E c \in Commits : status[c] = "tampered") => ~gatePass

\* F-G2: warn mode may merge even when gate fails (documented advisory path)
Inv_WarnAllowsAdvisoryMerge ==
    (gateMode = "warn" /\ merged /\ ~gatePass) => TRUE

\* --- Liveness ---

Live_FullySignedEventuallyPass ==
    []<>(AllValid => gatePass)

====
