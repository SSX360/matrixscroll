#!/usr/bin/env python3
"""Turn matrixscroll CLI output into GitHub Action outputs, failing closed.

The verify action used to parse CLI output with inline ``json.loads`` calls in
shell steps running under ``set -euo pipefail``. Output that is not JSON kills
the step before a single output is written: a Python traceback, an argparse
usage message, a missing dependency, a network error. A caller that gates on
``ok`` then reads an empty string rather than a false, and an empty string is
easy to write a condition that treats as success.

This script writes all eight outputs on every path, including the paths where
the verifier never produced a usable result.

Contract held by the tests in ``tests/test_verify_action_parser.py``:

* ``ok`` is spelled ``True`` or ``False``, matching what the previous
  ``print(json.loads(...).get("ok", False))`` emitted.
* Every other output gets a defined value. A caller never reads a blank it has
  to guess about.
* Exit status 0 only for an affirmative verified result. 2 for a verification
  failure or a policy violation, 1 for a verifier that broke, and the CLI's own
  status whenever that status is non-zero.

Inputs arrive as environment variables so that no action input is ever
interpolated into a shell command:

``MS_MODE``                ``range`` or ``manifest``
``MS_OUTPUT_FILE``         file holding the captured CLI output
``MS_CLI_RC``              exit status the CLI returned
``MS_REQUIRE_MODE``        value of the ``require-mode`` action input
``MS_SUMMARY_OUTPUT``      value of the ``summary-output`` action input
``MS_VERIFY_AGENT_SCOPE``  value of the ``verify-agent-scope`` action input
``MS_CONFIG_ERROR``        set when the action rejected its own inputs
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

TRUE = "True"
FALSE = "False"

DEFAULT_OUTPUTS: dict[str, str] = {
    "ok": FALSE,
    "device_id": "",
    "mode": "",
    "verified_count": "0",
    "agent_count": "0",
    "human_count": "0",
    "modes": "",
    "summary_path": "",
}

EXIT_OK = 0
EXIT_TOOL_FAILURE = 1
EXIT_VERIFICATION_FAILURE = 2

MAX_DIAGNOSTIC_LINES = 60
MAX_DIAGNOSTIC_CHARS = 4000

# Anything secret-shaped is masked before the captured output reaches the log or
# the step summary. The verifier has no reason to print a credential, but it
# echoes whatever the runner handed it, and a traceback can carry an argument
# list.
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "[redacted private key]",
    ),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "[redacted github token]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"), "[redacted github token]"),
    (re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{12,}"), "[redacted aws key id]"),
    (re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"), "[redacted slack token]"),
    (
        re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"),
        "[redacted json web token]",
    ),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{10,}"), "[redacted authorization]"),
    (
        # No leading word boundary: the name is usually prefixed, as in
        # SSX360_API_KEY or GITHUB_TOKEN.
        re.compile(
            r"(?i)(?:api[_-]?key|secret|password|passwd|token|authorization)\b"
            r"\s*[:=]\s*[\"']?[^\s\"',}]{6,}"
        ),
        "[redacted credential]",
    ),
]


def redact(text: str) -> str:
    """Mask secret-shaped substrings in *text*."""
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def truncate(text: str) -> str:
    """Cut *text* down to something a step summary can carry."""
    lines = text.splitlines()
    dropped_lines = 0
    if len(lines) > MAX_DIAGNOSTIC_LINES:
        dropped_lines = len(lines) - MAX_DIAGNOSTIC_LINES
        # Keep the tail. A traceback puts the exception on the last line.
        lines = lines[-MAX_DIAGNOSTIC_LINES:]
    result = "\n".join(lines)
    if len(result) > MAX_DIAGNOSTIC_CHARS:
        result = result[-MAX_DIAGNOSTIC_CHARS:]
        dropped_lines += 1
    if dropped_lines:
        result = f"[earlier output trimmed]\n{result}"
    return result


def diagnostic(text: str) -> str:
    """Prepare captured CLI output for a human to read."""
    return truncate(redact(text)).strip()


def extract_json(text: str) -> tuple[dict[str, Any] | None, bool]:
    """Pull the CLI's JSON result out of *text*.

    Returns the parsed object and whether the whole of *text* was that object.
    The action captures the CLI with ``2>&1``, so a warning on stderr lands in
    the same buffer as the result. Scanning for the object keeps a genuine pass
    from reading as a crash, while returning ``None`` for output that carries no
    JSON at all.
    """
    stripped = text.strip()
    if not stripped:
        return None, False
    try:
        whole = json.loads(stripped)
    except ValueError:
        pass
    else:
        if isinstance(whole, dict):
            return whole, True
        return None, False

    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _end = decoder.raw_decode(text, index)
        except ValueError:
            continue
        if isinstance(value, dict):
            candidates.append(value)
    if not candidates:
        return None, False
    for value in reversed(candidates):
        if "ok" in value:
            return value, False
    return candidates[-1], False


def sanitize(value: Any) -> str:
    """Render *value* as a single safe ``$GITHUB_OUTPUT`` line."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return TRUE if value else FALSE
    return re.sub(r"[\r\n]+", " ", str(value)).strip()


def as_count(value: Any) -> str:
    """Render a count, refusing anything that is not an integer."""
    if isinstance(value, bool) or not isinstance(value, int):
        return "0"
    return str(value)


class Reporter:
    """Collects log lines, annotations and step-summary markdown."""

    def __init__(self, log: Any = None) -> None:
        self.log = log if log is not None else sys.stdout
        self.summary_lines: list[str] = []

    def note(self, message: str) -> None:
        print(message, file=self.log)

    def error(self, message: str) -> None:
        print(f"::error title=Matrix Scroll verify::{message}", file=self.log)

    def summary(self, *lines: str) -> None:
        self.summary_lines.extend(lines)

    def flush_summary(self) -> None:
        path = os.environ.get("GITHUB_STEP_SUMMARY")
        if not path or not self.summary_lines:
            return
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\n".join(self.summary_lines).rstrip() + "\n")


def write_outputs(outputs: dict[str, str]) -> None:
    """Append every output, in a fixed order, to ``$GITHUB_OUTPUT``."""
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        for key in DEFAULT_OUTPUTS:
            print(f"{key}={outputs[key]}")
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key in DEFAULT_OUTPUTS:
            handle.write(f"{key}={outputs[key]}\n")


def read_cli_output() -> str:
    path = os.environ.get("MS_OUTPUT_FILE") or ""
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def cli_status() -> int:
    raw = (os.environ.get("MS_CLI_RC") or "").strip()
    try:
        return int(raw)
    except ValueError:
        return EXIT_TOOL_FAILURE


def _failure_rows(payload: dict[str, Any]) -> list[str]:
    rows = payload.get("results")
    if not isinstance(rows, list):
        return []
    failures = []
    for row in rows:
        if not isinstance(row, dict) or row.get("ok"):
            continue
        sha = sanitize(row.get("sha") or "")[:8]
        reason = redact(sanitize(row.get("error") or "unknown"))
        failures.append(f"- `{sha}`: {reason}")
    return failures[:20]


def main() -> int:
    reporter = Reporter()
    outputs = dict(DEFAULT_OUTPUTS)
    kind = (os.environ.get("MS_MODE") or "manifest").strip()
    require_mode = (os.environ.get("MS_REQUIRE_MODE") or "").strip()
    summary_output = (os.environ.get("MS_SUMMARY_OUTPUT") or "").strip()
    verify_agent_scope = (
        os.environ.get("MS_VERIFY_AGENT_SCOPE") or ""
    ).strip().lower() == "true"
    config_error = (os.environ.get("MS_CONFIG_ERROR") or "").strip()
    heading = (
        "## Matrix Scroll provenance gate"
        if kind == "range"
        else "## Matrix Scroll manifest verification"
    )

    if config_error:
        reporter.error(config_error)
        reporter.summary(heading, "", "**Status:** failed to start", "", config_error)
        write_outputs(outputs)
        reporter.flush_summary()
        return EXIT_TOOL_FAILURE

    raw = read_cli_output()
    status = cli_status()
    payload, whole_output_was_json = extract_json(raw)

    if payload is None:
        reason = (
            "the matrixscroll CLI produced no output"
            if not raw.strip()
            else "the matrixscroll CLI produced output that is not JSON"
        )
        detail = diagnostic(raw)
        reporter.error(
            f"{reason}. Treating the verification as failed. Exit status {status}."
        )
        if detail:
            reporter.note("Captured verifier output:")
            reporter.note(detail)
        reporter.summary(
            heading,
            "",
            "**Status:** failed. The verifier did not return a result.",
            f"**Reason:** {reason} (exit status {status}).",
            "",
            "### Verifier output",
            "",
            "```",
            detail or "(no output captured)",
            "```",
        )
        write_outputs(outputs)
        reporter.flush_summary()
        return status if status != EXIT_OK else EXIT_TOOL_FAILURE

    if not whole_output_was_json:
        reporter.note(
            "Note: the verifier printed extra text alongside its JSON result. "
            "The result below came from the JSON object in that output."
        )

    ok = payload.get("ok") is True
    problems: list[str] = []

    # A result that claims success has to carry the fields that make the claim
    # checkable. Valid JSON missing them is a broken verifier, not a pass.
    if ok:
        if kind == "range":
            missing = [
                key
                for key in ("verified_count", "total", "agent_count", "human_count")
                if not isinstance(payload.get(key), int)
                or isinstance(payload.get(key), bool)
            ]
            if missing:
                problems.append(
                    "the verifier reported success without these fields: "
                    + ", ".join(missing)
                )
        else:
            missing = [
                key for key in ("device_id", "mode") if not sanitize(payload.get(key))
            ]
            if missing:
                problems.append(
                    "the verifier reported success without these fields: "
                    + ", ".join(missing)
                )

    if kind == "range":
        outputs["verified_count"] = as_count(payload.get("verified_count"))
        outputs["agent_count"] = as_count(payload.get("agent_count"))
        outputs["human_count"] = as_count(payload.get("human_count"))
        modes_value = payload.get("modes")
        modes = [sanitize(item) for item in modes_value] if isinstance(modes_value, list) else []
        modes = [item for item in modes if item]
        outputs["modes"] = ",".join(modes)
        # Claim the summary path only when the file is really there. The old
        # step echoed the input back whether or not the CLI ever wrote it.
        if summary_output and Path(summary_output).is_file():
            outputs["summary_path"] = sanitize(summary_output)
        elif summary_output:
            reporter.note(
                f"The verifier did not write a summary file at {summary_output}, "
                "so summary_path stays empty."
            )
        if require_mode:
            offenders = sorted({item for item in modes if item != require_mode})
            if offenders:
                problems.append(
                    f"require-mode is {require_mode} but the range carries "
                    + ", ".join(offenders)
                )
            elif ok and not modes and as_count(payload.get("total")) != "0":
                problems.append(
                    f"require-mode is {require_mode} but the verifier reported "
                    "no signature mode at all"
                )
    else:
        outputs["device_id"] = sanitize(payload.get("device_id"))
        outputs["mode"] = sanitize(payload.get("mode"))
        if require_mode and ok and outputs["mode"] != require_mode:
            problems.append(
                f"require-mode is {require_mode} but the manifest is signed "
                f"{outputs['mode'] or 'with no mode'}"
            )

    passed = ok and not problems
    outputs["ok"] = TRUE if passed else FALSE
    write_outputs(outputs)

    error_text = redact(sanitize(payload.get("error") or ""))
    if kind == "range":
        reporter.summary(
            heading,
            "",
            "**Status:** %s" % ("passed" if passed else "failed"),
            "**Commits verified:** %s / %s"
            % (outputs["verified_count"], as_count(payload.get("total"))),
            "**Agent commits:** %s" % outputs["agent_count"],
            "**Human commits:** %s" % outputs["human_count"],
            "**Modes:** %s" % (", ".join(modes) or "none"),
        )
        if verify_agent_scope:
            reporter.summary("**Agent scope signatures:** requested from the verifier")
        failures = _failure_rows(payload)
        if failures:
            reporter.summary("", "### Failures", "", *failures)
    else:
        reporter.summary(
            heading,
            "",
            "**Status:** %s" % ("passed" if passed else "failed"),
            "**Device id:** %s" % (outputs["device_id"] or "none reported"),
            "**Signature mode:** %s" % (outputs["mode"] or "none reported"),
        )
    if error_text:
        reporter.summary("", "**Verifier error:** %s" % error_text)
    if problems:
        reporter.summary("", "### Policy problems", "")
        for problem in problems:
            reporter.error(problem)
            reporter.summary(f"- {problem}")
    if not ok:
        reporter.error(
            f"the verifier reported ok={payload.get('ok')!r}, which is not an "
            "affirmative verified result"
        )

    reporter.flush_summary()

    if status != EXIT_OK:
        return status
    if passed:
        return EXIT_OK
    return EXIT_VERIFICATION_FAILURE


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
