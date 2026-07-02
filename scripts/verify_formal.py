#!/usr/bin/env python3
"""Run TLC on all Matrix Scroll TLA+ models when tla2tools is available."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TLA_DIR = ROOT / "formal" / "tla"

MODELS = [
    ("CanonicalBytes.tla", "CanonicalBytes.cfg"),
    ("ScrollGate.tla", "ScrollGate.cfg"),
    ("AuthorityFive.tla", "AuthorityFive.cfg"),
    ("OrgPlanSync.tla", "OrgPlanSync.cfg"),
]


def find_tlc() -> list[str] | None:
    if jar := shutil.which("tlc2.jar"):
        return ["java", "-cp", jar, "tlc2.TLC"]
    tlc = shutil.which("tlc")
    if tlc:
        return [tlc]
    return None


def main() -> int:
    cmd = find_tlc()
    if cmd is None:
        print("SKIP: TLC not installed (see formal/README.md for Toolbox or Docker)")
        return 0

    failures = 0
    for tla, cfg in MODELS:
        tla_path = TLA_DIR / tla
        cfg_path = TLA_DIR / cfg
        if not tla_path.exists() or not cfg_path.exists():
            print(f"MISSING: {tla}")
            failures += 1
            continue
        print(f"TLC {tla} ...")
        result = subprocess.run(
            [*cmd, "-config", str(cfg_path), str(tla_path)],
            cwd=TLA_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures += 1
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        else:
            print("  OK")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
