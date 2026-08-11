# Exit codes

Every Matrix Scroll command uses the same three codes. The separation between
`1` and `2` is deliberate: a gate must be able to tell a failed proof apart from
a broken tool, because they call for different responses.

| Code | Meaning | What a CI gate should do |
| --- | --- | --- |
| `0` | Verification succeeded, or the command completed | Continue |
| `1` | The tool could not run. An unresolvable ref, a missing module, a failed hook install, or `--source bundle` with no `--bundle` directory | Fail the build and page the owner |
| `2` | Verification failed, or an input file could not be read | Fail the build and block the merge |

An unreadable input file returns `2`, not `1`. This applies to
`matrixscroll verify`, `matrixscroll envelope-verify` and
`matrixscroll mcp verify`.

## What produces exit code 2

`matrixscroll verify` and `matrixscroll envelope-verify` exit `2` on any of:

- a tampered manifest, where the canonical bytes no longer match the signature
- a missing `signature` block
- a wrong `schema` or a `signature.algorithm` other than `ed25519`
- a device ID that does not match the signing key
- a malformed or undecodable public key
- an unreadable envelope file

`matrixscroll mcp verify` exits `2` on tool-surface drift against a baseline.

`matrixscroll envelope-verify-range` and `ssx360 check` exit `2` when the range
holds no commits, because a gate that verified nothing has proved nothing. The
JSON carries `"empty_range": true` so a caller can separate that from a signature
failure. Pass `--allow-empty-range` where an empty range is expected, such as a
re-run of a commit that already merged.

## Every failure is JSON

Any exception that escapes a subcommand is caught at the top of
`matrixscroll.cli.main`, printed as `{"ok": false, "error": "..."}` on stdout,
and exits `1`. A CI step that parses the output never has to read a Python
traceback and guess. An argparse usage error still exits `2` from argparse
itself, and `--help` still exits `0`.

## Never treat 1 and 2 the same

A script that does `if ! matrixscroll envelope-verify "$SHA"; then` cannot tell a
tampered envelope from a typo in the path. Branch on the code:

```bash
matrixscroll envelope-verify "$SHA"
case $? in
  0) echo "verified" ;;
  2) echo "PROVENANCE FAILURE: do not merge"; exit 1 ;;
  *) echo "tool error: investigate the runner"; exit 1 ;;
esac
```
