#!/usr/bin/env python3
"""Verify matrixscroll release metadata before tagging and publishing to PyPI.

Exit 0 when the staged release is fully published, 2 when it is staged but not on
PyPI yet (expected on a release PR), and 1 when the metadata is inconsistent.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "matrixscroll" / "__init__.py"
GLAMA = ROOT / "glama.json"
README = ROOT / "README.md"
README_PIN = re.compile(r'matrixscroll(?:\[mcp\])?==([0-9]+\.[0-9]+\.[0-9]+)')
PYPI_URL = "https://pypi.org/pypi/matrixscroll/json"


def read_version_from_pyproject() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', text, re.MULTILINE)
    if not match:
        raise SystemExit(f"Could not parse version from {PYPROJECT}")
    return match.group(1)


def read_version_from_init() -> str:
    text = INIT.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        raise SystemExit(f"Could not parse __version__ from {INIT}")
    return match.group(1)


def read_version_from_glama() -> str:
    data = json.loads(GLAMA.read_text(encoding="utf-8"))
    return str(data["version"])


def fetch_pypi_versions() -> tuple[str, set[str]]:
    with urllib.request.urlopen(PYPI_URL, timeout=30) as resp:
        data = json.load(resp)
    latest = str(data["info"]["version"])
    releases = set(data.get("releases", {}).keys())
    return latest, releases


def read_readme_pins() -> set[str]:
    text = README.read_text(encoding="utf-8")
    return set(README_PIN.findall(text))


def main() -> int:
    versions = {
        "pyproject.toml": read_version_from_pyproject(),
        "__init__.py": read_version_from_init(),
    }
    unique = set(versions.values())
    print("Local version pins:")
    for path, version in versions.items():
        print(f"  {path}: {version}")

    if len(unique) != 1:
        print("FAIL: local version pins disagree", file=sys.stderr)
        return 1

    target = unique.pop()
    print(f"OK: local release target is {target}")

    try:
        pypi_latest, pypi_releases = fetch_pypi_versions()
    except OSError as exc:
        print(f"WARN: could not reach PyPI ({exc})", file=sys.stderr)
        return 2
    print(f"PyPI latest: {pypi_latest}")

    # glama.json is deliberately a release behind while a release is staged.
    # Glama installs packages[].version from PyPI, and so does the stdio smoke
    # step in ci-unit.yml, so pinning an unpublished version breaks both.
    # validate_glama_pypi.py enforces that; requiring an exact match with the
    # release target here contradicted it and deadlocked every release PR.
    glama_version = read_version_from_glama()
    print(f"glama.json pin: {glama_version}")
    if glama_version == target:
        print(f"OK: glama.json already at the release target {target}")
    elif glama_version in pypi_releases:
        print(
            f"OK: glama.json lags at published {glama_version} while {target} is staged; "
            f"bump it to {target} after PyPI publish completes"
        )
    else:
        print(
            f"FAIL: glama.json pins {glama_version}, which is neither the release "
            f"target {target} nor a published release",
            file=sys.stderr,
        )
        return 1

    readme_pins = read_readme_pins()
    print(f"README install pins: {sorted(readme_pins) or ['(none)']}")
    if not readme_pins:
        print("FAIL: README.md has no matrixscroll== pins", file=sys.stderr)
        return 1
    if readme_pins != {target}:
        print(
            f"FAIL: README pins {sorted(readme_pins)} disagree with release target {target}",
            file=sys.stderr,
        )
        return 1
    print(f"OK: README quickstart pins match {target}")

    if target in pypi_releases:
        print(f"OK: {target} is published on PyPI")
    else:
        print(
            f"WARN: {target} is not on PyPI yet. Publish with "
            f"matrixscroll/.github/workflows/publish.yml and tag v{target}.",
            file=sys.stderr,
        )
        return 2

    print("Release readiness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
