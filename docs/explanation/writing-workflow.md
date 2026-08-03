# The writing workflow

Prose in this project passes through three stages in a fixed order: Vale, then a
constrained LLM pass, then Vale again as the CI gate. The order is the point.
This page explains why, and is honest about what the arrangement cannot do.

## The sandwich

```text
1. vale --minAlertLevel=error       deterministic, pre-commit
        |
        v
2. LLM pass constrained by CLAUDE.md   probabilistic, human-reviewed
        |
        v
3. vale-cli/vale-action, fail_on_error: true   deterministic, CI gate
```

### Stage 1: Vale first

Run the linter before a model touches the text. Vale catches the mechanical
defects cheaply and exactly: banned vocabulary, em-dashes, wordiness, missing
compliance hedges. Fixing them first means the model spends its attention on
things only a reader can judge, and it means the model is never asked to
"improve the writing", which is the instruction that produces slop.

### Stage 2: the LLM pass

An LLM reads what Vale cannot: whether a paragraph names anything real, whether
a claim is checkable, whether a section ties a bow it has not earned. The pass is
constrained by `CLAUDE.md`, which carries the always-on rules, and by the
[style supplement](style-supplement.md) loaded on demand.

The questions this stage answers:

- Does this paragraph name a real thing, or does it gesture at a category?
- Is every number, version, and date checkable against a source?
- Does the section end by restating itself? Cut the restatement.
- Is there more than one negative-parallelism construction on the page?
- Does a hardware or compliance claim overstate what actually exists?

### Stage 3: Vale last

The linter gets the last word, never the model. An LLM pass reliably reintroduces
the patterns it was asked to remove, because the generation process that produces
good rewrites is the same one that produces "seamlessly" and em-dashes. Running
the deterministic gate after the probabilistic step is the only way to know the
rewrite did not undo the cleanup.

`fail_on_error: true` is mandatory on the CI action. reviewdog exits `0` by
default even when it reports errors, so a workflow without that input is
decorative: it renders annotations and merges anyway.

## Why the ordering matters

Put the LLM last and you have a gate whose output distribution you do not
control. Put it first and its work gets audited. The pipeline is designed so
that the final state of any document is one a deterministic tool has approved.

That also makes review tractable. A reviewer reading a pull request knows the
mechanical layer is already clean and can spend attention on whether the claims
are true.

## What this does not achieve

A clean Vale run is not proof the copy reads human. This is the most important
sentence on the page, and it should be read as a limit on the whole apparatus.

Vale operates on words and punctuation. Detection research has moved past both.
A University of Maryland and Google DeepMind preprint submitted 3 April 2026,
introducing StoryScope, tested on 61,608 stories and reported 93.2% macro-F1
(0.96 AUPRC) at distinguishing human from AI text using narrative features
alone, with no word-level analysis at all. Two of the discriminating features:
AI narrators explicitly explain the theme 77% of the time versus 52% for humans,
and 79% of AI stories contain no subplots.

Translate that to technical writing. The tells that survive a lint pass are
structural: explaining the point instead of demonstrating it, resolving every
tension a section raises, giving each subsection the same shape and weight,
never leaving a thread hanging because a real writer got interested in something
else. No `existence` rule catches any of that.

So the honest claim for this stack is bounded. It removes the vocabulary and
punctuation fingerprints deterministically and reproducibly. It does not make
prose read as human-written, and anyone treating a green CI check as evidence of
that has misread what the check measures. The structural layer is a human
editing job, and stage 2 is where a person has to actually read the thing.

## Prior art evaluated

| Project | Verdict |
| --- | --- |
| [`tbhb/vale-ai-tells`](https://github.com/tbhb/vale-ai-tells) | Adopted as a package. MIT, 73 rule files, actively maintained, ships an `ai-tells-commits` style for commit messages. Fitting for a provenance tool to lint its own commit log. |
| [`hardikpandya/stop-slop`](https://github.com/hardikpandya/stop-slop) | Not vendored. Overlaps heavily with `ai-tells` at the vocabulary layer, and a Skill cannot enforce anything in CI. The deterministic layer is the one worth owning. |
| `Xamfonos/technical-writing-best-practices` | Not vendored. The 26 principles are largely a restatement of the Google Developer Documentation Style Guide, which is already the adopted standard. Adopting both creates two sources of truth. |
| DeleteSlop 28-pattern checklist | Folded in selectively. Several patterns became tokens in `SSX360.Slop`; the rest duplicated `ai-tells`. |
| Metabase style-guide-review skill pattern | Adopted as a *pattern*, not as content. The heavy guide lives in an on-demand Skill; only the always-on rules live in `CLAUDE.md`. |

The reasoning throughout: own the deterministic layer, borrow the probabilistic
layer, and never let two documents claim to be the style guide.
