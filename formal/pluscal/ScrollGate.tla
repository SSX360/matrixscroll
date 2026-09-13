---- MODULE ScrollGate ----
EXTENDS FiniteSets

\* Non-normative PlusCal sketch of the gate. formal/tla/ScrollGate.tla is
\* hand-maintained and is the module CI checks; it is not generated from this file.
\* This sketch omits the gatePass/evaluated cache invalidation modelled there.

\*--algorithm ScrollGate
variables status \in [Commits -> {"missing", "valid", "invalid", "tampered"}],
          gateMode \in {"warn", "enforce"},
          gatePass \in BOOLEAN,
          merged \in BOOLEAN;

define
  allValid == \A c \in Commits : status[c] = "valid"
end define;

fair process Commit \in Commits
begin Sign:
  await status[self] \in {"missing", "invalid"};
  status[self] := "valid";
  goto Sign
or Tamper:
  await status[self] = "valid";
  status[self] := "tampered";
  goto Sign
end process;

fair process Gate
begin Eval:
  gatePass := allValid;
  if gateMode = "enforce" then
    merged := gatePass;
  elsif allValid then
    merged := TRUE;
  end if;
  goto Eval
or WarnMerge:
  await gateMode = "warn" /\ ~gatePass;
  merged := TRUE;
  goto Eval
end process;
\*--

====
