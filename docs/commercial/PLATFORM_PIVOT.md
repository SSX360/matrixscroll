# SSX360 platform pivot — migration guide

Matrix Scroll remains the **open protocol and thin client** (PyPI + MCP). SSX360 is the **hosted control plane** for identity, billing, network verification, audit, and fleet cards.

## URL map

| Old | New |
|-----|-----|
| matrixscroll.com (catch-all) | ssx360.com/docs |
| matrixscroll.com/verify | ssx360.com/verify |
| matrixscroll.com/hardware | ssx360.com/hardware |
| PyPI Homepage | ssx360.com |

## Product split

**Free (local):** `create_envelope`, `verify_envelope`, `status`, emulated signing, hooks.

**Paid (network, `SSX360_API_KEY`):** hosted Scroll Gate, `list_envelopes`, platform audit export, team policy, compliance.

## Signup & API keys

1. Sign up at [ssx360.com/signup](https://ssx360.com/signup)
2. A **Community API key** is provisioned automatically on first sign-in
3. Community tier: **100 hosted verifications/day**
4. Manage keys at [ssx360.com/settings](https://ssx360.com/settings)

## CI migration (Scroll Gate v2)

See [SCROLL_GATE_V2.md](./SCROLL_GATE_V2.md). Set `SSX360_API_KEY` in GitHub Actions secrets.

## SDK 0.4.1

```bash
pip install "matrixscroll[mcp]==0.4.1"
```

New in 0.4.1: `sign-action`, `scroll commit`, expanded MCP `sign_action`. Module `matrixscroll.cloud` — HTTP client for ssx360.com APIs.

## MCP environment

```json
{
  "mcpServers": {
    "matrixscroll-mcp": {
      "command": "matrixscroll-mcp",
      "env": {
        "SSX360_API_KEY": "sk_live_..."
      }
    }
  }
}
```

## Pricing tiers

| Tier | Price | Highlights |
|------|-------|------------|
| Community | Free | Auto API key, 100 verifications/day, local signing |
| Team | $99–299/org/mo | Seats, audit export, shared history |
| Enterprise | Contact | SSO, SIEM, custom policy |

Upgrade at [ssx360.com/#pricing](https://ssx360.com/#pricing).
