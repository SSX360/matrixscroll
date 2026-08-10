# Sign and verify your first commit in 5 minutes

This tutorial signs a Git commit with an Ed25519 key, verifies the signature
offline, alters the commit, and shows verification fail. Everything runs on your
machine, with no account, network, or hardware required.

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
pip install "matrixscroll==0.6.3"
```

Confirm the install:

```bash
matrixscroll status
```

You will see a JSON object. The `device_id` is generated on first run and will
differ from the one below.

```json
{
  "available": true,
  "device_id": "MS-A3F2-9C81",
  "mode": "emulated",
  "public_key": "3b9f...",
  "schema": "matrixscroll.identity.v1"
}
```

`"mode": "emulated"` confirms the software signer is active. `"available": true`
confirms the key store was created at `~/.matrixscroll/device.json`.

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

A valid envelope prints a result object and exits `0`:

```json
{"ok": true, "actor_type": "agent", "tool": "agent-runner", "mode": "emulated"}
```

Check the exit code yourself:

```bash
echo $?
```

It is `0`. That is the value a CI gate reads.

## Step 6: Watch verification fail

The point of a signature is that it stops being valid when something changes.
Amend the commit, which rewrites it and leaves the old envelope bound to a
commit that no longer exists:

```bash
git commit --amend -m "feat: add greeting (edited)"
matrixscroll envelope-verify "$(git rev-parse HEAD)"
echo $?
```

Verification fails and the exit code is `2`. Matrix Scroll uses `2` for
verification failure, never `1`, so a gate can tell a failed proof apart from a
crashed tool.

## What you built

You signed a commit, verified it offline, then made verification fail on demand
by altering the commit. The verifier used no network and trusted nothing about
the session that produced the commit.

## Where to go next

- [Gate a protected branch in GitHub Actions](../how-to/gate-protected-branch.md)
  turns this into an enforced merge requirement.
- [Publish envelopes to git notes](../how-to/publish-git-notes.md) moves
  envelopes somewhere a reviewer can reach them.
- [Why commit-time provenance](../explanation/commit-time-vs-artifact-time.md)
  explains what this proves that Sigstore and SLSA do not.
