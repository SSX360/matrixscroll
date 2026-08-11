---- MODULE ScrollGate ----
\* Formal model: Scroll Gate PR merge semantics (maps F-G1..F-G4, matrixscroll/gate.py).
\* This module is hand-maintained and is what CI checks. formal/pluscal/ScrollGate.tla
\* is a non-normative sketch, not the generated source of this file.

EXTENDS FiniteSets

CONSTANTS Commits

VARIABLES status, gateMode, gatePass, merged, evaluated

vars == <<status, gateMode, gatePass, merged, evaluated>>

CommitStates == {"missing", "valid", "invalid", "tampered"}

TypeOK ==
    /\ status \in [Commits -> CommitStates]
    /\ gateMode \in {"warn", "enforce"}
    /\ gatePass \in BOOLEAN
    /\ merged \in BOOLEAN
    /\ evaluated \in BOOLEAN

AllValid ==
    \A c \in Commits : status[c] = "valid"

\* An empty range makes AllValid vacuously true. The gate does not treat that as
\* a pass, because "every commit here is signed" says nothing when the range
\* holds nothing. gate.verify_envelope_range returns ok: false with
\* empty_range: true unless the caller passes allow_empty.
RangeEmpty ==
    Commits = {}

Init ==
    /\ status = [c \in Commits |-> "missing"]
    /\ gateMode \in {"warn", "enforce"}
    /\ gatePass = FALSE
    /\ merged = FALSE
    /\ evaluated = FALSE

\* gatePass / evaluated cache the outcome of the last gate run. Any action that
\* mutates commit status invalidates that cache, exactly as re-signing or
\* tampering invalidates a cached verify result in CanonicalBytes.
Sign(c) ==
    /\ status[c] \in {"missing", "invalid"}
    /\ status' = [status EXCEPT ![c] = "valid"]
    /\ gatePass' = FALSE
    /\ evaluated' = FALSE
    /\ UNCHANGED <<gateMode, merged>>

Invalidate(c) ==
    /\ status[c] = "missing"
    /\ status' = [status EXCEPT ![c] = "invalid"]
    /\ gatePass' = FALSE
    /\ evaluated' = FALSE
    /\ UNCHANGED <<gateMode, merged>>

Tamper(c) ==
    /\ status[c] = "valid"
    /\ status' = [status EXCEPT ![c] = "tampered"]
    /\ gatePass' = FALSE
    /\ evaluated' = FALSE
    /\ UNCHANGED <<gateMode, merged>>

EvalGate ==
    /\ gatePass' = (AllValid /\ ~RangeEmpty)
    /\ evaluated' = TRUE
    /\ IF gateMode = "enforce"
       THEN merged' = gatePass'
       ELSE IF gatePass'
            THEN merged' = TRUE
            ELSE UNCHANGED merged
    /\ UNCHANGED <<status, gateMode>>

\* Warn mode: operator may merge despite failure (advisory CI)
WarnMergeDespiteFail ==
    /\ gateMode = "warn"
    /\ ~gatePass
    /\ merged' = TRUE
    /\ UNCHANGED <<status, gateMode, gatePass, evaluated>>

ToggleMode ==
    /\ gateMode' = IF gateMode = "warn" THEN "enforce" ELSE "warn"
    /\ UNCHANGED <<status, gatePass, merged, evaluated>>

Next ==
    \/ \E c \in Commits : Sign(c)
    \/ \E c \in Commits : Invalidate(c)
    \/ \E c \in Commits : Tamper(c)
    \/ EvalGate
    \/ WarnMergeDespiteFail
    \/ ToggleMode

Spec ==
    /\ Init
    /\ [][Next]_vars

\* --- Safety ---

Inv_TypeOK == TypeOK

\* F-G1: enforce mode never merges unless every commit envelope is valid.
\* This constrains the merge *step*: a merge performed while in warn mode
\* (F-G2, below) stays legitimate if the mode is later switched to enforce,
\* so the guarantee cannot be stated over single states.
Prop_EnforceNoMergeUnlessAllValid ==
    [][ (gateMode = "enforce" /\ ~merged /\ merged') => AllValid ]_vars

\* F-G3: all valid => gate passes, once the gate has actually been run and the
\* range holds at least one commit. Envelope validity cannot imply a gate result
\* that was never computed, and an empty range computes no result about any
\* commit.
Inv_ValidRangeImpliesPass ==
    (evaluated /\ AllValid /\ ~RangeEmpty) => gatePass

\* F-G4: any tampered commit in range prevents pass
Inv_TamperFailsGate ==
    (\E c \in Commits : status[c] = "tampered") => ~gatePass

\* F-G5: an empty range never passes. This is the vacuous-truth case: AllValid
\* holds over the empty set, so without this the gate reports success for a
\* mistyped base ref or a shallow clone.
Inv_EmptyRangeNeverPasses ==
    RangeEmpty => ~gatePass

\* F-G2: warn mode may merge even when gate fails (documented advisory path)
Inv_WarnAllowsAdvisoryMerge ==
    (gateMode = "warn" /\ merged /\ ~gatePass) => TRUE

\* --- Liveness ---

Live_FullySignedEventuallyPass ==
    []<>((AllValid /\ ~RangeEmpty) => gatePass)

====
