"""End-to-end tests for the verify action's shell step.

The parser is covered by ``test_verify_action_parser.py``. What this file covers
is the plumbing around it: the step must reach its output writes even when the
CLI is missing, when the CLI crashes, and when the parser itself cannot run. The
body under test is read out of ``action.yml``, so a change to the committed step
that reintroduces an early abort fails here.

A stub ``matrixscroll`` on ``PATH`` stands in for the real CLI, which keeps these
tests offline and lets each case pick its own output and exit status.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_DIR = REPO_ROOT / ".github" / "actions" / "verify"
ACTION_YML = ACTION_DIR / "action.yml"

BASH = os.environ.get("MATRIXSCROLL_TEST_BASH") or shutil.which("bash")

pytestmark = pytest.mark.skipif(
    not BASH
    or (sys.platform == "win32" and not os.environ.get("MATRIXSCROLL_TEST_BASH")),
    reason=(
        "the composite step body needs a POSIX shell; set MATRIXSCROLL_TEST_BASH "
        "to run it on Windows"
    ),
)

TRACEBACK = (
    "Traceback (most recent call last):\n"
    '  File "/opt/hostedtoolcache/bin/matrixscroll", line 8, in <module>\n'
    "    sys.exit(main())\n"
    '  File "/opt/matrixscroll/policy.py", line 26, in from_json_file\n'
    '    data = json.loads(Path(path).read_text(encoding="utf-8"))\n'
    "FileNotFoundError: [Errno 2] No such file or directory: "
    "'.github/nope.json'\n"
)


def verify_step_body() -> str:
    """Read the ``run:`` block of the step with ``id: verify`` out of action.yml.

    Deliberately dependency-free. Pulling in a YAML parser for one block would
    add a test dependency the SDK does not otherwise need.
    """
    lines = ACTION_YML.read_text(encoding="utf-8").splitlines()
    start = next(
        index for index, line in enumerate(lines) if line.strip() == "id: verify"
    )
    run_at = next(
        index
        for index in range(start, len(lines))
        if lines[index].rstrip() == "      run: |"
    )
    body: list[str] = []
    for line in lines[run_at + 1 :]:
        if line.strip() and not line.startswith("        "):
            break
        body.append(line[8:] if line.startswith("        ") else line)
    text = "\n".join(body)
    assert "emit_fallback_outputs" in text, "extracted the wrong block from action.yml"
    return text


@pytest.fixture
def step(tmp_path):
    """Run the committed step body with a stub CLI and return what it produced."""

    def _step(
        *,
        cli_output: str = "",
        cli_rc: int = 0,
        cli_installed: bool = True,
        manifest: str = "release.signed.json",
        head_ref: str = "",
        require_mode: str = "",
        summary_output: str = "",
        allow_empty_range: str = "false",
        verify_agent_scope: str = "false",
        action_path: Path | None = None,
    ):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        payload = tmp_path / "stub-output.txt"
        payload.write_text(cli_output, encoding="utf-8")
        if cli_installed:
            stub = bin_dir / "matrixscroll"
            stub.write_text(
                "#!/usr/bin/env bash\n"
                'echo "stub args: $*" >&2\n'
                f'cat "{payload.as_posix()}"\n'
                f"exit {cli_rc}\n",
                encoding="utf-8",
            )
            stub.chmod(0o755)

        github_output = tmp_path / "github-output.txt"
        github_output.write_text("", encoding="utf-8")
        step_summary = tmp_path / "step-summary.md"
        step_summary.write_text("", encoding="utf-8")

        env = dict(os.environ)
        env.update(
            {
                "PATH": os.pathsep.join([str(bin_dir), env.get("PATH", "")]),
                "GITHUB_OUTPUT": github_output.as_posix(),
                "GITHUB_STEP_SUMMARY": step_summary.as_posix(),
                "GITHUB_ACTION_PATH": (action_path or ACTION_DIR).as_posix(),
                "MS_MANIFEST": manifest,
                "MS_HEAD_REF": head_ref,
                "MS_BASE_REF": "",
                "MS_SOURCE": "notes",
                "MS_BUNDLE_DIR": "",
                "MS_NOTES_REF": "refs/notes/matrixscroll",
                "MS_REQUIRE_MODE": require_mode,
                "MS_TRUSTED_KEYS": "",
                "MS_SUMMARY_OUTPUT": summary_output,
                "MS_ALLOW_EMPTY_RANGE": allow_empty_range,
                "MS_VERIFY_AGENT_SCOPE": verify_agent_scope,
            }
        )
        env.pop("MS_CONFIG_ERROR", None)
        env.pop("MS_MODE", None)

        script = tmp_path / "step.sh"
        script.write_text(verify_step_body(), encoding="utf-8")
        completed = subprocess.run(
            # The exact invocation the runner uses for `shell: bash`. The flags
            # matter: errexit is on before the step body starts, and an earlier
            # version of this fix looked correct under a plain `bash script.sh`
            # while still aborting before its output writes on the runner.
            [str(BASH), "--noprofile", "--norc", "-e", "-o", "pipefail", str(script)],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        outputs: dict[str, str] = {}
        for line in github_output.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            outputs[key] = value
        return (
            completed,
            outputs,
            step_summary.read_text(encoding="utf-8"),
        )

    return _step


MANIFEST_PASS = (
    '{"device_id": "MS-D0FC-35A3", "mode": "emulated", "ok": true, '
    '"signed_at": "2026-06-20T02:01:16Z"}'
)
RANGE_PASS = (
    '{"ok": true, "total": 2, "verified_count": 2, "agent_count": 1, '
    '"human_count": 1, "modes": ["emulated"], "results": []}'
)


def test_success(step):
    completed, outputs, summary = step(cli_output=MANIFEST_PASS)
    assert completed.returncode == 0
    assert outputs["ok"] == "True"
    assert outputs["device_id"] == "MS-D0FC-35A3"
    assert outputs["mode"] == "emulated"
    assert "passed" in summary
    # The step still echoes the verifier's output into the log.
    assert "MS-D0FC-35A3" in completed.stdout


def test_range_success(step):
    completed, outputs, _summary = step(
        cli_output=RANGE_PASS, head_ref="deadbeef", manifest=""
    )
    assert completed.returncode == 0
    assert outputs["ok"] == "True"
    assert outputs["verified_count"] == "2"
    assert outputs["modes"] == "emulated"
    assert "--allow-empty-range" not in completed.stdout


def test_allowed_empty_range_passes_the_explicit_cli_flag(step):
    payload = (
        '{"ok": true, "total": 0, "verified_count": 0, "agent_count": 0, '
        '"human_count": 0, "modes": [], "empty_range": true, "results": []}'
    )
    completed, outputs, _summary = step(
        cli_output=payload,
        head_ref="deadbeef",
        manifest="",
        allow_empty_range="true",
    )
    assert completed.returncode == 0
    assert outputs["ok"] == "True"
    assert "--allow-empty-range" in completed.stdout


def test_legitimate_verification_failure(step):
    completed, outputs, summary = step(
        cli_output='{"ok": false, "error": "cryptographic verification failed"}',
        cli_rc=2,
    )
    assert completed.returncode == 2
    assert outputs["ok"] == "False"
    assert "cryptographic verification failed" in summary


def test_crash_with_non_json_output(step):
    """The defect this action file exists to close."""
    completed, outputs, summary = step(cli_output=TRACEBACK, cli_rc=1)
    assert completed.returncode == 1
    assert outputs["ok"] == "False"
    assert outputs == {
        "ok": "False",
        "device_id": "",
        "mode": "",
        "verified_count": "0",
        "agent_count": "0",
        "human_count": "0",
        "modes": "",
        "summary_path": "",
    }
    assert "FileNotFoundError" in summary
    assert "not JSON" in summary


def test_crash_in_range_mode(step):
    completed, outputs, summary = step(
        cli_output=TRACEBACK, cli_rc=1, head_ref="deadbeef", manifest=""
    )
    assert completed.returncode == 1
    assert outputs["ok"] == "False"
    assert outputs["verified_count"] == "0"
    assert outputs["modes"] == ""
    assert "FileNotFoundError" in summary


def test_cli_not_installed(step):
    """A refused SDK install used to leave every output blank."""
    completed, outputs, _summary = step(cli_installed=False)
    assert completed.returncode != 0
    assert outputs["ok"] == "False"


def test_parser_unavailable_still_writes_outputs(step, tmp_path):
    """The shell fallback covers a parser that cannot run at all."""
    empty = tmp_path / "no-action-here"
    empty.mkdir()
    completed, outputs, _summary = step(
        cli_output=MANIFEST_PASS, action_path=empty
    )
    assert completed.returncode != 0
    assert outputs["ok"] == "False"
    assert len(outputs) == 8


def test_no_manifest_and_no_head_ref(step):
    completed, outputs, summary = step(manifest="", head_ref="")
    assert completed.returncode == 1
    assert outputs["ok"] == "False"
    assert "Either manifest or head-ref" in summary


def test_require_mode_mismatch_fails(step):
    completed, outputs, summary = step(
        cli_output=MANIFEST_PASS, require_mode="hardware"
    )
    assert completed.returncode == 2
    assert outputs["ok"] == "False"
    assert "require-mode is hardware" in summary


def test_inputs_are_not_interpolated_into_the_shell(step, tmp_path):
    """A manifest path is an argument, never shell source."""
    completed, outputs, _summary = step(
        cli_output=MANIFEST_PASS,
        manifest='$(touch pwned.txt)"; touch pwned2.txt; "',
    )
    assert not (tmp_path / "pwned.txt").exists()
    assert not (tmp_path / "pwned2.txt").exists()
    assert outputs["ok"] == "True"
