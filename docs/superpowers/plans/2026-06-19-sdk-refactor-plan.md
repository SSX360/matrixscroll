# SDK Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the monolithic `_core.py` into focused modules while preserving the public API in `matrixscroll/__init__.py`.

**Architecture:** Move crypto, canonical encoding, manifest signing, providers, and policy into separate modules. Keep `_core.py` as a thin compatibility shim that re-exports everything until v0.3.0.

**Tech Stack:** Python 3.10+, cryptography, pytest

---

## Target module layout

```
matrixscroll/
  __init__.py          # unchanged public API
  _core.py             # compatibility re-exports (deprecated v0.3.0)
  canonical.py         # deterministic JSON encoding
  manifest.py          # sign_manifest / verify_manifest
  policy.py            # policy-aware verification
  errors.py            # IdentityError, VerificationError
  git.py               # git hooks (v0.2.0)
  providers/
    __init__.py
    base.py            # IdentityProvider ABC
    emulated.py        # EmulatedProvider
    hardware.py        # HardwareProvider stub
    yubikey.py         # YubiKey bridge (optional extra)
  cli.py
  py.typed
```

## Public API contract (must not break)

These symbols remain importable from `matrixscroll`:

- Constants: `SCHEMA`, `SIGNATURE_SCHEMA`, `ALGORITHM`, `DEVICE_FILE`
- Exceptions: `IdentityError`
- Providers: `IdentityProvider`, `EmulatedProvider`, `HardwareProvider`
- Functions: `store_dir`, `device_id`, `get_provider`, `identity_info`, `status`, `public_key_b64`, `sign`, `verify`, `sign_manifest`, `verify_manifest`

## Task 1: Extract errors and constants

**Files:**
- Create: `matrixscroll/errors.py`
- Create: `matrixscroll/constants.py`
- Modify: `matrixscroll/_core.py`

Move `IdentityError`, `SCHEMA`, `SIGNATURE_SCHEMA`, `ALGORITHM`, `DEVICE_FILE`, `SEED_LEN`, mode constants.

## Task 2: Extract canonical encoding

**Files:**
- Create: `matrixscroll/canonical.py`
- Modify: `matrixscroll/manifest.py`

Move `_canonical()` → `canonical_bytes(payload: dict) -> bytes`.

## Task 3: Extract manifest signing

**Files:**
- Create: `matrixscroll/manifest.py`

Move `sign_manifest`, `verify_manifest`, keep importing `sign`/`verify` from providers layer.

## Task 4: Extract providers

**Files:**
- Create: `matrixscroll/providers/base.py`
- Create: `matrixscroll/providers/emulated.py`
- Create: `matrixscroll/providers/hardware.py`
- Create: `matrixscroll/providers/__init__.py`

Move provider classes and `get_provider()`.

## Task 5: Add policy module

**Files:**
- Create: `matrixscroll/policy.py`
- Modify: `matrixscroll/cli.py`

Add:

```python
@dataclass
class VerifyPolicy:
    require_mode: str | None = None
    trusted_public_keys: set[str] | None = None
    allowed_schemas: set[str] | None = None

def verify_manifest_with_policy(manifest: dict, policy: VerifyPolicy) -> tuple[bool, str | None]:
    ...
```

CLI flags (v0.2.1):

```
matrixscroll verify manifest.json --require-mode hardware --trusted-keys keys.json
```

## Task 6: Compatibility shim

**Files:**
- Modify: `matrixscroll/_core.py`

Replace body with re-exports:

```python
from .canonical import canonical_bytes as _canonical
from .manifest import sign_manifest, verify_manifest
from .providers import EmulatedProvider, HardwareProvider, IdentityProvider, get_provider
...
```

Add deprecation comment; remove shim in v0.3.0.

## Task 7: Update tests

**Files:**
- Modify: `tests/test_core.py` — add imports from new modules
- Create: `tests/test_policy.py`
- Create: `tests/test_canonical.py`

Run: `pytest -ra`

## Task 8: Update packaging

**Files:**
- Modify: `pyproject.toml` — include `schemas/`, optional `[yubikey]` extra

```toml
[project.optional-dependencies]
yubikey = []  # PKCS#11 deps added when bridge ships
git = []
```

## Migration guide (for downstream consumers)

| Before | After (preferred) |
|--------|-------------------|
| `from matrixscroll._core import _canonical` | `from matrixscroll.canonical import canonical_bytes` |
| `verify_manifest(m)` | `verify_manifest_with_policy(m, policy)` for CI gates |
| `MATRIXSCROLL_MODE=hardware` | unchanged |

## Version bump

- v0.2.0: git module, schemas, provider split (shim retained)
- v0.2.1: policy CLI flags
- v0.3.0: remove `_core.py` shim, add YubiKey extra

## Risks

| Risk | Mitigation |
|------|------------|
| Import cycles | providers → manifest → canonical (one direction) |
| Vector drift | run `tests/test_vectors.py` after every task |
| Breaking private imports | document `_core` deprecation; grep GitHub for `_core` usage |

## Verification checklist

- [ ] `pytest` green
- [ ] `matrixscroll status` unchanged output shape
- [ ] All vectors pass
- [ ] `pip install -e .` works
- [ ] No new runtime deps without CONTRIBUTING discussion
