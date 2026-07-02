# Formal methods (TLA+ / PlusCal)

Matrix Scroll treats **protocol rules as mathematics first, implementations second**.

We model core governance at the root with [TLA+](https://lamport.azurewebsites.net/tla/tla.html) and
[PlusCal](https://lamport.azurewebsites.net/tla/pluscal.html), then run the **TLC model checker** to
exhaustively explore state space and emit **counterexample traces** when an invariant breaks.

This complements Hypothesis property tests in `tests/test_security_properties.py` — Hypothesis
fuzzes implementations; TLC falsifies **designs** before code ships.

## Layout

| File | Domain | Maps to code |
|------|--------|--------------|
| [`tla/CanonicalBytes.tla`](tla/CanonicalBytes.tla) | Sign / verify / tamper | `matrixscroll/crypto_backend.py`, `envelope-verify.ts` |
| [`tla/ScrollGate.tla`](tla/ScrollGate.tla) | PR merge gate | `matrixscroll/gate.py`, `ssx360 check` |
| [`tla/AuthorityFive.tla`](tla/AuthorityFive.tla) | Five commercial authorities | AP2 mandate roadmap, WAYE-style governance |
| [`tla/OrgPlanSync.tla`](tla/OrgPlanSync.tla) | Entitlement → org plan lattice | `lib/platform-service.ts` (SSX360) |
| [`pluscal/*.tla`](pluscal/) | Human-editable PlusCal sources | Compile with TLA+ Toolbox → sync `tla/` |
| [`PROPERTIES.md`](PROPERTIES.md) | Property ID registry | `docs/SECURITY_PROPERTIES.md` |

## Safety vs liveness

| Kind | Meaning | Examples here |
|------|---------|---------------|
| **Safety** | Nothing bad happens | Unsigned commits never merge in enforce mode; payment without grant never succeeds |
| **Liveness** | Something good eventually happens | After webhook, org plan eventually reaches entitlement floor; valid PR eventually passable |

## Run TLC locally

### Option A — TLA+ Toolbox (recommended)

1. Install [TLA+ Tools](https://github.com/tlaplus/tlaplus/releases).
2. Open `formal/tla/ScrollGate.tla` in the Toolbox.
3. Create TLC model from `formal/tla/ScrollGate.cfg` → Run.

### Option B — Docker

```bash
docker run --rm -v "$PWD/formal/tla:/tla" -w /tla tlaplus/tlaplus \
  java -cp tla2tools.jar tlc2.TLC -config ScrollGate.cfg ScrollGate.tla
```

### Option C — Repo script

```bash
python scripts/verify_formal.py
```

Skips gracefully when TLC is not installed; CI runs TLC when the Docker image is available.

## PlusCal workflow

1. Edit algorithm in `formal/pluscal/<Module>.tla` (between `\*--algorithm` / `\*--`).
2. Translate with TLA+ Toolbox (*PlusCal → TLA+*).
3. Copy generated TLA+ into `formal/tla/<Module>.tla` (or verify diff).
4. Update `PROPERTIES.md` if invariants changed.

## When a model fails

TLC prints a **counterexample trace** — an exact sequence of states leading to the violation.
Treat it like a failing unit test for the **spec**: fix the model or fix the implementation, never
silence the invariant.

## References

- Leslie Lamport, *Specifying Systems*
- AWS engineering blog on TLA+ for DynamoDB / S3 design
- [`docs/SECURITY_PROPERTIES.md`](../docs/SECURITY_PROPERTIES.md) — implementation property tests
