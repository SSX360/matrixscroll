# Matrix Scroll security lockdown — operator runbook

Manual steps for maintainers. Rotate credentials; do not rely on deleting copies from
mirrors, caches, or backups.

## Tier 1 — credential rotation (do first)

| Credential | Action |
|------------|--------|
| `PARALLEL_API_KEY` | Revoke at Parallel dashboard; issue new key |
| `MESHY_API_KEY` | Revoke at Meshy; issue new key |
| `HF_TOKEN` / `HUGGINGFACE_HUB_TOKEN` | Hugging Face → Access Tokens → revoke old, create new |
| `TREX_ADMIN_PASS` / `TREX_NICK_PASS` | Rotate Trex admin passwords |
| `VERCEL_OIDC_TOKEN` | Vercel → regenerate OIDC token |
| `VERCEL_TOKEN` | GitHub `SSX360/Matrix_Scroll` secret → new token at vercel.com/account/tokens |

Local workbench (never commit):

```powershell
# Regenerate session.secret (example: 64 hex bytes)
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToHexString($bytes).ToLower() | Set-Content -NoNewline session.secret

# Invalidate one-time credentials file
Remove-Item credentials.once.txt -ErrorAction SilentlyContinue
```

Update every `.env`, Vercel project env, and CI secret that consumed the old values.

## Tier 2 — OneDrive

The workspace lives under `OneDrive\Desktop\`. Deleting a file locally does not purge
version history.

1. OneDrive web → browse to affected folders
2. For `session.secret`, `credentials.once.txt`, `.env.local`: **Version history** → delete all versions
3. Empty **Recycle bin** (local and OneDrive web)

## Tier 3 — backup archives

Locate every copy of archives listed in `BACKUP-MANIFEST.txt` (includes `.env`,
`credentials.once.txt`, `session.secret`, sqlite DB). Destroy or re-encrypt and record
where copies lived.

## Tier 4 — third-party surfaces

After Tier 1 rotation: Vercel env on `matrixscroll-site`, CI logs, and build caches are
covered. No additional deletion required.

## Tier 5 — operational data

`data/envelopes/` and `workbench.sqlite3` are audit evidence, not credentials. Retain
unless a separate retention policy says otherwise. Document the decision in
[`OFFLINE-SHUTDOWN.md`](./OFFLINE-SHUTDOWN.md).

## DNS and mail (matrixscroll.com)

**Never let the domain lapse.** Squatters can host fake verifier pages under your brand.

1. Registrar: enable **lock** and **auto-renew**
2. DNS TXT: `v=spf1 -all`
3. DNS TXT `_dmarc`: `v=DMARC1; p=reject; adkim=s; aspf=s`
4. Remove or null **MX** records (no inbound mail on this domain unless explicitly maintained elsewhere)
5. Tombstone lists GitHub Security Advisories as primary report path if `security@` is retired

## PyPI supply chain

1. Enable **2FA** on every PyPI maintainer account (account settings)
2. Confirm **Trusted Publishing**: repo `SSX360/matrixscroll`, workflow `publish.yml`, environment `pypi` (OIDC; no long-lived `PYPI_TOKEN` in GitHub)
3. Register defensive placeholder packages (same org): `matrix-scroll`, `matrixscroll-sdk`, `matrixscrolls`, `mtrxscroll`, `ssx360-scroll`
4. Revoke stale personal PyPI API tokens in GitHub org secrets

## Signing key rotation

| Surface | Action |
|---------|--------|
| Emulated `~/.matrixscroll/device.json` | `matrixscroll status` on clean host; new key; update deployment `trusted-keys.json` |
| SE050 / USB fleet | Re-provision per [`hardware-provider.md`](./hardware-provider.md) |
| Production signing | Move to hardware token or HSM; laptops must not hold production private keys |

Record rotation date in team notes. See [`SECURITY.md`](../SECURITY.md) for custody policy.
