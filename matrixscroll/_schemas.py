"""Locate the JSON Schema files that ship with the package.

The canonical copies live in ``schemas/`` at the repository root, where SPEC.md
and the docs link them. The wheel maps that directory to ``matrixscroll/schemas``
through ``tool.hatch.build.targets.wheel.force-include``, so an installed
package carries the same files next to the module. Look in the installed
location first, then fall back to the repository root for source checkouts and
editable installs.
"""

from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_INSTALLED = _PACKAGE_DIR / "schemas"
_REPO_ROOT = _PACKAGE_DIR.parent / "schemas"


def schemas_dir() -> Path:
    """Directory holding the shipped schemas."""
    return _INSTALLED if _INSTALLED.is_dir() else _REPO_ROOT


def schema_path(filename: str) -> Path:
    """Path to one shipped schema by file name, for example ``commit-envelope.v1.json``.

    Returns the installed path even when the file is absent, so callers report a
    missing schema rather than a missing directory.
    """
    installed = _INSTALLED / filename
    if installed.is_file():
        return installed
    return _REPO_ROOT / filename
