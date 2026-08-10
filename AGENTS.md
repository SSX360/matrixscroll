# AGENTS.md

Prose rules for this repository live in [`CLAUDE.md`](CLAUDE.md). Read it before
writing or editing any user-facing text. The condensed version:

- Active voice, sentence-case headings, present tense, second person.
- Every paragraph must name something a reader could look up.
- No em-dashes (—) and no en-dash separators ( – ). Use a hyphen, comma, period,
  or parentheses.
- One negative-parallelism construction per page, maximum.
- Banned: seamless, cutting-edge, robust, game-changer, unleash, elevate,
  next-gen, revolutionize, delve, tapestry, leverage, harness, empower.
- Naming DORA, PCI DSS, the EU AI Act, SOC 2, NIST, the SSDF, or the FS-AI RMF
  obliges the file to carry "evidence mapping, not a certification claim".
  Never assert that anything is certified or compliant.
- The shipping version is `0.6.3`, per `pyproject.toml` and
  `https://pypi.org/pypi/matrixscroll/json`. Pin it explicitly in every install
  example.
- Hardware (SE050, Pico 2 W) is a bench prototype, not generally available. Say
  so every time.
- Never delete or soften an "Honest limits" section.

## Commit attribution

Commit envelopes detect `actor_type` and `tool` from the environment, so a
commit you make is recorded as `agent` with your tool name. Do not set
`MATRIXSCROLL_ACTOR_TYPE=human` to make a range look human-authored, and do not
edit or re-sign an envelope that is already published. See
[`docs/explanation/actor-attribution.md`](docs/explanation/actor-attribution.md).

Run `vale --minAlertLevel=error` before you start and again before you finish.
The linter gets the last word, never the model. The full guide is the
`ssx360-prose` Skill and
[`docs/explanation/style-supplement.md`](docs/explanation/style-supplement.md).

## Building the docs

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

The documentation follows [Diátaxis](https://diataxis.fr/) and is migrating
incrementally. Legacy flat files under `docs/` are still authoritative for their
subjects and are listed in `exclude_docs` in `mkdocs.yml` until migrated.
