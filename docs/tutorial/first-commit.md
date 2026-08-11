# Sign and verify your first commit in 5 minutes

This tutorial signs a Git commit with an Ed25519 key and verifies the signature
offline. You then alter the signed record and watch verification fail. Everything
runs on your machine. You need no account and no hardware.

This tutorial uses emulated mode, which keeps the signing key in a file on disk.
That is the supported evaluation path and the default.

## Before you start

You need Python 3.10 or later and Git. Check both:

```bash
python --version
git --version
```

## Step 1: Install Matrix Scroll

```bash
pip install "matrixscroll==0.7.0"
```

Confirm the install:

```bash
matrixscroll status
```

You will see a JSON object. The `device_id` and `public_key` are generated on
first run and differ from the ones below.

```json
{
  "algorithm": "ed25519",
  "available": true,
  "created_at": "2026-08-11T12:09:31Z",
  "device_id": "MS-BB6E-6DB4",
  "mode": "emulated",
  "pqc": {
    "configured_algorithm": null,
    "pqc_available": "false",
    "pqc_backend": "none"
  },
  "public_key": "pio5q0TXMN1KF3fAe2EZ31kzSXWNUzHU0fr40sxdnY8=",
  "schema": "matrixscroll.identity.v1"
}
```

`"mode": "emulated"` confirms the software signer is active. `"available": true`
confirms the key store was created at `~/.matrixscroll/device.json`. The `pqc`
block reports `"none"` until you install the optional `matrixscroll[pqc]` extra,
which does not affect this tutorial.

## Step 2: Create a repository to experiment in

Work in a throwaway repository so nothing you care about is affected.

```bash
mkdir scroll-tutorial
cd scroll-tutorial
git init
```

## Step 3: Install the commit hook

```bash
matrixscroll hook-install
matrixscroll hook-status
```

`hook-status` reports that the post-commit hook is present. The hook runs after
each commit and writes a signed envelope recording who or what made it.

## Step 4: Make a signed commit

Declare the actor before committing. These two variables are what turn an
anonymous commit into an attributable one.

```bash
export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=agent-runner

echo "hello" > file.txt
git add file.txt
git commit -m "feat: add greeting"
```

On Windows PowerShell, set the variables with `$env:MATRIXSCROLL_ACTOR_TYPE =
"agent"` instead of `export`.

## Step 5: Verify the envelope

```bash
matrixscroll envelope-verify "$(git rev-parse HEAD)"
```

A valid envelope prints the signer and exits `0`:

```json
{"device_id": "MS-BB6E-6DB4", "mode": "emulated", "ok": true, "signed_at": "2026-08-11T12:09:31Z"}
```

To read the actor and tool the hook recorded, open the envelope itself. The hook
wrote it to `.git/matrixscroll/envelopes/<sha>.json`, and its `provenance` block
holds `actor_type` and `tool`.

Check the exit code yourself:

```bash
echo $?
```

It is `0`. That is the value a CI gate reads.

## Step 6: Watch verification fail

Now break the signature on purpose. Rewrite the recorded actor from `agent` to
`human`, which is exactly the lie a signature has to catch:

```bash
SHA="$(git rev-parse HEAD)"
python -c "import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text()); d['provenance']['actor_type']='human'; p.write_text(json.dumps(d))" \
  ".git/matrixscroll/envelopes/$SHA.json"
matrixscroll envelope-verify "$SHA"
echo $?
```

Verification fails and the exit code is `2`:

```json
{"ok": false, "error": "cryptographic verification failed"}
```

Verification failure always returns `2`. See
[Exit codes](../reference/exit-codes.md) for what each code means to a CI gate,
and [Commit envelope schema](../reference/commit-envelope.md) for why editing any
field outside `signature` breaks the signature.

Do not try this with `git commit --amend`. Amending fires the post-commit hook
again, so a fresh envelope gets signed for the new SHA and verification passes
with exit `0`.

## What you built

You signed a commit and verified it offline. You then altered the signed record
and made verification fail on demand. The verifier used no network and trusted
nothing about the session that produced the commit.

## Where to go next

- [Gate a protected branch in GitHub Actions](../how-to/gate-protected-branch.md)
  turns this into an enforced merge requirement.
- [Publish envelopes to git notes](../how-to/publish-git-notes.md) moves
  envelopes somewhere a reviewer can reach them.
- [Why commit-time provenance](../explanation/commit-time-vs-artifact-time.md)
  explains what this proves that Sigstore and SLSA do not.
