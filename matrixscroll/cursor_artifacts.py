"""Render local project rule artifacts used by Digital Rain."""

from __future__ import annotations

import re
from pathlib import Path


# --- rules -----------------------------------------------------------------

def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "rule"


def render_rule(description: str, body: str, *,
                globs: str = "", always_apply: bool = False) -> str:
    """Return a valid `.cursor/rules/*.mdc` file as a string.

    - description: short trigger description (used for Agent-requested rules)
    - globs: comma-separated file patterns the rule auto-attaches to (optional)
    - always_apply: if True the rule is always in context
    """
    fm = ["---"]
    fm.append(f"description: {_yaml_scalar(description)}")
    fm.append(f"globs: {globs}")  # empty is fine; Cursor treats it as no auto-glob
    fm.append(f"alwaysApply: {'true' if always_apply else 'false'}")
    fm.append("---")
    return "\n".join(fm) + "\n\n" + body.strip() + "\n"


def _yaml_scalar(text: str) -> str:
    """Quote a one-line YAML scalar if it contains risky characters."""
    one_line = " ".join(text.splitlines()).strip()
    if one_line and re.search(r"[:#\"'\[\]{}]", one_line):
        escaped = one_line.replace('"', '\\"')
        return f'"{escaped}"'
    return one_line


def write_rule(project_path: str, filename: str, description: str, body: str,
               globs: str = "", always_apply: bool = False) -> Path:
    """Generate and write a rule file into project_path/.cursor/rules/."""
    p_path = Path(project_path).expanduser().resolve()
    rules_dir = p_path / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    name = filename
    if name.endswith(".mdc"):
        name = name[:-4]
    name = slugify(name) + ".mdc"
    
    file_path = rules_dir / name
    content = render_rule(description, body, globs=globs, always_apply=always_apply)
    file_path.write_text(content, encoding="utf-8")
    return file_path
