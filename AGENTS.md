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
- The published version is `0.7.0`, per `pyproject.toml` and
  `https://pypi.org/pypi/matrixscroll/json`. Pin it explicitly in every install
  example. Unreleased tree changes may retarget the software PQC default to
  `ml-dsa-87`; do not claim that default on PyPI until the release that ships it.
- SSX360 produces the SE050 USB signer and supplies it through direct inquiry.
  Distinguish direct-contact availability from self-service or retail distribution.
- Never delete or soften a "Verification boundaries" section.
- Do not claim CNSA 2.0 certification, FIPS CMVP validation, or NSA approval.
  Naming ML-DSA-87 as the Category 5 / CNSA 2.0 signature parameter set is
  parameter readiness only.

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
