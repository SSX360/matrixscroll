# Why commit-time provenance

Sigstore, SLSA, and GitHub artifact attestations answer "what was built in CI,
and from what?" Matrix Scroll answers "who or what signed this change before it
was pushed?" Those are different questions about different moments, and a supply
chain that answers only the second one has a gap where agent-authored code
enters.

## The gap

A build attestation starts its story at the build. Everything before the build,
the part where a human or an agent decided what the code should say, is outside
its frame. It can prove that artifact `X` was produced from commit `abc123` by a
particular workflow. It cannot say anything about how `abc123` came to exist.

That was a reasonable place to draw the line when commits were typed by people
whose identities were established by other means. It is a worse place to draw it
when a meaningful share of commits are produced by agents running under a shared
service account, where the commit author field records the account and not the
agent, the model, or the operator who invoked it.

Matrix Scroll signs at the moment the commit is created, on the machine that
created it, and records what the build attestation structurally cannot know.

## The two systems are complementary

They are not substitutes and adopting one does not weaken the case for the other.

| | Artifact attestation | Commit envelope |
| --- | --- | --- |
| Moment | Build | Commit |
| Location | CI runner | Developer or agent machine |
| Question | What was built, from what, by which workflow? | Who or what authored this change? |
| Verifies against | Transparency log, OIDC identity | Canonical bytes, Ed25519 public key |
| Network required | Usually | No |
| Blast radius covered | Release | Merge |

Keep GitHub Advanced Security, Semgrep, Snyk, branch protection, and artifact
attestations. Matrix Scroll adds a signed commit-time authorship claim that a
reviewer can check before merge, which is earlier than any of them act.

## Why offline verification is a design constraint

A verifier that needs a network needs a service, and a service is a party you
have to trust. The verification contract here is pure Ed25519 over canonical
manifest bytes, so a verifier needs the envelope and the public key and nothing
else. That property is what lets an auditor check evidence years later, on an
air-gapped machine, without asking whether the vendor is still operating.

It is also the reason the project holds no keys and runs no required service. An
assessment signed by a party that also controls the verification infrastructure
is worth less than one that anyone can re-check independently.

## Why not just sign commits with GPG or Sigstore's gitsign

Git already supports signed commits, and gitsign brings Sigstore identities to
them. Both prove that a key or an OIDC identity was present at commit time. That
is genuinely useful and Matrix Scroll does not replace it.

What neither carries is structured attribution. A GPG-signed commit tells you the
key. It does not tell you that the change was produced by an agent, which tool
invoked it, under what declared scope, or that the operator asserted any of that
at the time. Matrix Scroll's envelope is a typed record, so a gate can ask "how
many commits in this range were agent-authored?" and get an answer rather than a
guess.

The systems compose. A commit can be GPG-signed and carry an envelope; they
answer different questions and neither invalidates the other.

## What this does not claim

Commit-time provenance does not establish that the actor field is true. It
establishes that someone holding a specific key asserted it and that the
assertion has not been altered. See
[Trust boundaries](trust-boundaries.md) for the full boundary statement.

Compliance mappings referenced here are evidence mapping, not a certification
claim.
