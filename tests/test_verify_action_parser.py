"""Contract tests for the verify action's output parser.

The action is a gate, so the failure modes matter more than the happy path. Each
test below pins one of them: a crashed verifier, a silent verifier, a verifier
that answers with JSON it cannot back up, and a verifier that legitimately says
no. All of them have to leave ``ok`` set to ``False`` and every other output
defined, because a blank output is the one value a calling workflow can mistake
for a pass.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

PARSER_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "actions"
    / "verify"
    / "parse_verify_output.py"
)

OUTPUT_KEYS = {
    "ok",
    "device_id",
    "mode",
    "verified_count",
    "agent_count",
    "human_count",
    "modes",
    "summary_path",
}

TRACEBACK = """Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.12.4/x64/bin/matrixscroll", line 8, in <module>
    sys.exit(main())
  File "/opt/.../matrixscroll/cli.py", line 849, in main
    return handler(args)
  File "/opt/.../matrixscroll/policy.py", line 26, in from_json_file
    data = json.loads(Path(path).read_text(encoding="utf-8"))
FileNotFoundError: [Errno 2] No such file or directory: '.github/nope.json'
"""


@pytest.fixture(scope="module")
def parser():
    spec = importlib.util.spec_from_file_location("ms_verify_parser", PARSER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Result:
    def __init__(self, status: int, outputs: dict[str, str], summary: str) -> None:
        self.status = status
        self.outputs = outputs
        self.summary = summary


@pytest.fixture
def run(parser, tmp_path, monkeypatch):
    def _run(
        cli_output: str,
        *,
        cli_rc: int = 0,
        mode: str = "manifest",
        require_mode: str = "",
        summary_output: str = "",
        verify_agent_scope: str = "false",
        allow_empty_range: str = "false",
        summary_preexisted: str = "false",
        config_error: str = "",
        write_output_file: bool = True,
    ) -> Result:
        output_file = tmp_path / "cli-output.txt"
        if write_output_file:
            output_file.write_text(cli_output, encoding="utf-8")
        github_output = tmp_path / "github-output.txt"
        github_output.write_text("", encoding="utf-8")
        step_summary = tmp_path / "step-summary.md"
        step_summary.write_text("", encoding="utf-8")

        monkeypatch.setenv("MS_OUTPUT_FILE", str(output_file))
        monkeypatch.setenv("MS_CLI_RC", str(cli_rc))
        monkeypatch.setenv("MS_MODE", mode)
        monkeypatch.setenv("MS_REQUIRE_MODE", require_mode)
        monkeypatch.setenv("MS_SUMMARY_OUTPUT", summary_output)
        monkeypatch.setenv("MS_VERIFY_AGENT_SCOPE", verify_agent_scope)
        monkeypatch.setenv("MS_ALLOW_EMPTY_RANGE", allow_empty_range)
        monkeypatch.setenv("MS_SUMMARY_PREEXISTED", summary_preexisted)
        monkeypatch.setenv("MS_CONFIG_ERROR", config_error)
        monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(step_summary))

        status = parser.main()

        outputs: dict[str, str] = {}
        for line in github_output.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            outputs[key] = value
        return Result(status, outputs, step_summary.read_text(encoding="utf-8"))

    return _run


def _manifest_pass() -> str:
    return json.dumps(
        {
            "ok": True,
            "device_id": "MS-D0FC-35A3",
            "mode": "emulated",
            "signed_at": "2026-08-04T00:00:00Z",
        }
    )


def _range_pass() -> str:
    return json.dumps(
        {
            "ok": True,
            "base": "abc",
            "head": "def",
            "source": "notes",
            "total": 3,
            "verified_count": 3,
            "agent_count": 2,
            "human_count": 1,
            "modes": ["emulated"],
            "results": [],
        }
    )


# --- the success paths, which must keep working exactly as before -------------


def test_manifest_success(run):
    result = run(_manifest_pass())
    assert result.status == 0
    assert result.outputs["ok"] == "True"
    assert result.outputs["device_id"] == "MS-D0FC-35A3"
    assert result.outputs["mode"] == "emulated"
    assert "passed" in result.summary


def test_range_success(run):
    result = run(_range_pass(), mode="range")
    assert result.status == 0
    assert result.outputs["ok"] == "True"
    assert result.outputs["verified_count"] == "3"
    assert result.outputs["agent_count"] == "2"
    assert result.outputs["human_count"] == "1"
    assert result.outputs["modes"] == "emulated"
    assert "**Commits verified:** 3 / 3" in result.summary


def test_success_survives_noise_on_stderr(run):
    """A warning printed next to the result is not a crash."""
    noisy = f"WARNING: pip is looking at multiple versions\n{_manifest_pass()}\n"
    result = run(noisy)
    assert result.status == 0
    assert result.outputs["ok"] == "True"
    assert result.outputs["device_id"] == "MS-D0FC-35A3"


# --- the failure paths --------------------------------------------------------


CRASH_CASES = {
    "traceback": (TRACEBACK, 1),
    "argparse usage": (
        "usage: matrixscroll [-h] ...\nmatrixscroll: error: unrecognized "
        "arguments: --verify-agent-scope\n",
        2,
    ),
    "command not found": ("bash: line 1: matrixscroll: command not found\n", 127),
    "network error": ("ERROR: Could not find a version that satisfies\n", 1),
    "empty output": ("", 1),
    "whitespace only": ("   \n\n", 0),
}


@pytest.mark.parametrize("name", sorted(CRASH_CASES))
@pytest.mark.parametrize("mode", ["manifest", "range"])
def test_non_json_output_fails_closed(run, name, mode):
    cli_output, cli_rc = CRASH_CASES[name]
    result = run(cli_output, cli_rc=cli_rc, mode=mode)
    assert result.outputs["ok"] == "False"
    assert set(result.outputs) == OUTPUT_KEYS
    assert result.status != 0
    # A crash is a broken tool, not a proven tamper, so it must not masquerade
    # as a clean verification failure when the CLI itself said nothing.
    assert result.status == (cli_rc if cli_rc else 1)


def test_every_output_is_defined_on_crash(run):
    result = run(TRACEBACK, cli_rc=1)
    assert result.outputs == {
        "ok": "False",
        "device_id": "",
        "mode": "",
        "verified_count": "0",
        "agent_count": "0",
        "human_count": "0",
        "modes": "",
        "summary_path": "",
    }


def test_crash_surfaces_the_real_error(run):
    result = run(TRACEBACK, cli_rc=1)
    assert "not JSON" in result.summary
    assert "FileNotFoundError" in result.summary
    assert ".github/nope.json" in result.summary


def test_empty_output_says_so(run):
    result = run("", cli_rc=1)
    assert "no output" in result.summary
    assert result.outputs["ok"] == "False"


def test_missing_output_file_fails_closed(run):
    result = run("", cli_rc=0, write_output_file=False)
    assert result.outputs["ok"] == "False"
    assert result.status == 1


def test_legitimate_verification_failure(run):
    payload = json.dumps({"ok": False, "error": "cryptographic verification failed"})
    result = run(payload, cli_rc=2)
    assert result.status == 2
    assert result.outputs["ok"] == "False"
    assert result.outputs["device_id"] == ""
    assert "cryptographic verification failed" in result.summary


def test_range_verification_failure_lists_the_bad_commits(run):
    payload = json.dumps(
        {
            "ok": False,
            "total": 2,
            "verified_count": 1,
            "agent_count": 1,
            "human_count": 0,
            "modes": ["emulated"],
            "results": [
                {"ok": True, "sha": "a" * 40, "mode": "emulated"},
                {"ok": False, "sha": "b" * 40, "error": "missing envelope"},
            ],
        }
    )
    result = run(payload, cli_rc=2, mode="range")
    assert result.status == 2
    assert result.outputs["ok"] == "False"
    assert result.outputs["verified_count"] == "1"
    assert "missing envelope" in result.summary
    assert "bbbbbbbb" in result.summary


def test_verification_failure_with_zero_exit_still_fails(run):
    """A CLI that says no but exits 0 must not pass the step."""
    result = run(json.dumps({"ok": False, "error": "nope"}), cli_rc=0)
    assert result.status == 2
    assert result.outputs["ok"] == "False"


def test_nonzero_exit_cannot_publish_a_passing_payload(run):
    result = run(_manifest_pass(), cli_rc=1)
    assert result.status == 1
    assert result.outputs["ok"] == "False"
    assert "exited with status 1" in result.summary


def test_ok_must_be_a_json_boolean(run):
    result = run(json.dumps({"ok": "true", "device_id": "MS-1", "mode": "emulated"}))
    assert result.outputs["ok"] == "False"
    assert result.status == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"ok": True},
        {"ok": True, "device_id": "MS-D0FC-35A3"},
        {"ok": True, "mode": "emulated"},
    ],
)
def test_manifest_success_without_its_fields_is_not_a_pass(run, payload):
    result = run(json.dumps(payload))
    assert result.outputs["ok"] == "False"
    assert result.status == 2
    assert "without these fields" in result.summary


@pytest.mark.parametrize(
    "field,value",
    [
        ("device_id", 360),
        ("device_id", True),
        ("mode", ["hardware"]),
        ("mode", {"name": "hardware"}),
    ],
)
def test_manifest_success_requires_string_identity_fields(run, field, value):
    payload = json.loads(_manifest_pass())
    payload[field] = value
    result = run(json.dumps(payload))
    assert result.outputs["ok"] == "False"
    assert result.status == 2


def test_range_success_without_counts_is_not_a_pass(run):
    result = run(json.dumps({"ok": True, "modes": ["emulated"]}), mode="range")
    assert result.outputs["ok"] == "False"
    assert result.status == 2
    assert "verified_count" in result.summary


@pytest.mark.parametrize(
    "updates",
    [
        {"total": -1, "verified_count": -1},
        {"total": 3, "verified_count": 2},
        {"total": 3, "verified_count": 3, "agent_count": 3, "human_count": 1},
        {"total": 3, "verified_count": 3, "empty_range": True},
    ],
)
def test_range_success_requires_consistent_nonnegative_counts(run, updates):
    payload = json.loads(_range_pass())
    payload.update(updates)
    result = run(json.dumps(payload), mode="range")
    assert result.outputs["ok"] == "False"
    assert result.status == 2


def test_empty_range_needs_the_explicit_opt_in(run):
    payload = {
        "ok": True,
        "total": 0,
        "verified_count": 0,
        "agent_count": 0,
        "human_count": 0,
        "modes": [],
        "empty_range": True,
        "results": [],
    }
    rejected = run(json.dumps(payload), mode="range")
    accepted = run(
        json.dumps(payload), mode="range", allow_empty_range="true"
    )
    assert rejected.outputs["ok"] == "False"
    assert accepted.outputs["ok"] == "True"


# --- policy gates -------------------------------------------------------------


def test_require_mode_is_checked_against_the_result(run):
    result = run(_manifest_pass(), require_mode="hardware")
    assert result.outputs["ok"] == "False"
    assert result.status == 2
    assert "require-mode is hardware" in result.summary


def test_require_mode_passes_when_the_mode_matches(run):
    result = run(_manifest_pass(), require_mode="emulated")
    assert result.outputs["ok"] == "True"
    assert result.status == 0


def test_require_mode_is_checked_across_a_range(run):
    payload = json.loads(_range_pass())
    payload["modes"] = ["emulated", "hardware"]
    result = run(json.dumps(payload), mode="range", require_mode="emulated")
    assert result.outputs["ok"] == "False"
    assert "hardware" in result.summary


def test_require_mode_rejects_a_range_with_no_mode(run):
    payload = json.loads(_range_pass())
    payload["modes"] = []
    result = run(json.dumps(payload), mode="range", require_mode="emulated")
    assert result.outputs["ok"] == "False"
    assert "no signature mode" in result.summary


def test_require_mode_rejects_an_allowed_empty_range(run):
    payload = {
        "ok": True,
        "total": 0,
        "verified_count": 0,
        "agent_count": 0,
        "human_count": 0,
        "modes": [],
        "empty_range": True,
        "results": [],
    }
    result = run(
        json.dumps(payload),
        mode="range",
        require_mode="hardware",
        allow_empty_range="true",
    )
    assert result.outputs["ok"] == "False"
    assert result.status == 2
    assert "no signature mode" in result.summary


# --- output hygiene -----------------------------------------------------------


def test_summary_path_only_claims_a_file_that_exists(run, tmp_path):
    missing = tmp_path / "provenance-summary.json"
    result = run(_range_pass(), mode="range", summary_output=str(missing))
    assert result.outputs["summary_path"] == ""

    missing.write_text("{}", encoding="utf-8")
    result = run(_range_pass(), mode="range", summary_output=str(missing))
    assert result.outputs["summary_path"] == str(missing)

    result = run(
        _range_pass(),
        mode="range",
        summary_output=str(missing),
        summary_preexisted="true",
    )
    assert result.outputs["summary_path"] == ""


def test_output_values_cannot_inject_extra_outputs(run):
    payload = json.dumps(
        {"ok": True, "device_id": "MS-1\nok=True", "mode": "emulated"}
    )
    result = run(payload)
    assert result.outputs["device_id"] == "MS-1 ok=True"
    assert result.outputs["ok"] == "True"
    assert len(result.outputs) == len(OUTPUT_KEYS)


# Assembled from fragments rather than written out. These are inert fixtures, but
# a literal token-shaped string in a public repository trips secret scanners and
# creates an incident somebody has to triage.
FAKE_SECRETS = [
    "gh" + "p_" + "0123456789abcdefghijklmnopqrstuvwxyz",
    "github" + "_pat_" + "11ABCDEFG0123456789_abcdefghijklmnop",
    "AKIA" + "IOSFODNN7EXAMPLE",
    "SSX360_API" + "_KEY=" + "sk-live-0123456789abcdef",
]


@pytest.mark.parametrize("secret", FAKE_SECRETS)
def test_secret_shaped_text_is_masked(run, secret):
    result = run(f"Traceback: boom while calling with {secret}\n", cli_rc=1)
    assert secret not in result.summary
    assert "redacted" in result.summary


def test_huge_output_is_truncated(run):
    noise = "\n".join(f"line {index} of verifier noise" for index in range(4000))
    result = run(noise, cli_rc=1)
    assert "earlier output trimmed" in result.summary
    assert len(result.summary) < 8000
    # The tail is what carries the exception, so it has to survive.
    assert "line 3999" in result.summary


def test_config_error_fails_closed_without_running_the_cli(run):
    result = run("", config_error="Either manifest or head-ref must be provided.")
    assert result.status == 1
    assert result.outputs["ok"] == "False"
    assert set(result.outputs) == OUTPUT_KEYS
    assert "Either manifest or head-ref" in result.summary
