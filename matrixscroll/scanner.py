"""
Project scanner — reads a project directory and infers a "stack profile".

This is Digital Rain's eyes: it answers "what is the user actually building?"
from concrete on-disk signals (manifests, lockfiles, config files, the file tree,
and the README) so recommendations are grounded in the real project rather than a
vague description. Pure stdlib, no third-party dependencies.

Output is a plain dict (JSON-serialisable) consumed by the MCP tools:

    {
      "path": "...",
      "languages": ["python", "typescript"],
      "package_managers": ["pip", "npm"],
      "frameworks": ["flask", "next"],
      "notable_sdks": ["stripe", "supabase"],
      "manifests": ["package.json", "requirements.txt"],
      "components": [{"path": ".", "kind": "node", ...}],
      "suggested_commands": [{"label": "Run dev server", ...}],
      "launch_readiness": {"status": "ready", ...},
      "security_posture": {"status": "clean", ...},
      "signals": ["Dockerfile", "tsconfig.json", "tailwind"],
      "readme_excerpt": "...",
      "file_summary": {"py": 12, "ts": 30, ...}
    }
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9/3.10 support.
    tomllib = None

# Directories that are noise for stack detection.
_SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", "out", ".next", ".venv", "venv",
    "__pycache__", ".mypy_cache", ".pytest_cache", "target", "vendor",
    ".idea", ".vscode", "coverage", ".turbo", ".cache", "scratch",
}

_SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "secrets.json",
    "service-account.json",
}
_SENSITIVE_FILE_SUFFIXES = (".pem", ".key", ".p12", ".pfx")

# Extension -> language.
_EXT_LANG = {
    "py": "python", "ts": "typescript", "tsx": "typescript", "js": "javascript",
    "jsx": "javascript", "html": "html", "css": "css", "go": "go", "rs": "rust", "rb": "ruby", "java": "java",
    "kt": "kotlin", "php": "php", "cs": "csharp", "swift": "swift", "c": "c",
    "cpp": "cpp", "cc": "cpp", "h": "c", "hpp": "cpp", "scala": "scala",
    "ex": "elixir", "exs": "elixir", "dart": "dart", "vue": "vue", "svelte": "svelte",
}

# Substrings that appear in dependency lists -> framework label.
_FRAMEWORK_HINTS = {
    "next": "next", "react": "react", "vue": "vue", "svelte": "svelte",
    "vite": "vite",
    "@angular/core": "angular", "express": "express", "fastify": "fastify",
    "nestjs": "nestjs", "@nestjs/core": "nestjs", "fastapi": "fastapi",
    "flask": "flask", "django": "django", "starlette": "starlette",
    "rails": "rails", "sinatra": "sinatra", "spring-boot": "spring",
    "gin-gonic": "gin", "fiber": "fiber", "axum": "axum", "actix": "actix",
    "remix": "remix", "nuxt": "nuxt", "astro": "astro", "solid-js": "solid",
}

# Substrings -> notable SDK/service the project integrates with. These drive the
# best MCP-server recommendations ("you use Stripe -> here's the Stripe MCP").
_SDK_HINTS = {
    "stripe": "stripe", "supabase": "supabase", "openai": "openai",
    "anthropic": "anthropic", "@anthropic-ai": "anthropic", "twilio": "twilio",
    "prisma": "prisma", "drizzle": "drizzle", "mongoose": "mongodb",
    "mongodb": "mongodb", "pg": "postgres", "psycopg": "postgres",
    "redis": "redis", "ioredis": "redis", "boto3": "aws", "aws-sdk": "aws",
    "@aws-sdk": "aws", "firebase": "firebase", "firebase-admin": "firebase",
    "@vercel": "vercel", "sentry": "sentry", "@sentry": "sentry",
    "sendgrid": "sendgrid", "resend": "resend", "clerk": "clerk",
    "@clerk": "clerk", "auth0": "auth0",     "graphql": "graphql",
    "playwright": "playwright", "puppeteer": "puppeteer", "three": "threejs",
    "@react-three/fiber": "threejs", "@react-three/drei": "threejs",
    "pinecone": "pinecone", "weaviate": "weaviate", "shopify": "shopify",
    "slack": "slack", "@slack": "slack", "discord.js": "discord", "discord": "discord",
    "notion": "notion", "@notionhq": "notion", "octokit": "github", "PyGithub": "github",
    # ML & Data Analysis libraries
    "pandas": "pandas", "numpy": "numpy", "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn", "matplotlib": "matplotlib", "seaborn": "seaborn",
    "tensorflow": "tensorflow", "torch": "pytorch", "pytorch": "pytorch",
    "keras": "keras", "jax": "jax", "xgboost": "xgboost", "lightgbm": "lightgbm",
}

_MANIFEST_NAMES = {
    "package.json", "requirements.txt", "pyproject.toml", "setup.py",
    "setup.cfg", "go.mod", "Cargo.toml", "Gemfile", "composer.json",
    "pom.xml", "build.gradle", "build.gradle.kts",
}

_PUBLIC_SITE_ROUTE_NAMES = {
    "docs", "pricing", "account", "verify", "spec", "compare", "device",
    "ecosystem", "roadmap", "api",
}

_SURFACE_KEYWORD_HINTS = {
    "model context protocol": ("signals", "mcp"),
    " mcp ": ("signals", "mcp"),
    '"mcp"': ("signals", "mcp"),
    "sigstore": ("signals", "sigstore"),
    "cosign": ("signals", "cosign"),
    "in-toto": ("signals", "in-toto"),
    "slsa": ("signals", "slsa"),
    "provenance": ("signals", "provenance"),
    "verify": ("signals", "verification"),
    "verification": ("signals", "verification"),
    "attestation": ("signals", "attestation"),
    "attestations": ("signals", "attestation"),
    "ed25519": ("signals", "ed25519"),
    "supply chain": ("signals", "supply-chain"),
    "security": ("signals", "security"),
    "trust": ("signals", "trust"),
    "protocol": ("signals", "protocol"),
    "github action": ("signals", "github-action"),
    "github actions": ("signals", "github-action"),
    "pypi": ("signals", "pypi"),
    "vercel": ("notable_sdks", "vercel"),
    "supabase": ("notable_sdks", "supabase"),
    "stripe": ("notable_sdks", "stripe"),
}

_SALIENT_SIGNALS = (
    "static-site",
    "docs-site",
    "vercel-config",
    "github-action",
    "mcp",
    "verification",
    "provenance",
    "protocol",
    "security",
    "attestation",
    "supply-chain",
    "trust",
    "sigstore",
    "cosign",
    "in-toto",
    "slsa",
    "pypi",
)

_KNOWN_COMMAND_PREFIXES = (
    "npm ",
    "pnpm ",
    "yarn ",
    "python -m ",
    "go ",
    "cargo ",
    "bundle ",
    "composer ",
    "mvn ",
    "gradle ",
)
_SHELL_CONTROL_RE = re.compile(r"[;&|<>`]")
_DESTRUCTIVE_PATTERNS = (
    re.compile(r"\brm\s+-[^\n]*r[^\n]*f\b", re.IGNORECASE),
    re.compile(r"\brmdir\b", re.IGNORECASE),
    re.compile(r"\bdel\s+", re.IGNORECASE),
    re.compile(r"\berase\s+", re.IGNORECASE),
    re.compile(r"\bremove-item\b", re.IGNORECASE),
    re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
    re.compile(r"\bgit\s+clean\s+-[^\n]*f\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+system\s+prune\b", re.IGNORECASE),
    re.compile(r"\bdrop\s+database\b", re.IGNORECASE),
    re.compile(r"\bformat\b", re.IGNORECASE),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\breboot\b", re.IGNORECASE),
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"\b([A-Z0-9_.-]*(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|"
    r"PRIVATE[_-]?KEY|ACCESS[_-]?KEY)[A-Z0-9_.-]*)\b"
    r"(\s*[:=]\s*)"
    r"([\"']?)"
    r"([^\"'\s,;]+)"
    r"(\3)",
    re.IGNORECASE,
)
_URL_CREDENTIAL_RE = re.compile(r"\b(https?://)([^/@\s:]+):([^/@\s]+)@")


def _add(seq: list, value: str) -> None:
    if value and value not in seq:
        seq.append(value)


def _hint_scan(haystack: str, hints: dict, into: list) -> None:
    """Match dependency hints on alphanumeric word boundaries.

    A plain substring test produces cross-ecosystem false positives — e.g.
    "express" inside "regular expressions", or "pg" inside "ripgrep". A hint
    only counts when the characters flanking the match are not alphanumeric,
    so the needle is a standalone token rather than a fragment of a longer word.
    Separator characters inside a needle (``@``, ``/``, ``-``, ``.``) are left
    intact; only the outer boundaries are checked.
    """
    low = haystack.lower()
    n = len(low)
    for needle, label in hints.items():
        nl = needle.lower()
        start = 0
        while True:
            i = low.find(nl, start)
            if i < 0:
                break
            before = low[i - 1] if i > 0 else ""
            after = low[i + len(nl)] if i + len(nl) < n else ""
            if not (before.isalnum() or after.isalnum()):
                _add(into, label)
                break
            start = i + 1


def _apply_surface_keyword_hints(profile: dict, text: str) -> None:
    low = f" {text.lower()} "
    for needle, (bucket, value) in _SURFACE_KEYWORD_HINTS.items():
        if needle in low:
            _add(profile[bucket], value)


def _surface_candidate_paths(root: Path) -> list[Path]:
    candidates = [
        root / "README.md",
        root / "README.rst",
        root / "README.txt",
        root / "index.html",
        root / "vercel.json",
    ]
    for route in sorted(_PUBLIC_SITE_ROUTE_NAMES):
        candidates.append(root / route / "index.html")
    candidates.append(root / "docs" / "Documentation.html")

    workflow_dir = root / ".github" / "workflows"
    if workflow_dir.exists():
        candidates.extend(sorted(workflow_dir.glob("*.yml"))[:2])
        candidates.extend(sorted(workflow_dir.glob("*.yaml"))[:2])

    out: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path.exists() and path.is_file() and path not in seen:
            out.append(path)
            seen.add(path)
    return out[:10]


def _scan_surface_content(root: Path, profile: dict, ext_counts: dict[str, int]) -> None:
    route_dirs = {name for name in _PUBLIC_SITE_ROUTE_NAMES if (root / name).is_dir()}
    if (root / "vercel.json").exists():
        _add(profile["signals"], "vercel-config")
        _add(profile["notable_sdks"], "vercel")
    if (root / "index.html").exists() and ext_counts.get("html", 0) >= 2:
        _add(profile["frameworks"], "static-site")
    if len(route_dirs) >= 3:
        _add(profile["signals"], "docs-site")

    for path in _surface_candidate_paths(root):
        text = _redact_for_profile(root, profile, path, _read(path, limit=12_000), "surface content")
        if not text:
            continue
        _apply_surface_keyword_hints(profile, text)


def _read(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _security_posture() -> dict:
    return {
        "status": "clean",
        "dry_run": True,
        "secret_file_count": 0,
        "redacted_value_count": 0,
        "findings": [],
    }


def _relative_file(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _is_sensitive_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        name in _SENSITIVE_FILE_NAMES
        or name.startswith(".env.")
        or any(name.endswith(suffix) for suffix in _SENSITIVE_FILE_SUFFIXES)
    )


def _record_security_finding(
    profile: dict,
    *,
    severity: str,
    finding_type: str,
    path: str,
    message: str,
    redaction_count: int = 0,
) -> None:
    posture = profile.setdefault("security_posture", _security_posture())
    if finding_type == "sensitive_file_present":
        posture["secret_file_count"] = int(posture.get("secret_file_count") or 0) + 1
    if redaction_count:
        posture["redacted_value_count"] = int(posture.get("redacted_value_count") or 0) + redaction_count
    posture.setdefault("findings", []).append(
        {
            "severity": severity,
            "type": finding_type,
            "path": path,
            "message": message,
            **({"redaction_count": redaction_count} if redaction_count else {}),
        }
    )


def _redact_secret_values(text: str) -> tuple[str, int]:
    redaction_count = 0

    def replace_assignment(match: re.Match) -> str:
        nonlocal redaction_count
        value = match.group(4)
        if value in {"", "<redacted>", "<unset>"}:
            return match.group(0)
        redaction_count += 1
        return f"{match.group(1)}{match.group(2)}{match.group(3)}<redacted>{match.group(5)}"

    def replace_url(match: re.Match) -> str:
        nonlocal redaction_count
        redaction_count += 1
        return f"{match.group(1)}<redacted>:<redacted>@"

    redacted = _SECRET_ASSIGNMENT_RE.sub(replace_assignment, text)
    redacted = _URL_CREDENTIAL_RE.sub(replace_url, redacted)
    return redacted, redaction_count


def _redact_for_profile(root: Path, profile: dict, path: Path, text: str, surface: str) -> str:
    redacted, count = _redact_secret_values(text)
    if count:
        _record_security_finding(
            profile,
            severity="warning",
            finding_type="secret_value_redacted",
            path=_relative_file(root, path),
            message=f"Secret-like value redacted from {surface}.",
            redaction_count=count,
        )
    return redacted


def _finalize_security_posture(profile: dict) -> None:
    posture = profile.setdefault("security_posture", _security_posture())
    has_review_items = bool(posture.get("secret_file_count")) or bool(posture.get("redacted_value_count"))
    posture["status"] = "review" if has_review_items else "clean"


def parse_notebook_file(path: Path) -> dict:
    """Parse a Jupyter notebook (.ipynb) to extract cells, imports, variables, and headers."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception as e:
        return {"filename": path.name, "error": f"Failed to parse JSON: {e}"}

    cells = data.get("cells", [])
    code_cells_count = 0
    markdown_cells_count = 0
    execution_counts = []
    imports = set()
    variables = set()
    headers = []

    # Common Python import patterns
    import_re = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)")
    # Simple assignment pattern to find defined variables (like df = ..., model = ...)
    var_re = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=[^=]")

    for cell in cells:
        cell_type = cell.get("cell_type")
        source = cell.get("source", [])
        if isinstance(source, str):
            source_lines = source.splitlines()
        elif isinstance(source, list):
            source_lines = source
        else:
            source_lines = []

        if cell_type == "code":
            code_cells_count += 1
            exec_count = cell.get("execution_count")
            if exec_count is not None:
                execution_counts.append(exec_count)
            
            for line in source_lines:
                imp_match = import_re.match(line)
                if imp_match:
                    imports.add(imp_match.group(1))
                
                var_match = var_re.match(line)
                if var_match:
                    var_name = var_match.group(1)
                    if var_name not in ("import", "from", "print", "if", "for", "while", "return", "def", "class"):
                        variables.add(var_name)
                        
        elif cell_type == "markdown":
            markdown_cells_count += 1
            for line in source_lines:
                if line.strip().startswith("#"):
                    headers.append(line.strip())

    # Check execution order health
    out_of_order = False
    if len(execution_counts) > 1:
        # Check if they are non-decreasing
        for i in range(len(execution_counts) - 1):
            if execution_counts[i] > execution_counts[i + 1]:
                out_of_order = True
                break

    return {
        "filename": path.name,
        "code_cells": code_cells_count,
        "markdown_cells": markdown_cells_count,
        "execution_counts": execution_counts[:30],
        "execution_health": "out_of_order" if out_of_order else "ordered",
        "imports": sorted(list(imports)),
        "variables": sorted(list(variables))[:20],
        "headers": headers[:10],
    }


def scan_project(
    path: str,
    max_files: int = 4000,
    max_notebooks: int = 5,
    exclude_dirs: list[str] | None = None,
) -> dict:
    """Build a stack profile for the project rooted at `path`."""
    root = Path(path).expanduser().resolve()
    skip_dirs = set(_SKIP_DIRS)
    if exclude_dirs:
        skip_dirs.update(exclude_dirs)
    profile = {
        "path": str(root),
        "languages": [],
        "package_managers": [],
        "frameworks": [],
        "notable_sdks": [],
        "manifests": [],
        "components": [],
        "suggested_commands": [],
        "launch_readiness": {},
        "security_posture": _security_posture(),
        "signals": [],
        "readme_excerpt": "",
        "file_summary": {},
    }
    if not root.exists() or not root.is_dir():
        profile["error"] = f"Not a directory: {root}"
        return profile

    ext_counts: dict[str, int] = {}
    notebook_paths = []
    manifest_paths: list[Path] = []
    seen = 0
    manifest_names_lower = {item.lower() for item in _MANIFEST_NAMES}
    try:
        stop = False
        # Prune noise directories before descending so large trees such as
        # node_modules or .venv are never walked, instead of filtering files
        # after the fact.
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for filename in filenames:
                p = Path(dirpath) / filename
                if _is_sensitive_file(p):
                    _add(profile["signals"], "secret-file")
                    _record_security_finding(
                        profile,
                        severity="review",
                        finding_type="sensitive_file_present",
                        path=_relative_file(root, p),
                        message="Sensitive local file detected; contents were not read during stack scan.",
                    )
                seen += 1
                if seen > max_files:
                    stop = True
                    break
                ext = p.suffix.lstrip(".").lower()
                if ext:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
                name = p.name.lower()
                if p.name in _MANIFEST_NAMES or name in manifest_names_lower:
                    manifest_paths.append(p)
                # Config-file signals (presence is meaningful regardless of content).
                if name == "dockerfile":
                    _add(profile["signals"], "Dockerfile")
                elif name == "docker-compose.yml" or name == "docker-compose.yaml":
                    _add(profile["signals"], "docker-compose")
                elif name == "tsconfig.json":
                    _add(profile["signals"], "tsconfig.json")
                elif name.startswith("tailwind.config"):
                    _add(profile["signals"], "tailwind")
                elif name.startswith("vite.config"):
                    _add(profile["signals"], "vite")
                elif name == "schema.prisma":
                    _add(profile["signals"], "prisma")
                    _add(profile["notable_sdks"], "prisma")
                elif name == ".cursorrules" or ".cursor" in p.parts:
                    _add(profile["signals"], "cursor-config")

                # Collect Jupyter Notebooks
                if ext == "ipynb" and len(notebook_paths) < max_notebooks:
                    notebook_paths.append(p)
            if stop:
                break
    except Exception as e:
        profile["error"] = f"Scan error: {e}"

    profile["file_summary"] = dict(
        sorted(ext_counts.items(), key=lambda kv: kv[1], reverse=True)[:15]
    )
    for ext, _n in ext_counts.items():
        lang = _EXT_LANG.get(ext)
        if lang:
            _add(profile["languages"], lang)

    _scan_manifests(root, profile, manifest_paths)
    profile["suggested_commands"] = _flatten_suggested_commands(profile["components"])
    profile["launch_readiness"] = assess_launch_readiness(root, profile)
    _scan_readme(root, profile)
    _scan_surface_content(root, profile, ext_counts)
    _finalize_security_posture(profile)

    if notebook_paths:
        profile["notebooks"] = []
        for np_path in notebook_paths:
            nb_profile = parse_notebook_file(np_path)
            profile["notebooks"].append(nb_profile)
            for imp in nb_profile.get("imports", []):
                _hint_scan(imp, _SDK_HINTS, profile["notable_sdks"])

    return profile


def _manifest_label(root: Path, path: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return path.name
    return path.name if rel.parent == Path(".") else rel.as_posix()


def _add_manifest(profile: dict, root: Path, path: Path) -> None:
    _add(profile["manifests"], _manifest_label(root, path))


def _paths_by_name(root: Path, manifest_paths: list[Path], name: str) -> list[Path]:
    matches = [path for path in manifest_paths if path.name.lower() == name.lower()]
    root_match = root / name
    if root_match.exists() and root_match not in matches:
        matches.insert(0, root_match)
    return sorted(matches, key=lambda path: (path.parent != root, str(path)))


def _node_package_manager(root: Path, package_dir: Path) -> str:
    if (package_dir / "pnpm-lock.yaml").exists() or (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (package_dir / "yarn.lock").exists() or (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _rel_dir(root: Path, path: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "."
    return "." if rel == Path(".") else rel.as_posix()


def _command(label: str, command: str, cwd: str, **metadata: str) -> dict:
    item = {"label": label, "command": command, "cwd": cwd}
    item.update({key: value for key, value in metadata.items() if value})
    return item


def _add_command(commands: list[dict], label: str, command: str, cwd: str, **metadata: str) -> None:
    item = _command(label, command, cwd, **metadata)
    if item not in commands:
        commands.append(item)


def _node_install_command(package_manager: str) -> str:
    if package_manager == "pnpm":
        return "pnpm install"
    if package_manager == "yarn":
        return "yarn install"
    return "npm install"


def _node_run_command(package_manager: str, script: str) -> str:
    if package_manager == "pnpm":
        return f"pnpm {script}"
    if package_manager == "yarn":
        return f"yarn {script}"
    if script == "test":
        return "npm test"
    return f"npm run {script}"


def _component_languages(component_dir: Path, fallback: str) -> list[str]:
    languages: list[str] = []
    try:
        for p in component_dir.rglob("*"):
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            if not p.is_file():
                continue
            lang = _EXT_LANG.get(p.suffix.lstrip(".").lower())
            if lang:
                _add(languages, lang)
    except OSError:
        pass
    if not languages:
        _add(languages, fallback)
    return languages


def _component(
    root: Path,
    manifest: Path,
    kind: str,
    *,
    languages: list[str] | None = None,
    frameworks: list[str] | None = None,
    notable_sdks: list[str] | None = None,
    package_manager: str | None = None,
    scripts: dict[str, str] | None = None,
    suggested_commands: list[dict] | None = None,
) -> dict:
    item = {
        "path": _rel_dir(root, manifest.parent),
        "kind": kind,
        "manifest": _manifest_label(root, manifest),
        "languages": languages or [],
        "frameworks": frameworks or [],
        "notable_sdks": notable_sdks or [],
        "suggested_commands": suggested_commands or [],
    }
    if package_manager:
        item["package_manager"] = package_manager
    if scripts:
        item["scripts"] = scripts
    return item


def _flatten_suggested_commands(components: list[dict], limit: int = 10) -> list[dict]:
    commands: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for component in components:
        for command in component.get("suggested_commands") or []:
            key = (command.get("cwd", "."), command.get("command", ""))
            if not key[1] or key in seen:
                continue
            seen.add(key)
            commands.append(command)
            if len(commands) >= limit:
                return commands
    return commands


def _workspace_relative_path_is_safe(root: Path, cwd: str) -> bool:
    try:
        resolved = (root / cwd).resolve()
    except (OSError, RuntimeError):
        return False
    root_text = str(root.resolve()).rstrip("\\/")
    resolved_text = str(resolved).rstrip("\\/")
    return resolved_text == root_text or resolved_text.startswith(root_text + "\\") or resolved_text.startswith(root_text + "/")


def _stage_for_command(command: dict) -> str:
    label = str(command.get("label") or "").lower()
    command_text = str(command.get("command") or "").lower()
    if "install" in label or command_text.endswith(" install") or " install" in command_text:
        return "install"
    if "lint" in label or " lint" in command_text:
        return "lint"
    if "build" in label or " build" in command_text:
        return "build"
    if "test" in label or " test" in command_text:
        return "test"
    if "api" in label:
        return "run_api"
    if "dev" in label:
        return "run_dev"
    if "run" in label:
        return "run_app"
    return "other"


def _sequence_for_stage(stage: str) -> int:
    return {
        "install": 10,
        "lint": 30,
        "build": 40,
        "test": 50,
        "run_api": 60,
        "run_dev": 70,
        "run_app": 80,
    }.get(stage, 90)


def _matches_destructive_pattern(text: str) -> str | None:
    for pattern in _DESTRUCTIVE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def _validate_launch_command(root: Path, command: dict, index: int) -> tuple[dict, list[dict]]:
    command_text = str(command.get("command") or "").strip()
    source_text = str(command.get("source") or "").strip()
    source_for_shell_check = source_text.replace("<redacted>", "REDACTED")
    cwd = str(command.get("cwd") or ".")
    stage = _stage_for_command(command)
    issues: list[dict] = []
    validations: list[str] = []

    if command_text:
        validations.append("non_empty_command")
    else:
        issues.append({"severity": "blocker", "message": "command is empty", "command": command})

    if _workspace_relative_path_is_safe(root, cwd):
        validations.append("cwd_inside_workspace")
    else:
        issues.append({"severity": "blocker", "message": "cwd escapes workspace", "command": command})

    destructive_match = _matches_destructive_pattern(" ".join([command_text, source_text]))
    if destructive_match:
        issues.append(
            {
                "severity": "blocker",
                "message": f"destructive pattern detected: {destructive_match}",
                "command": command,
            }
        )
    else:
        validations.append("no_destructive_patterns")

    if _SHELL_CONTROL_RE.search(command_text):
        issues.append({"severity": "warning", "message": "command contains shell control characters", "command": command})
    elif command_text:
        validations.append("plain_command")

    if source_text and _SHELL_CONTROL_RE.search(source_for_shell_check):
        issues.append({"severity": "warning", "message": "package script contains shell control characters", "command": command})
    elif source_text:
        validations.append("plain_source_script")

    if command_text and not command_text.startswith(_KNOWN_COMMAND_PREFIXES):
        issues.append({"severity": "warning", "message": "command prefix is not in the known allowlist", "command": command})
    elif command_text:
        validations.append("known_command_prefix")

    safety = "blocked" if any(issue["severity"] == "blocker" for issue in issues) else ("review" if issues else "safe")
    validated = {
        **command,
        "stage": stage,
        "sequence": _sequence_for_stage(stage) + index,
        "safety": safety,
        "validations": validations,
    }
    if source_text:
        validated["source"] = source_text
    command_issues = [{**issue, "cwd": cwd, "command_text": command_text} for issue in issues]
    return validated, command_issues


def assess_launch_readiness(root: Path, profile: dict) -> dict:
    commands = profile.get("suggested_commands") or []
    if not commands:
        return {
            "status": "no_commands",
            "dry_run": True,
            "command_count": 0,
            "safe_command_count": 0,
            "warning_count": 0,
            "blocking_issue_count": 0,
            "commands": [],
            "issues": [],
            "launch_order": [],
        }

    validated_commands: list[dict] = []
    issues: list[dict] = []
    for index, command in enumerate(commands):
        validated, command_issues = _validate_launch_command(root, command, index)
        validated_commands.append(validated)
        issues.extend(command_issues)

    blocking = [issue for issue in issues if issue.get("severity") == "blocker"]
    warnings = [issue for issue in issues if issue.get("severity") == "warning"]
    status = "blocked" if blocking else ("review" if warnings else "ready")
    launch_order = sorted(validated_commands, key=lambda item: (item["sequence"], item.get("cwd", ""), item.get("command", "")))
    return {
        "status": status,
        "dry_run": True,
        "command_count": len(validated_commands),
        "safe_command_count": sum(1 for command in validated_commands if command["safety"] == "safe"),
        "warning_count": len(warnings),
        "blocking_issue_count": len(blocking),
        "commands": validated_commands,
        "issues": issues,
        "launch_order": launch_order,
    }


def _parse_pyproject_dependencies(raw: str) -> list[str]:
    if tomllib is None:
        return []
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError:
        return []
    deps: list[str] = []
    project = data.get("project") or {}
    if isinstance(project.get("dependencies"), list):
        deps.extend(str(item) for item in project["dependencies"])
    optional = project.get("optional-dependencies") or {}
    if isinstance(optional, dict):
        for values in optional.values():
            if isinstance(values, list):
                deps.extend(str(item) for item in values)
    poetry = ((data.get("tool") or {}).get("poetry") or {})
    poetry_deps = poetry.get("dependencies") or {}
    if isinstance(poetry_deps, dict):
        deps.extend(str(key) for key in poetry_deps)
    poetry_groups = (poetry.get("group") or {})
    if isinstance(poetry_groups, dict):
        for group in poetry_groups.values():
            group_deps = ((group or {}).get("dependencies") or {})
            if isinstance(group_deps, dict):
                deps.extend(str(key) for key in group_deps)
    return deps


def _python_package_manager(root: Path, pyproject: Path, raw: str) -> str:
    if "poetry" in raw or (pyproject.parent / "poetry.lock").exists() or (root / "poetry.lock").exists():
        return "poetry"
    if "[tool.uv]" in raw or (pyproject.parent / "uv.lock").exists() or (root / "uv.lock").exists():
        return "uv"
    return "pip"


def _python_install_command(package_manager: str, manifest_name: str) -> str:
    if package_manager == "poetry":
        return "poetry install"
    if package_manager == "uv":
        return "uv sync"
    if manifest_name == "requirements.txt":
        return "python -m pip install -r requirements.txt"
    return "python -m pip install -e ."


def _python_commands(
    root: Path,
    manifest: Path,
    package_manager: str,
    blob: str,
    frameworks: list[str],
) -> list[dict]:
    cwd = _rel_dir(root, manifest.parent)
    commands: list[dict] = []
    _add_command(commands, "Install dependencies", _python_install_command(package_manager, manifest.name), cwd)
    if "fastapi" in frameworks and (manifest.parent / "main.py").exists():
        _add_command(commands, "Run API server", "python -m uvicorn main:app --reload", cwd)
    if "flask" in frameworks and (manifest.parent / "app.py").exists():
        _add_command(commands, "Run dev server", "python -m flask --app app run", cwd)
    if "pytest" in blob.lower() or (manifest.parent / "tests").exists():
        _add_command(commands, "Run tests", "python -m pytest", cwd)
    return commands


def _scan_manifests(root: Path, profile: dict, manifest_paths: list[Path] | None = None) -> None:
    manifest_paths = manifest_paths or []
    # --- Node / npm-family ---
    for pkg in _paths_by_name(root, manifest_paths, "package.json"):
        _add_manifest(profile, root, pkg)
        raw = _read(pkg)
        scripts: dict[str, str] = {}
        raw_scripts: dict[str, str] = {}
        frameworks: list[str] = []
        notable_sdks: list[str] = []
        package_manager = _node_package_manager(root, pkg.parent)
        try:
            data = json.loads(raw)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            blob = " ".join(deps.keys())
            raw_scripts = {
                str(key): str(value)
                for key, value in (data.get("scripts") or {}).items()
                if isinstance(key, str) and isinstance(value, str)
            }
            scripts = {
                key: _redact_for_profile(root, profile, pkg, value, "package.json script")
                for key, value in raw_scripts.items()
            }
            if data.get("workspaces"):
                _add(profile["signals"], "workspaces")
        except (json.JSONDecodeError, AttributeError):
            blob = raw
        _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(blob, _SDK_HINTS, notable_sdks)
        _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
        _hint_scan(blob, _SDK_HINTS, profile["notable_sdks"])
        _add(profile["package_managers"], package_manager)
        component_commands: list[dict] = []
        install_cwd = "." if pkg.parent != root and (root / "pnpm-lock.yaml").exists() else _rel_dir(root, pkg.parent)
        _add_command(component_commands, "Install dependencies", _node_install_command(package_manager), install_cwd)
        for script, label in (
            ("dev", "Run dev server"),
            ("build", "Build"),
            ("test", "Run tests"),
            ("lint", "Run lint"),
        ):
            if script in raw_scripts:
                _add_command(
                    component_commands,
                    label,
                    _node_run_command(package_manager, script),
                    _rel_dir(root, pkg.parent),
                    script=script,
                    source=scripts.get(script) or raw_scripts[script],
                )
        languages = _component_languages(pkg.parent, "javascript")
        if "typescript" in blob.lower() or (pkg.parent / "tsconfig.json").exists():
            _add(languages, "typescript")
        profile["components"].append(
            _component(
                root,
                pkg,
                "node",
                languages=languages,
                frameworks=frameworks,
                notable_sdks=notable_sdks,
                package_manager=package_manager,
                scripts=scripts,
                suggested_commands=component_commands,
            )
        )
    if (root / "pnpm-workspace.yaml").exists():
        _add(profile["signals"], "pnpm-workspace")

    # --- Python ---
    for req in _paths_by_name(root, manifest_paths, "requirements.txt"):
        _add_manifest(profile, root, req)
        _add(profile["package_managers"], "pip")
        blob = _read(req)
        frameworks: list[str] = []
        notable_sdks: list[str] = []
        _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(blob, _SDK_HINTS, notable_sdks)
        _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
        _hint_scan(blob, _SDK_HINTS, profile["notable_sdks"])
        profile["components"].append(
            _component(
                root,
                req,
                "python",
                languages=_component_languages(req.parent, "python"),
                frameworks=frameworks,
                notable_sdks=notable_sdks,
                package_manager="pip",
                suggested_commands=_python_commands(root, req, "pip", blob, frameworks),
            )
        )
    for pyproject in _paths_by_name(root, manifest_paths, "pyproject.toml"):
        _add_manifest(profile, root, pyproject)
        blob = _read(pyproject)
        deps_blob = " ".join(_parse_pyproject_dependencies(blob)) or blob
        package_manager = _python_package_manager(root, pyproject, blob)
        frameworks: list[str] = []
        notable_sdks: list[str] = []
        _add(profile["package_managers"], package_manager)
        _hint_scan(deps_blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(deps_blob, _SDK_HINTS, notable_sdks)
        _hint_scan(deps_blob, _FRAMEWORK_HINTS, profile["frameworks"])
        _hint_scan(deps_blob, _SDK_HINTS, profile["notable_sdks"])
        profile["components"].append(
            _component(
                root,
                pyproject,
                "python",
                languages=_component_languages(pyproject.parent, "python"),
                frameworks=frameworks,
                notable_sdks=notable_sdks,
                package_manager=package_manager,
                suggested_commands=_python_commands(root, pyproject, package_manager, deps_blob, frameworks),
            )
        )

    # --- Python (legacy setuptools manifests) ---
    setup_paths = (
        _paths_by_name(root, manifest_paths, "setup.py")
        + _paths_by_name(root, manifest_paths, "setup.cfg")
    )
    for setup in setup_paths:
        _add_manifest(profile, root, setup)
        _add(profile["package_managers"], "pip")
        blob = _read(setup)
        frameworks: list[str] = []
        notable_sdks: list[str] = []
        _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(blob, _SDK_HINTS, notable_sdks)
        _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
        _hint_scan(blob, _SDK_HINTS, profile["notable_sdks"])
        # A richer manifest (pyproject.toml / requirements.txt) in the same
        # directory already contributes a Python component; only the package
        # manager and manifest record are needed from the legacy file.
        if (setup.parent / "pyproject.toml").exists() or (setup.parent / "requirements.txt").exists():
            continue
        profile["components"].append(
            _component(
                root,
                setup,
                "python",
                languages=_component_languages(setup.parent, "python"),
                frameworks=frameworks,
                notable_sdks=notable_sdks,
                package_manager="pip",
                suggested_commands=_python_commands(root, setup, "pip", blob, frameworks),
            )
        )

    # --- Go ---
    for gomod in _paths_by_name(root, manifest_paths, "go.mod"):
        _add_manifest(profile, root, gomod)
        _add(profile["package_managers"], "go modules")
        blob = _read(gomod)
        frameworks: list[str] = []
        notable_sdks: list[str] = []
        _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(blob, _SDK_HINTS, notable_sdks)
        _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
        _hint_scan(blob, _SDK_HINTS, profile["notable_sdks"])
        cwd = _rel_dir(root, gomod.parent)
        profile["components"].append(
            _component(
                root,
                gomod,
                "go",
                languages=_component_languages(gomod.parent, "go"),
                frameworks=frameworks,
                notable_sdks=notable_sdks,
                package_manager="go modules",
                suggested_commands=[
                    _command("Install dependencies", "go mod download", cwd),
                    _command("Run tests", "go test ./...", cwd),
                ],
            )
        )

    # --- Rust ---
    for cargo in _paths_by_name(root, manifest_paths, "Cargo.toml"):
        _add_manifest(profile, root, cargo)
        _add(profile["package_managers"], "cargo")
        blob = _read(cargo)
        frameworks: list[str] = []
        notable_sdks: list[str] = []
        _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(blob, _SDK_HINTS, notable_sdks)
        _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
        _hint_scan(blob, _SDK_HINTS, profile["notable_sdks"])
        cwd = _rel_dir(root, cargo.parent)
        profile["components"].append(
            _component(
                root,
                cargo,
                "rust",
                languages=_component_languages(cargo.parent, "rust"),
                frameworks=frameworks,
                notable_sdks=notable_sdks,
                package_manager="cargo",
                suggested_commands=[
                    _command("Install dependencies", "cargo fetch", cwd),
                    _command("Run tests", "cargo test", cwd),
                    _command("Run app", "cargo run", cwd),
                ],
            )
        )

    # --- Ruby / PHP / Java (lighter touch) ---
    for gemfile in _paths_by_name(root, manifest_paths, "Gemfile"):
        _add_manifest(profile, root, gemfile)
        _add(profile["package_managers"], "bundler")
        blob = _read(gemfile)
        frameworks: list[str] = []
        _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
        cwd = _rel_dir(root, gemfile.parent)
        profile["components"].append(
            _component(
                root,
                gemfile,
                "ruby",
                languages=_component_languages(gemfile.parent, "ruby"),
                frameworks=frameworks,
                package_manager="bundler",
                suggested_commands=[
                    _command("Install dependencies", "bundle install", cwd),
                    _command("Run tests", "bundle exec rake test", cwd),
                ],
            )
        )
    for composer in _paths_by_name(root, manifest_paths, "composer.json"):
        _add_manifest(profile, root, composer)
        _add(profile["package_managers"], "composer")
        cwd = _rel_dir(root, composer.parent)
        profile["components"].append(
            _component(
                root,
                composer,
                "php",
                languages=_component_languages(composer.parent, "php"),
                package_manager="composer",
                suggested_commands=[
                    _command("Install dependencies", "composer install", cwd),
                    _command("Run tests", "composer test", cwd),
                ],
            )
        )
    for pom in _paths_by_name(root, manifest_paths, "pom.xml"):
        _add_manifest(profile, root, pom)
        _add(profile["package_managers"], "maven")
        blob = _read(pom)
        frameworks: list[str] = []
        _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
        _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
        cwd = _rel_dir(root, pom.parent)
        profile["components"].append(
            _component(
                root,
                pom,
                "java",
                languages=_component_languages(pom.parent, "java"),
                frameworks=frameworks,
                package_manager="maven",
                suggested_commands=[
                    _command("Install dependencies", "mvn dependency:resolve", cwd),
                    _command("Run tests", "mvn test", cwd),
                ],
            )
        )
    for gradle in ("build.gradle", "build.gradle.kts"):
        for gradle_path in _paths_by_name(root, manifest_paths, gradle):
            _add_manifest(profile, root, gradle_path)
            _add(profile["package_managers"], "gradle")
            blob = _read(gradle_path)
            frameworks: list[str] = []
            _hint_scan(blob, _FRAMEWORK_HINTS, frameworks)
            _hint_scan(blob, _FRAMEWORK_HINTS, profile["frameworks"])
            cwd = _rel_dir(root, gradle_path.parent)
            profile["components"].append(
                _component(
                    root,
                    gradle_path,
                    "java",
                    languages=_component_languages(gradle_path.parent, "java"),
                    frameworks=frameworks,
                    package_manager="gradle",
                    suggested_commands=[
                        _command("Install dependencies", "gradle dependencies", cwd),
                        _command("Run tests", "gradle test", cwd),
                    ],
                )
            )
    if list(root.glob("*.csproj")):
        _add(profile["manifests"], "*.csproj")
        _add(profile["package_managers"], "nuget")


def _scan_readme(root: Path, profile: dict) -> None:
    for name in ("README.md", "README.rst", "README.txt", "readme.md", "README"):
        f = root / name
        if f.exists():
            text = _redact_for_profile(root, profile, f, _read(f, limit=4000), "README excerpt").strip()
            # Collapse whitespace for a compact excerpt.
            excerpt = re.sub(r"\s+", " ", text)[:1500]
            profile["readme_excerpt"] = excerpt
            return


def profile_summary(profile: dict) -> str:
    """One-line human/LLM-friendly summary of a stack profile."""
    parts = []
    if profile.get("languages"):
        parts.append("langs=" + ",".join(profile["languages"]))
    if profile.get("frameworks"):
        parts.append("frameworks=" + ",".join(profile["frameworks"]))
    if profile.get("notable_sdks"):
        parts.append("sdks=" + ",".join(profile["notable_sdks"]))
    if profile.get("package_managers"):
        parts.append("pkg=" + ",".join(profile["package_managers"]))
    signals = [s for s in profile.get("signals", []) if s in _SALIENT_SIGNALS]
    if signals:
        parts.append("signals=" + ",".join(signals[:6]))
    return "; ".join(parts) or "no clear stack detected"


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(json.dumps(scan_project(target), indent=2))
