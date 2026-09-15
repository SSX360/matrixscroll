#!/usr/bin/env python3
"""Emit CycloneDX 1.6 JSON SBOM for the matrixscroll package."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
OUT = ROOT / "dist" / "sbom.cdx.json"


def _project_meta() -> tuple[str, str, list[str]]:
    text = PYPROJECT.read_text(encoding="utf-8")
    name_m = re.search(r'(?m)^name\s*=\s*"([^"]+)"', text)
    version_m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    if not name_m or not version_m:
        raise RuntimeError("could not parse name/version from pyproject.toml")
    deps_block = re.search(
        r"(?ms)^dependencies\s*=\s*\[(.*?)\]",
        text,
    )
    deps: list[str] = []
    if deps_block:
        deps = re.findall(r'"([^"]+)"', deps_block.group(1))
    return name_m.group(1), version_m.group(1), deps


def _parse_dep(req: str) -> tuple[str, str | None]:
    match = re.match(r"^([A-Za-z0-9_.-]+)\s*(.*)$", req.strip())
    if not match:
        return req, None
    return match.group(1), (match.group(2).strip() or None)


def main() -> None:
    name, version, deps = _project_meta()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    root_component = {
        "type": "library",
        "name": name,
        "version": version,
        "bom-ref": f"pkg:pypi/{name}@{version}",
        "purl": f"pkg:pypi/{name}@{version}",
        "licenses": [{"license": {"id": "Apache-2.0"}}],
    }
    components = []
    for dep in deps:
        dep_name, dep_ver = _parse_dep(dep)
        entry: dict = {
            "type": "library",
            "name": dep_name,
            "bom-ref": f"pkg:pypi/{dep_name}",
            "purl": f"pkg:pypi/{dep_name}",
            "licenses": [],
        }
        if dep_ver:
            entry["version"] = dep_ver
            entry["properties"] = [
                {"name": "matrixscroll:requirement", "value": dep},
            ]
        components.append(entry)

    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": now,
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "matrixscroll-generate_sbom",
                        "version": version,
                    }
                ]
            },
            "component": root_component,
            "licenses": [{"license": {"id": "Apache-2.0"}}],
        },
        "components": components,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(bom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
