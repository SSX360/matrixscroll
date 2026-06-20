#!/usr/bin/env bash
# Agent provenance demo — run from matrixscroll repo root after pip install -e .
set -euo pipefail

export MATRIXSCROLL_ACTOR_TYPE=agent
export MATRIXSCROLL_TOOL=cursor
export MATRIXSCROLL_HOME="${MATRIXSCROLL_HOME:-$(mktemp -d)/matrixscroll-demo}"

DEMO_TMPDIR="$(mktemp -d)"
trap 'rm -rf "$DEMO_TMPDIR"' EXIT

echo "== Matrix Scroll agent commit demo =="
matrixscroll hook-status 2>/dev/null || true

cd "$DEMO_TMPDIR"
git init -q
git config user.email "agent-demo@matrixscroll.com"
git config user.name "Matrix Scroll Demo"

python -c "from matrixscroll.git import install_hooks; print(install_hooks())"
echo "agent change" > hello.txt
git add hello.txt
git commit -m "feat: agent-assisted change"

SHA="$(git rev-parse HEAD)"
echo "commit: $SHA"

matrixscroll envelope-verify "$SHA"
echo "verify passed"

ENV_PATH=".git/matrixscroll/envelopes/${SHA}.json"
python -c "
import json, sys
from pathlib import Path
p = Path('$ENV_PATH')
data = json.loads(p.read_text())
data['provenance']['tool'] = 'tampered'
p.write_text(json.dumps(data, indent=2))
"

if matrixscroll envelope-verify "$SHA"; then
  echo "expected tamper verify to fail" >&2
  exit 1
fi
echo "tamper correctly rejected"
echo "demo complete"
