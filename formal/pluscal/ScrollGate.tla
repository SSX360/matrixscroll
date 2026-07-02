---- MODULE ScrollGate ----
EXTENDS FiniteSets

\* PlusCal algorithm — translate with TLA+ Toolbox to refresh formal/tla/ScrollGate.tla

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
