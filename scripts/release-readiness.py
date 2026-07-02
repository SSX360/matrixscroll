#!/usr/bin/env python3
"""Verify matrixscroll release metadata before tagging v0.5.1 and publishing to PyPI."""

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
        "glama.json": read_version_from_glama(),
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

    try:
        pypi_latest, pypi_releases = fetch_pypi_versions()
        print(f"PyPI latest: {pypi_latest}")
        if target in pypi_releases:
            print(f"OK: {target} is published on PyPI")
        else:
            print(
                f"WARN: {target} is not on PyPI yet. Publish with "
                f"matrixscroll/.github/workflows/publish.yml and tag v{target}.",
                file=sys.stderr,
            )
            return 2
    except OSError as exc:
        print(f"WARN: could not reach PyPI ({exc})", file=sys.stderr)
        return 2

    print("Release readiness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
