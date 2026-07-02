#!/usr/bin/env python3
"""Clean-machine onboarding smoke for the pinned PyPI release."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "cmd": cmd,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                },
                indent=2,
            )
        )
    return proc


def append_step_summary(body: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    target = Path(summary_path)
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    target.write_text(existing + body, encoding="utf-8")


def write_payload(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    summary_file = Path(os.environ.get("ONBOARDING_SUMMARY_PATH", "onboarding-smoke-summary.json"))
    started = time.time()
    root = Path(tempfile.mkdtemp(prefix="matrixscroll-onboarding-"))
    repo = root / "repo"
    home = root / "matrixscroll-home"
    repo.mkdir()
    home.mkdir()

    env = os.environ.copy()
    env["MATRIXSCROLL_HOME"] = str(home)
    env["MATRIXSCROLL_ACTOR_TYPE"] = "agent"
    env["MATRIXSCROLL_TOOL"] = "agent-runner"

    matrixscroll_cmd = [sys.executable, "-m", "matrixscroll.cli"]

    payload: dict[str, object] = {
        "ok": False,
        "platform": platform.system().lower(),
        "python": platform.python_version(),
        "install": "matrixscroll==0.5.0",
        "workspace": str(repo),
    }

    try:
        run(["git", "init", "-q"], cwd=repo)
        run(["git", "config", "user.email", "proof@matrixscroll.com"], cwd=repo)
        run(["git", "config", "user.name", "Matrix Scroll Proof"], cwd=repo)

        run(matrixscroll_cmd + ["hook-install"], cwd=repo, env=env)
        hook_status = json.loads(run(matrixscroll_cmd + ["hook-status"], cwd=repo, env=env).stdout)

        (repo / "hello.txt").write_text("clean-machine proof\n", encoding="utf-8")
        run(["git", "add", "hello.txt"], cwd=repo, env=env)
        commit_proc = run(["git", "commit", "-m", "feat: onboarding smoke"], cwd=repo, env=env)

        sha = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
        verify = json.loads(run(matrixscroll_cmd + ["envelope-verify", sha], cwd=repo, env=env).stdout)

        payload.update(
            {
                "ok": True,
                "hook_status": hook_status,
                "commit": {
                    "sha": sha,
                    "stdout": commit_proc.stdout.strip(),
                    "stderr": commit_proc.stderr.strip(),
                },
                "verify": verify,
                "time_to_first_verified_commit_seconds": round(time.time() - started, 1),
            }
        )
        write_payload(summary_file, payload)
        append_step_summary(
            "\n".join(
                [
                    f"## Onboarding smoke ({payload['platform']})",
                    "",
                    f"- Install: `{payload['install']}`",
                    f"- Time to first verified commit: `{payload['time_to_first_verified_commit_seconds']}s`",
                    f"- Commit: `{sha}`",
                    f"- Verify mode: `{verify.get('mode', 'unknown')}`",
                    f"- Device ID: `{verify.get('device_id', 'unknown')}`",
                    "",
                ]
            )
            + "\n"
        )
        print(json.dumps(payload, indent=2))
        return 0
    except Exception as exc:  # pragma: no cover
        payload["error"] = str(exc)
        payload["time_to_first_verified_commit_seconds"] = round(time.time() - started, 1)
        write_payload(summary_file, payload)
        append_step_summary(
            "\n".join(
                [
                    f"## Onboarding smoke ({payload['platform']})",
                    "",
                    "- Status: `FAILED`",
                    f"- Error: `{exc}`",
                    "",
                ]
            )
            + "\n"
        )
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
