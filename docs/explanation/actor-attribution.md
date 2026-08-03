# How an envelope decides who wrote a commit

Every commit envelope records `provenance.actor_type` (`human`, `agent`, or
`ci`) and `provenance.tool`. Those two fields are the reason the envelope
exists. A verifier that cannot trust them has nothing left to check.

## The old default was wrong

`build_commit_envelope()` used to read `actor_type` from
`.git/matrixscroll/config.json` and fall back to `human` and `git-cli`.
`matrixscroll hook-install` writes that file once, with those values, and never
revisits them. Any commit an agent made in a clone that had run `hook-install`
was signed as human authorship, and signed correctly, which is worse than
leaving it unsigned: the signature attests to a false claim.

The `refs/notes/matrixscroll` history in `SSX360/digital-rain` carries three
envelopes with `actor_type: human` and `tool: cursor-agent`. The tool name came
from the environment; the actor type came from the stale config file. Those
three records name the defect precisely.

## What happens now

`build_commit_envelope()` inspects the environment before it reads the config
file:

1. `MATRIXSCROLL_ACTOR_TYPE` and `MATRIXSCROLL_TOOL`, if set. An agent harness
   this package does not recognize declares itself here.
2. Agent markers: `CURSOR_AGENT`, `CLAUDECODE`, `CLAUDE_CODE`, `AIDER_CHAT`,
   `CODEX_SANDBOX`, `DEVIN_SESSION_ID`. A match produces `agent` and the
   matching tool name.
3. CI markers: `GITHUB_ACTIONS`, `GITLAB_CI`, `CIRCLECI`, `BUILDKITE`,
   `JENKINS_URL`, `CI`. A match produces `ci`.
4. `.git/matrixscroll/config.json`.
5. `human` and `git-cli`.

Agents are checked before CI so that an agent driving a commit inside a pipeline
is still recorded as an agent.

Detection deliberately outranks the config file. A file written at install time
must not be able to claim human authorship for a machine, which is the failure
this ordering exists to prevent. Detection can only move attribution away from
`human`, so a false positive costs the accuracy of a tool name and can never
manufacture a human record.

## Historical notes stay as they are

Sampling the last 200 commits of `SSX360/digital-rain` returns 145 envelopes
recording `human` and `git-cli`; the last 400 commits of `SSX360/matrixscroll`
return 29. Some of those commits were agent-authored.

They will not be corrected, for two reasons.

Envelopes are signed over their canonical bytes with the `signature` block
excluded. Editing `provenance.actor_type` in place either invalidates the
signature or, if the record is re-signed, produces a validly signed false
statement. The second outcome is worse than the inaccuracy it replaces, because
a verifier reports it as sound.

Schema v1 defines no superseding or amending record, and git notes cannot supply
one. Verification reads a note with a single `json.loads()` call over the whole
blob, so a second note attached to the same commit under `cat_sort_uniq` yields
two concatenated JSON objects and fails to parse. A correcting note would break
verification for the commit it corrects.

The correction is therefore forward-only. Envelopes written after this change
carry detected attribution. Earlier envelopes stay as written, and this page is
the record of why they are wrong.

Adding a superseding record to a future schema version is tractable. It needs a
resolution rule for verifiers, such as the newest valid signature from a trusted
key, and a policy for which keys may supersede whose records. That is a protocol
change with its own conformance vectors.

## Related

- [Commit envelope schema](../reference/commit-envelope.md)
- [Publish envelopes to git notes](../how-to/publish-git-notes.md)
