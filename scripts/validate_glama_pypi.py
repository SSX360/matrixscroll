#!/usr/bin/env python3
"""Fail CI when glama.json pins a PyPI version that is not published yet."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLAMA_JSON = ROOT / "glama.json"


def _pypi_exists(package: str, version: str) -> bool:
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def main() -> int:
    data = json.loads(GLAMA_JSON.read_text(encoding="utf-8"))
    packages = data.get("packages") or []
    pypi_pins = [
        pkg for pkg in packages if pkg.get("registry") == "pypi" and pkg.get("version")
    ]
    if not pypi_pins:
        print("glama.json: no PyPI package pins to validate")
        return 0

    failed = False
    for pkg in pypi_pins:
        name = pkg["name"]
        version = pkg["version"]
        if _pypi_exists(name, version):
            print(f"ok: {name}=={version} is on PyPI")
            continue
        failed = True
        print(
            f"error: glama.json pins {name}=={version} but that release is not on PyPI yet; "
            "publish to PyPI before bumping glama.json or Glama builds will fail",
            file=sys.stderr,
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
