"""Workspace resolution and per-project Digital Rain configuration."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

INSTALL_ROOT = Path(__file__).resolve().parent
CONFIG_FILENAME = "co-pilot.json"
ACTIVE_POINTER = Path.home() / ".cursor" / "co-pilot-active.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "workspace_root": ".",
    "vault": {
        "mode": "project",
        "path": "",
        "project_subdir": "docs/vault",
    },
    "notebooks": {
        "enabled": True,
        "warn_on_out_of_order": True,
        "max_notebooks": 10,
        "exclude_dirs": ["scratch", ".venv", "node_modules"],
    },
    "brainstorm": {
        "enabled": True,
        "max_suggestions": 6,
        "include_vault_context": True,
        "prefer_llm_enhancement": True,
    },
}


def _merge_defaults(config: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_CONFIG)
    for key, value in config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def get_active_workspace_raw() -> Path | None:
    if not ACTIVE_POINTER.exists():
        return None
    try:
        data = json.loads(ACTIVE_POINTER.read_text(encoding="utf-8"))
        path = data.get("workspace")
        if path:
            resolved = Path(path).expanduser().resolve()
            if resolved.is_dir():
                return resolved
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return None


def set_active_workspace(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"Not a directory: {resolved}")
    ACTIVE_POINTER.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_POINTER.write_text(
        json.dumps({"workspace": str(resolved)}, indent=2),
        encoding="utf-8",
    )
    return resolved


def resolve_workspace() -> tuple[Path, bool]:
    """Return (workspace_path, configured).

    Priority: COPILOT_WORKSPACE env -> active pointer -> install root.
    """
    env_path = os.environ.get("COPILOT_WORKSPACE", "").strip()
    if env_path:
        resolved = Path(env_path).expanduser().resolve()
        if resolved.is_dir():
            return resolved, True

    pointer = get_active_workspace_raw()
    if pointer is not None:
        return pointer, True

    return INSTALL_ROOT, False


def config_path_for(workspace: Path) -> Path:
    return workspace / ".cursor" / CONFIG_FILENAME


def load_config(workspace: Path | None = None) -> dict[str, Any]:
    ws = workspace if workspace is not None else resolve_workspace()[0]
    path = config_path_for(ws)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return _merge_defaults(data)
        except (OSError, json.JSONDecodeError):
            pass
    return deepcopy(DEFAULT_CONFIG)


def save_config(workspace: Path, config: dict[str, Any]) -> Path:
    merged = _merge_defaults(config)
    dest = config_path_for(workspace)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return dest


def ensure_default_config(workspace: Path) -> Path:
    dest = config_path_for(workspace)
    if not dest.exists():
        return save_config(workspace, deepcopy(DEFAULT_CONFIG))
    return dest


def resolve_vault_path(
    workspace: Path | None = None,
    config: dict[str, Any] | None = None,
) -> Path | None:
    ws = workspace if workspace is not None else resolve_workspace()[0]
    cfg = config or load_config(ws)
    vault_cfg = cfg.get("vault", {})
    mode = vault_cfg.get("mode", "project")

    if mode == "existing":
        raw = vault_cfg.get("path", "").strip()
        if not raw:
            return None
        path = Path(raw).expanduser().resolve()
        return path if path.is_dir() else None

    if mode == "project":
        subdir = vault_cfg.get("project_subdir", "docs/vault")
        return (ws / subdir).resolve()

    return None


def scaffold_project_vault(workspace: Path, subdir: str = "docs/vault") -> Path:
    vault_dir = (workspace / subdir).resolve()
    vault_dir.mkdir(parents=True, exist_ok=True)

    readme = vault_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Project Notes Vault\n\n"
            "Personal notes grounded by Digital Rain for this repository.\n",
            encoding="utf-8",
        )

    context = vault_dir / "project-context.md"
    if not context.exists():
        context.write_text(
            "# Project Context\n\n"
            "Capture architecture decisions, stack notes, and links here.\n",
            encoding="utf-8",
        )

    cfg = load_config(workspace)
    cfg["vault"]["mode"] = "project"
    cfg["vault"]["project_subdir"] = subdir
    save_config(workspace, cfg)
    return vault_dir


def workspace_status() -> dict[str, Any]:
    ws, configured = resolve_workspace()
    cfg = load_config(ws)
    vault_path = resolve_vault_path(ws, cfg)
    vault_exists = vault_path.is_dir() if vault_path else False
    return {
        "workspace": str(ws),
        "configured": configured,
        "config_path": str(config_path_for(ws)),
        "config_exists": config_path_for(ws).exists(),
        "vault_mode": cfg.get("vault", {}).get("mode"),
        "vault_path": str(vault_path) if vault_path else None,
        "vault_exists": vault_exists,
        "notebooks": cfg.get("notebooks", {}),
        "brainstorm": cfg.get("brainstorm", {}),
    }
