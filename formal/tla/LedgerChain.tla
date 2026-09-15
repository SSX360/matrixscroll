---- MODULE LedgerChain ----
\* Formal model: hash-linked ledger integrity (SPEC §12, matrixscroll/ledger.py).
\* Toy string hashes; TLC checks link integrity under reorder/omit/fork/truncate.

EXTENDS Integers, Sequences, TLC

CONSTANTS MaxRecords, PayloadSet

VARIABLES records, tip, evaluated, verdict

Record == [index: Nat, prev: STRING, payload: STRING, hash: STRING]

TypeOK ==
    /\ records \in Seq(Record)
    /\ tip \in STRING
    /\ evaluated \in BOOLEAN
    /\ verdict \in {"CONSISTENT", "INCONSISTENT", "INDETERMINATE"}

Init ==
    /\ records = << >>
    /\ tip = "genesis"
    /\ evaluated = FALSE
    /\ verdict = "CONSISTENT"

Append(p) ==
    /\ Len(records) < MaxRecords
    /\ p \in PayloadSet
    /\ LET i == Len(records)
           h == ToString(i) \o "-" \o tip \o "-" \o p
           r == [index |-> i, prev |-> tip, payload |-> p, hash |-> h]
       IN /\ records' = Append(records, r)
          /\ tip' = h
          /\ evaluated' = FALSE
          /\ UNCHANGED verdict

Reorder ==
    /\ Len(records) >= 2
    /\ evaluated
    /\ records' = << records[2], records[1] >> \o Tail(Tail(records))
    /\ tip' = records'[Len(records')].hash
    /\ evaluated' = FALSE
    /\ UNCHANGED verdict

OmitMiddle ==
    /\ Len(records) >= 3
    /\ evaluated
    /\ records' = << records[1] >> \o Tail(Tail(records))
    /\ tip' = records'[Len(records')].hash
    /\ evaluated' = FALSE
    /\ UNCHANGED verdict

Fork ==
    /\ Len(records) >= 1
    /\ evaluated
    /\ LET last == records[Len(records)]
           bad == [last EXCEPT !.prev = "forked",
                               !.hash = "fork-" \o last.hash]
       IN records' = SubSeq(records, 1, Len(records) - 1) \o << bad >>
    /\ tip' = records'[Len(records')].hash
    /\ evaluated' = FALSE
    /\ UNCHANGED verdict

TruncateSuffix ==
    /\ Len(records) >= 2
    /\ evaluated
    /\ records' = SubSeq(records, 1, Len(records) - 1)
    /\ tip' = records'[Len(records')].hash
    /\ evaluated' = FALSE
    /\ UNCHANGED verdict

LinksOK ==
    /\ \A i \in DOMAIN records : records[i].index = i - 1
    /\ Len(records) = 0 \/ records[1].prev = "genesis"
    /\ \A i \in 2..Len(records) : records[i].prev = records[i - 1].hash

Eval ==
    /\ verdict' = IF LinksOK THEN "CONSISTENT" ELSE "INCONSISTENT"
    /\ evaluated' = TRUE
    /\ UNCHANGED <<records, tip>>

Next ==
    \/ \E p \in PayloadSet : Append(p)
    \/ Reorder
    \/ OmitMiddle
    \/ Fork
    \/ TruncateSuffix
    \/ Eval

Spec == Init /\ [][Next]_<<records, tip, evaluated, verdict>>

EvalSound ==
    evaluated => ((verdict = "CONSISTENT") <=> LinksOK)

====
