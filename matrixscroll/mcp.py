from __future__ import annotations

"""Matrix Scroll MCP server — provenance verbs only.

Install: ``pip install "matrixscroll[mcp]"``
Run: ``python -m matrixscroll.mcp``

Tools cover commit envelope production, Scroll Gate verification, notes
transport, and audit export. All verification is offline and read-only except
where noted (``create_envelope``, ``publish_notes``, ``audit_export`` write
local files or git notes).
"""

from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from . import mcp_core as core
from .cloud.client import CloudAuthError, audit_export as cloud_audit_export
from .cloud.client import list_envelopes as cloud_list_envelopes
from .cloud.client import verify_range as cloud_verify_range

SIGNUP_URL = "https://ssx360.com/signup"
DOCS_URL = "https://ssx360.com/docs"


def _require_api_key(feature: str) -> dict[str, Any] | None:
    """Return structured auth error payload when SSX360_API_KEY is unset."""
    import os

    if os.environ.get("SSX360_API_KEY", "").strip():
        return None
    return {
        "ok": False,
        "error": "api_key_required",
        "message": (
            f"{feature} requires SSX360_API_KEY. "
            "Community tier includes 100 CI verifications/day. "
            f"Get a key at {SIGNUP_URL}"
        ),
        "signup_url": SIGNUP_URL,
        "docs_url": DOCS_URL,
    }


def _cloud_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, CloudAuthError):
        return {"ok": False, **exc.payload}
    return {"ok": False, "error": "cloud_error", "message": str(exc)}

mcp = FastMCP(
    "matrixscroll-mcp",
    instructions=(
        "Matrix Scroll MCP exposes provenance verbs for AI agent governance: "
        "create and verify RFC 8032 Ed25519 commit envelopes, run Scroll Gate "
        "over PR ranges, publish git notes, export audit bundles, and (preview) "
        "connect SE050 hardware cards. Prefer ``status`` first in a new repo. "
        "Verification tools are read-only; ``create_envelope``, ``sign_action``, "
        "``publish_notes``, and ``audit_export`` write local artifacts. Hosted "
        "Scroll Gate and org-wide audit export require SSX360_API_KEY."
    ),
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "commit-envelope.v1.json"
_SPEC_PATH = _REPO_ROOT / "SPEC.md"


@mcp.resource("matrixscroll://schema/commit-envelope.v1")
def commit_envelope_schema() -> str:
    """Public JSON Schema for Matrix Scroll commit envelopes (v1)."""
    if _SCHEMA_PATH.is_file():
        return _SCHEMA_PATH.read_text(encoding="utf-8")
    return '{"error":"commit-envelope.v1.json not found in install root"}'


@mcp.resource("matrixscroll://spec")
def specification() -> str:
    """Matrix Scroll byte contract and verification rules (SPEC.md)."""
    if _SPEC_PATH.is_file():
        return _SPEC_PATH.read_text(encoding="utf-8")
    return "SPEC.md not found in install root."


@mcp.prompt()
def provenance_report(repo_path: str = ".") -> str:
    """Guide an agent to produce a provenance audit report for a Git repository."""
    return (
        f"Using Matrix Scroll MCP tools, inspect the repository at {repo_path!r}:\n"
        "1. Call ``status`` to confirm hooks and local envelope count.\n"
        "2. Call ``verify_pr_range`` with source=notes (or local if notes are missing).\n"
        "3. Call ``audit_export`` to write an evidence bundle under "
        "``.matrixscroll/audit-export``.\n"
        "4. Summarize signed vs unsigned commits, actor types, and any policy failures.\n"
        "Do not modify source code unless the user explicitly asks."
    )


@mcp.tool()
def create_envelope(
    workspace: Annotated[
        str,
        Field(
            description="Absolute or relative path to the Git repository root. "
            "Leave empty to auto-detect from the current working directory.",
        ),
    ] = "",
    commit_sha: Annotated[
        str,
        Field(
            description="Existing commit to envelope (full or short SHA). "
            "Empty uses the staged commit or HEAD depending on hook context.",
        ),
    ] = "",
    actor_type: Annotated[
        str,
        Field(
            description="Provenance actor label recorded in the envelope, e.g. agent, human, or ci.",
        ),
    ] = "",
    tool: Annotated[
        str,
        Field(
            description="Producing tool name recorded in provenance, e.g. cursor or claude-code.",
        ),
    ] = "",
    agent_scope: Annotated[
        str,
        Field(
            description="Optional path or glob limiting what an agent commit claims to touch.",
        ),
    ] = "",
    sign: Annotated[
        bool,
        Field(
            description="When true (default), Ed25519-sign the envelope with the active key store.",
        ),
    ] = True,
    save: Annotated[
        bool,
        Field(
            description="When true (default), persist the envelope under .matrixscroll/envelopes/.",
        ),
    ] = True,
) -> dict[str, Any]:
    """Create a signed Git commit envelope with Ed25519 provenance metadata.

    Records who produced a commit (human, agent, or CI), which tool signed it,
    and optional bounded agent scope. Use after staging changes and before or
    after ``git commit``. Side effects: may write ``.matrixscroll/envelopes/<sha>.json``
    when ``save`` is true. Returns ``{ok, sha, envelope, path}`` on success.
    """
    return core.create_envelope(
        workspace,
        commit_sha=commit_sha,
        actor_type=actor_type,
        tool=tool,
        agent_scope=agent_scope,
        sign=sign,
        save=save,
    )


@mcp.tool()
def verify_envelope(
    workspace: Annotated[
        str,
        Field(
            description="Git repository root. Empty auto-detects from the working directory.",
        ),
    ] = "",
    commit_sha: Annotated[
        str,
        Field(
            description="Commit SHA whose local envelope file should be verified offline.",
        ),
    ] = "",
    envelope: Annotated[
        str,
        Field(
            description="Path to a commit envelope JSON file to verify. Alias for envelope_path; "
            "use when importing bundles from CI artifacts or audit exports.",
        ),
    ] = "",
    envelope_path: Annotated[
        str,
        Field(
            description="Optional explicit path to an envelope JSON file instead of the default "
            "``.matrixscroll/envelopes/<sha>.json`` location.",
        ),
    ] = "",
    require_mode: Annotated[
        str,
        Field(
            description="Policy filter on signature mode, e.g. emulated or hardware. "
            "Empty skips mode enforcement.",
        ),
    ] = "",
    trusted_keys: Annotated[
        str,
        Field(
            description="Path to a JSON policy file listing trusted Ed25519 public keys "
            "(device_id or base64 public keys). Alias for trusted_keys_file.",
        ),
    ] = "",
    trusted_keys_file: Annotated[
        str,
        Field(
            description="Path to a JSON policy file listing trusted Ed25519 public keys.",
        ),
    ] = "",
    check_expiry: Annotated[
        bool,
        Field(
            description="When true, reject envelopes whose signed delegation or agent-scope "
            "manifest includes an expired ``expires_at`` timestamp (ISO 8601 UTC).",
        ),
    ] = False,
    require_actor_types: Annotated[
        list[str] | None,
        Field(
            description="If set, fail verification unless provenance.actor_type is in this list.",
        ),
    ] = None,
    deny_actor_types: Annotated[
        list[str] | None,
        Field(
            description="If set, fail verification when provenance.actor_type matches any denied value.",
        ),
    ] = None,
) -> dict[str, Any]:
    """Verify one signed commit envelope offline against RFC 8032 Ed25519 rules.

    Read-only: no network or hosted API required. Provide ``commit_sha`` for the
    default on-disk envelope, or ``envelope`` / ``envelope_path`` for an explicit
    JSON file from CI or audit export. Apply ``trusted_keys``, ``require_mode``,
    and actor policy lists to enforce team trust rules. Set ``check_expiry`` to
    reject stale agent delegations.

    Returns ``{ok, sha, actor_type, mode, ...}``; ``ok`` is false on signature,
    policy, expiry, or missing-envelope errors.
    """
    resolved_path = envelope_path or envelope
    keys_file = trusted_keys_file or trusted_keys
    result = core.verify_envelope(
        workspace,
        commit_sha=commit_sha,
        envelope_path=resolved_path,
        require_mode=require_mode,
        trusted_keys_file=keys_file,
        require_actor_types=require_actor_types,
        deny_actor_types=deny_actor_types,
    )
    if check_expiry and result.get("ok"):
        envelope_obj = result.get("envelope") or {}
        provenance = envelope_obj.get("provenance") or {}
        expires_at = provenance.get("expires_at")
        if expires_at:
            from datetime import datetime, timezone

            try:
                expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry < datetime.now(timezone.utc):
                    return {**result, "ok": False, "error": "envelope_expired", "expires_at": expires_at}
            except ValueError:
                pass
    return result


@mcp.tool()
def verify_pr_range(
    workspace: Annotated[
        str,
        Field(description="Git repository root. Empty auto-detects from the working directory."),
    ] = "",
    base: Annotated[
        str,
        Field(description="Range start Git ref (exclusive), typically origin/main."),
    ] = "origin/main",
    head: Annotated[
        str,
        Field(description="Range end Git ref (inclusive), e.g. HEAD or a PR head SHA."),
    ] = "HEAD",
    source: Annotated[
        Literal["hosted", "local", "notes", "bundle"],
        Field(
            description="Envelope transport: hosted Scroll Gate (default, requires SSX360_API_KEY), "
            "local files, git notes, or bundle dir for offline verification.",
        ),
    ] = "hosted",
    notes_ref: Annotated[
        str,
        Field(description="Git notes ref when source=notes, default refs/notes/matrixscroll."),
    ] = "refs/notes/matrixscroll",
    bundle_dir: Annotated[
        str,
        Field(description="Directory containing exported envelope bundles when source=bundle."),
    ] = "",
    require_mode: Annotated[
        str,
        Field(description="Optional policy require_mode filter applied to every commit in the range."),
    ] = "",
    trusted_keys_file: Annotated[
        str,
        Field(description="Optional JSON file of trusted public keys for the range check."),
    ] = "",
    require_actor_types: Annotated[
        list[str] | None,
        Field(description="Optional allow-list of provenance.actor_type values."),
    ] = None,
    deny_actor_types: Annotated[
        list[str] | None,
        Field(description="Optional deny-list of provenance.actor_type values."),
    ] = None,
) -> dict[str, Any]:
    """Scroll Gate: verify signed/unsigned commits across a PR commit range.

    Hosted mode (default): calls ssx360.com with SSX360_API_KEY.
    Set source=local|notes|bundle to verify offline without an API key.
    """
    if source in ("local", "notes", "bundle"):
        return core.verify_pr_range(
            workspace,
            base=base,
            head=head,
            source=source,
            notes_ref=notes_ref,
            bundle_dir=bundle_dir,
            require_mode=require_mode,
            trusted_keys_file=trusted_keys_file,
            require_actor_types=require_actor_types,
            deny_actor_types=deny_actor_types,
        )

    auth_err = _require_api_key("verify_pr_range (hosted Scroll Gate)")
    if auth_err:
        return auth_err
    try:
        return cloud_verify_range(base=base, head=head)
    except Exception as exc:
        return _cloud_error(exc)


@mcp.tool()
def publish_notes(
    workspace: Annotated[
        str,
        Field(description="Git repository root. Empty auto-detects from the working directory."),
    ] = "",
    base: Annotated[
        str,
        Field(description="Range start ref (exclusive) for envelopes to publish."),
    ] = "origin/main",
    head: Annotated[
        str,
        Field(description="Range end ref (inclusive) for envelopes to publish."),
    ] = "HEAD",
    notes_ref: Annotated[
        str,
        Field(description="Git notes ref to write, default refs/notes/matrixscroll."),
    ] = "refs/notes/matrixscroll",
) -> dict[str, Any]:
    """Publish local signed envelopes to git notes for CI Scroll Gate verification.

    Side effects: updates the local git notes ref; push ``refs/notes/matrixscroll`` to remote separately.
    """
    return core.publish_notes(workspace, base=base, head=head, notes_ref=notes_ref)


@mcp.tool()
def status(workspace: Annotated[
    str,
    Field(description="Git repository root. Empty auto-detects from the working directory."),
] = "") -> dict[str, Any]:
    """Report hook install state, local envelope count, and Matrix Scroll config (read-only)."""
    return core.status(workspace)


@mcp.tool()
def sign_action(
    action_type: Annotated[
        str,
        Field(
            description="Provenance action label stored in the signed manifest, e.g. agent_commit, "
            "release_manifest, delegation_grant, or ci_attestation.",
        ),
    ],
    payload: Annotated[
        dict[str, Any],
        Field(
            description="JSON object to sign. Keys are canonicalized before Ed25519 signing per SPEC.md §4. "
            "Do not include a top-level signature block.",
        ),
    ],
    key_path: Annotated[
        str,
        Field(
            description="Optional override for the Matrix Scroll identity store directory "
            "(defaults to MATRIXSCROLL_HOME or ~/.matrixscroll). Use for CI ephemeral keys.",
        ),
    ] = "",
    save_path: Annotated[
        str,
        Field(
            description="Optional file path to write the signed document. When empty, returns JSON only.",
        ),
    ] = "",
) -> dict[str, Any]:
    """Sign an arbitrary provenance manifest with the active Ed25519 identity.

    Use for release manifests, agent delegation grants, or evidence packs that
    are not Git commit envelopes. Side effects: writes ``save_path`` when set.
    Returns ``{ok, signed, device_id, mode}`` with the RFC 8032 signature block attached.
    """
    import json
    import os
    from pathlib import Path

    from .manifest import sign_manifest

    prev_home = os.environ.get("MATRIXSCROLL_HOME")
    if key_path.strip():
        os.environ["MATRIXSCROLL_HOME"] = key_path.strip()
    try:
        body = dict(payload)
        body.setdefault("action_type", action_type)
        signed = sign_manifest(body)
        if save_path.strip():
            out = Path(save_path).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(signed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {
            "ok": True,
            "signed": signed,
            "device_id": signed.get("signature", {}).get("device_id"),
            "mode": signed.get("signature", {}).get("mode"),
            "path": save_path or None,
        }
    except Exception as exc:
        return {"ok": False, "error": "sign_failed", "message": str(exc)}
    finally:
        if key_path.strip():
            if prev_home is None:
                os.environ.pop("MATRIXSCROLL_HOME", None)
            else:
                os.environ["MATRIXSCROLL_HOME"] = prev_home


@mcp.tool()
def audit_export(
    start_date: Annotated[
        str,
        Field(
            description="ISO 8601 UTC lower bound for audit records (inclusive), e.g. 2026-01-01T00:00:00Z. "
            "Hosted export filters org audit history; local export filters by commit author date when available.",
        ),
    ] = "",
    end_date: Annotated[
        str,
        Field(
            description="ISO 8601 UTC upper bound for audit records (inclusive), e.g. 2026-06-30T23:59:59Z.",
        ),
    ] = "",
    signer_id: Annotated[
        str,
        Field(
            description="Filter export to envelopes signed by this device_id (MS-XXXX-YYYY) or Ed25519 "
            "public-key fingerprint. Empty includes all signers in scope.",
        ),
    ] = "",
    format: Annotated[
        Literal["json", "guac", "evidence-pack"],
        Field(
            description="Export serialization: json (envelope bundle), guac (GUAC JSONL ingest), or "
            "evidence-pack (hosted Team+ procurement bundle with verification metadata).",
        ),
    ] = "json",
    include_verification: Annotated[
        bool,
        Field(
            description="When true (default), attach per-envelope verification results and trusted-key "
            "policy outcomes to the export for auditor replay without re-running Scroll Gate.",
        ),
    ] = True,
    workspace: Annotated[
        str,
        Field(
            description="Git repository root for local fallback export. Empty auto-detects from cwd.",
        ),
    ] = "",
    base: Annotated[
        str,
        Field(
            description="Local-only: Git ref (exclusive) when exporting from git notes or on-disk envelopes.",
        ),
    ] = "origin/main",
    head: Annotated[
        str,
        Field(
            description="Local-only: Git ref (inclusive) when exporting from git notes or on-disk envelopes.",
        ),
    ] = "HEAD",
    output_dir: Annotated[
        str,
        Field(
            description="Local-only: directory for exported files. Relative paths resolve under the repo root.",
        ),
    ] = ".matrixscroll/audit-export",
) -> dict[str, Any]:
    """Export a compliance or procurement audit bundle with optional verification proofs.

    Hosted (Team+): requires SSX360_API_KEY; calls ssx360.com/api/v1/audit/export with
    date, signer, and format filters. Local fallback: exports envelopes from the working
    tree when no API key is configured. Set ``include_verification`` for auditor-ready
    replay artifacts.
    """
    auth_err = _require_api_key("audit_export (hosted)")
    if auth_err is None:
        try:
            return cloud_audit_export(
                format=format,
                start_date=start_date,
                end_date=end_date,
                signer_id=signer_id,
                include_verification=include_verification,
            )
        except Exception as exc:
            return _cloud_error(exc)
    if auth_err.get("error") != "api_key_required":
        return auth_err
    include_guac = format == "guac"
    result = core.audit_export(
        workspace,
        base=base,
        head=head,
        output_dir=output_dir,
        include_guac=include_guac,
    )
    if include_verification:
        result["include_verification"] = True
    if signer_id:
        result["signer_filter"] = signer_id
    if start_date or end_date:
        result["date_filter"] = {"start_date": start_date or None, "end_date": end_date or None}
    return result


@mcp.tool()
def list_envelopes(
    limit: Annotated[
        int,
        Field(
            description="Maximum envelopes to return per page (1–200). Default 50. "
            "Use with offset for paginated audit review in agent workflows.",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Field(
            description="Number of newest matching envelopes to skip before returning results. "
            "Zero-based pagination index for large org histories.",
        ),
    ] = 0,
    signer_filter: Annotated[
        str,
        Field(
            description="Optional device_id (MS-XXXX-YYYY) or public-key prefix to restrict results "
            "to envelopes signed by one identity.",
        ),
    ] = "",
) -> dict[str, Any]:
    """List commit envelopes stored on ssx360.com for the authenticated organization.

    Requires SSX360_API_KEY. Returns paginated envelope metadata for Scroll Gate
    dashboards, agent memory, and compliance triage. Read-only.
    """
    auth_err = _require_api_key("list_envelopes")
    if auth_err:
        return auth_err
    try:
        return cloud_list_envelopes(limit=limit, offset=offset, signer_filter=signer_filter)
    except Exception as exc:
        return _cloud_error(exc)


@mcp.tool()
def connect_card(
    reader_name: Annotated[
        str,
        Field(
            description="Serial port or USB CDC device name for the SE050 bridge, e.g. COM3 on Windows "
            "or /dev/ttyACM0 on Linux. Empty uses MATRIXSCROLL_SE050_PORT.",
        ),
    ] = "",
    pin: Annotated[
        str,
        Field(
            description="Optional PIV or secure-element PIN when the reader requires user presence. "
            "Prefer env MATRIXSCROLL_PIV_PIN in CI; never log this value.",
        ),
    ] = "",
    timeout: Annotated[
        int,
        Field(
            description="Transport timeout in milliseconds for ping and sign operations (default 3000). "
            "Increase on slow USB hubs or VM passthrough.",
        ),
    ] = 3000,
) -> dict[str, Any]:
    """Preview: connect to an AP2 Vault Card / SE050 hardware signing bridge.

    Pings the USB CDC transport and reports availability. Hardware signing remains
    pilot-only; emulated mode is the default evaluation path. Side effects: opens
    a serial session; does not export private key material.
    """
    import os

    if reader_name.strip():
        os.environ["MATRIXSCROLL_SE050_PORT"] = reader_name.strip()
    if pin.strip():
        os.environ["MATRIXSCROLL_PIV_PIN"] = pin.strip()
    os.environ["MATRIXSCROLL_SE050_TIMEOUT_MS"] = str(max(timeout, 500))
    try:
        from .providers.hardware import HardwareProvider

        provider = HardwareProvider()
        status = provider.status_detail()
        return {
            "ok": bool(status.get("available")),
            "mode": "hardware",
            "reader_name": reader_name or os.environ.get("MATRIXSCROLL_SE050_PORT", ""),
            "timeout_ms": timeout,
            **status,
        }
    except Exception as exc:
        return {"ok": False, "mode": "hardware", "error": "connect_failed", "message": str(exc)}


def main() -> None:
    """Run the Matrix Scroll MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
