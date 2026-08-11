#!/usr/bin/env python3
"""Verify that every public JSON schema is present in an installed wheel."""

from __future__ import annotations

from pathlib import Path

import matrixscroll
from matrixscroll._schemas import schema_path, schemas_dir

SCHEMAS = (
    "action-envelope.v1.json",
    "commit-envelope.v1.1.json",
    "commit-envelope.v1.json",
    "evidence-pack.v1.json",
    "pqc-signature.v1.json",
    "release-manifest.v1.json",
    "ssx360.evidence-pack.v1.json",
    "ssx360.mcp-manifest.v1.json",
)


def main() -> int:
    package_dir = Path(matrixscroll.__file__).resolve().parent
    installed_dir = package_dir / "schemas"
    resolved_dir = schemas_dir().resolve()
    if resolved_dir != installed_dir.resolve():
        raise SystemExit(
            f"schema resolver fell back outside the installed package: {resolved_dir}"
        )

    missing = [
        name
        for name in SCHEMAS
        if schema_path(name).parent != installed_dir or not schema_path(name).is_file()
    ]
    if missing:
        raise SystemExit(f"wheel is missing schemas: {', '.join(missing)}")

    print(f"ok: {len(SCHEMAS)} schemas resolve from {installed_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
