"""SSX360 platform CLI — thin wrappers for Scroll Gate and compliance export.

Exposed as ``ssx360`` and ``ssx360-ledger`` console scripts. Delegates to
``matrixscroll`` for local Git provenance and to ``matrixscroll.cloud`` for
hosted ssx360.com APIs when ``SSX360_API_KEY`` is set.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

COMPLIANCE_FRAMEWORKS = {
    "SOC2": {
        "id": "soc2-type-ii",
        "standard": "SOC 2 Type II",
        "trust_service_criteria": ["CC6.1", "CC7.2", "CC8.1"],
        "evidence": [
            "Signed commit provenance envelopes",
            "Scroll Gate verification results",
            "Exportable audit ledger with verification replay",
        ],
    },
    "ISO27001": {
        "id": "iso-27001",
        "standard": "ISO/IEC 27001",
        "controls": ["A.8.25", "A.8.28", "A.8.32"],
        "evidence": [
            "Change authorization via signed envelopes",
            "Protected-branch gate outcomes",
            "Structured provenance export",
        ],
    },
    "NIST-SSDF": {
        "id": "nist-ssdf",
        "standard": "NIST SSDF",
        "practices": ["PO.3", "PS.1", "PW.4"],
        "evidence": [
            "Commit provenance envelope",
            "Protected-branch enforcement result",
            "Signed JSON compliance ledger",
        ],
    },
}


def _normalize_framework(value: str) -> str:
    key = value.strip().upper().replace("_", "-").replace(" ", "-")
    aliases = {
        "SOC-2": "SOC2",
        "SOC2": "SOC2",
        "ISO-27001": "ISO27001",
        "ISO27001": "ISO27001",
        "NIST": "NIST-SSDF",
        "NIST-SSDF": "NIST-SSDF",
        "SSDF": "NIST-SSDF",
    }
    normalized = aliases.get(key, key)
    if normalized not in COMPLIANCE_FRAMEWORKS:
        known = ", ".join(sorted(COMPLIANCE_FRAMEWORKS))
        raise ValueError(f"Unknown framework {value!r}; expected one of: {known}")
    return normalized


def _resolve_pr_refs(pr_number: int) -> tuple[str, str]:
    token = os.environ.get("GITHUB_TOKEN", "").strip() or os.environ.get("GH_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not token or not repo:
        raise RuntimeError(
            "ssx360 check --pr requires GITHUB_REPOSITORY and GITHUB_TOKEN (or GH_TOKEN) "
            "to resolve pull request refs. Use --base and --head for local verification."
        )
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error for PR #{pr_number}: {raw or exc}") from exc
    base = payload.get("base", {}).get("sha")
    head = payload.get("head", {}).get("sha")
    if not base or not head:
        raise RuntimeError(f"Could not resolve base/head SHAs for PR #{pr_number}")
    return str(base), str(head)


def _collect_commits_for_hosted(
    base: str,
    head: str,
    source: str,
) -> list[dict[str, Any]]:
    from matrixscroll import gate as gate_mod

    shas = gate_mod.commits_in_range(base, head)
    commits: list[dict[str, Any]] = []
    for sha in shas:
        envelope = gate_mod._load_envelope_for_sha(  # noqa: SLF001 — shared loader
            sha,
            source=source,  # type: ignore[arg-type]
            bundle_dir=None,
        )
        item: dict[str, Any] = {"sha": sha}
        if envelope is not None:
            item["envelope"] = envelope
        commits.append(item)
    return commits


def _cmd_check(args: argparse.Namespace) -> int:
    base = args.base or ""
    head = args.head or "HEAD"
    pr_number = args.pr

    if pr_number is not None:
        pr_base, pr_head = _resolve_pr_refs(pr_number)
        base = base or pr_base
        head = head or pr_head

    use_hosted = args.hosted or bool(os.environ.get("SSX360_API_KEY", "").strip())
    if use_hosted:
        from matrixscroll.cloud import verify_range

        try:
            commits = _collect_commits_for_hosted(base or "origin/main", head, args.source)
            if not commits:
                print(json.dumps({"ok": True, "base": base, "head": head, "note": "no commits in range"}))
                return 0
            summary = verify_range(base=base or "origin/main", head=head, commits=commits)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1
        if pr_number is not None:
            summary["pr"] = pr_number
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if summary.get("ok") else 2

    from matrixscroll import gate as gate_mod

    try:
        summary = gate_mod.verify_envelope_range(
            base,
            head,
            source=args.source,
            notes_ref=args.notes_ref,
            bundle_dir=None,
            policy=None,
        )
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    if pr_number is not None:
        summary["pr"] = pr_number
    if args.summary_output:
        from pathlib import Path

        Path(args.summary_output).write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("ok") else 2


def _attach_framework(pack: dict[str, Any], framework: str) -> dict[str, Any]:
    mapping = COMPLIANCE_FRAMEWORKS[framework]
    pack["framework"] = framework
    pack["framework_mapping"] = mapping
    pack["disclaimer"] = (
        "SSX360 produces structured evidence that maps to the selected framework. "
        "This export does not constitute certification or attestation."
    )
    return pack


def _cmd_ledger_export(args: argparse.Namespace) -> int:
    framework = _normalize_framework(args.export or args.framework or "SOC2")
    output_path = args.output

    if os.environ.get("SSX360_API_KEY", "").strip():
        from matrixscroll.cloud import audit_export

        try:
            pack = audit_export(
                format="evidence-pack",
                start_date=args.start_date or "",
                end_date=args.end_date or "",
                signer_id=args.signer_id or "",
                include_verification=True,
                framework=framework,
            )
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1
        pack = _attach_framework(pack, framework)
        text = json.dumps(pack, indent=2, sort_keys=True) + "\n"
        if output_path:
            from pathlib import Path

            Path(output_path).write_text(text, encoding="utf-8")
            print(json.dumps({"ok": True, "framework": framework, "output": output_path}))
        else:
            print(text, end="")
        return 0

    from matrixscroll import gate as gate_mod
    from pathlib import Path

    out_dir = Path(output_path) if output_path else Path(".matrixscroll/audit-export")
    try:
        result = gate_mod.export_envelope_bundle(
            args.base or "origin/main",
            args.head or "HEAD",
            out_dir,
        )
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    pack = _attach_framework(
        {
            "ok": True,
            "schema": "ssx360.evidence-pack.v1",
            "source": "local",
            "bundle": result,
            "exported_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        },
        framework,
    )
    manifest = out_dir / f"evidence-pack-{framework.lower()}.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "framework": framework, "manifest": str(manifest), **result}, indent=2))
    return 0


def build_parser(prog: str = "ssx360") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="SSX360 Scroll Gate and compliance export CLI",
    )
    sub = parser.add_subparsers(dest="command")

    check = sub.add_parser("check", help="Verify signed envelopes for a PR or commit range")
    check.add_argument("--pr", type=int, help="GitHub pull request number (requires GITHUB_TOKEN)")
    check.add_argument("--base", default="", help="Base ref or SHA (exclusive)")
    check.add_argument("--head", default="HEAD", help="Head ref or SHA (inclusive)")
    check.add_argument(
        "--source",
        choices=["local", "notes", "bundle"],
        default="notes",
        help="Envelope source for local verification (default: notes)",
    )
    check.add_argument(
        "--notes-ref",
        default="refs/notes/matrixscroll",
        help="Git notes ref when --source=notes",
    )
    check.add_argument(
        "--hosted",
        action="store_true",
        help="Force hosted verification via ssx360.com/api/v1/verify",
    )
    check.add_argument("--summary-output", help="Write JSON summary to file")
    check.set_defaults(handler=_cmd_check)

    ledger = sub.add_parser("ledger", help="Export compliance evidence packs")
    ledger_sub = ledger.add_subparsers(dest="ledger_command")
    export = ledger_sub.add_parser("export", help="Export structured audit evidence")
    export.add_argument(
        "--framework",
        "--export",
        dest="export",
        default="SOC2",
        help="Compliance framework: SOC2, ISO27001, or NIST-SSDF",
    )
    export.add_argument("--output", "-o", help="Write export JSON to file")
    export.add_argument("--start-date", help="ISO 8601 start date (hosted export)")
    export.add_argument("--end-date", help="ISO 8601 end date (hosted export)")
    export.add_argument("--signer-id", help="Filter by device_id or public key prefix")
    export.add_argument("--base", default="origin/main", help="Local fallback base ref")
    export.add_argument("--head", default="HEAD", help="Local fallback head ref")
    export.set_defaults(handler=_cmd_ledger_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser("ssx360")
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


def ledger_main(argv: list[str] | None = None) -> int:
    """Entry point for ``ssx360-ledger --export SOC2`` marketing alias."""
    parser = argparse.ArgumentParser(
        prog="ssx360-ledger",
        description="Export SSX360 compliance evidence packs",
    )
    parser.add_argument(
        "--export",
        required=True,
        help="Compliance framework: SOC2, ISO27001, or NIST-SSDF",
    )
    parser.add_argument("--output", "-o", help="Write export JSON to file")
    parser.add_argument("--start-date", help="ISO 8601 start date (hosted export)")
    parser.add_argument("--end-date", help="ISO 8601 end date (hosted export)")
    parser.add_argument("--signer-id", help="Filter by device_id or public key prefix")
    parser.add_argument("--base", default="origin/main", help="Local fallback base ref")
    parser.add_argument("--head", default="HEAD", help="Local fallback head ref")
    args = parser.parse_args(argv)
    return _cmd_ledger_export(args)


if __name__ == "__main__":
    sys.exit(main())
