#!/usr/bin/env bash
# Matrix Scroll Agent Self-Attestation Loop Demo
# 
# Demonstrates:
#   1. Agent writes code
#   2. Calls the Matrix Scroll MCP tool to generate & sign a commit envelope
#   3. Commit is created in git
#   4. Scroll Gate verifies the PR range offline
#   5. Verification succeeds via Ed25519
#
set -euo pipefail

# Set up demo directory
DEMO_DIR="$(mktemp -d)/matrixscroll-hero-demo"
mkdir -p "$DEMO_DIR"
trap 'rm -rf "$DEMO_DIR"' EXIT

echo "================================================================"
echo "  Matrix Scroll Hero Demo: Agent Self-Attestation Loop"
echo "================================================================"
echo ""

# Initialize git repository
cd "$DEMO_DIR"
git init -q
git config user.email "agent@matrixscroll.com"
git config user.name "Agent Attester"
echo "Initial codebase" > app.py
git add app.py
git commit -m "initial commit" -q
BASE_SHA="$(git rev-parse HEAD)"
echo "[-] Initial commit created: $BASE_SHA"

# 1. Agent writes/modifies code
echo "[1] Agent is editing code..."
echo 'def add(a, b): return a + b' > app.py
git add app.py
echo "    -> Staged changes in app.py"

# 2. Call Matrix Scroll MCP tool to create a signed envelope (actor=agent)
echo "[2] Calling Matrix Scroll MCP tool (create_envelope)..."
# We invoke it via python CLI representation of the create_envelope tool:
python -c "
from matrixscroll.mcp import create_envelope
import json
res = create_envelope('.', actor='agent', tool='matrixscroll-mcp', scope='issue-123', message='feat: implement addition function')
print(json.dumps(res, indent=2))
" > envelope_creation.json

# Extract path and preview the envelope
ENV_PATH="$(python -c "import json; print(json.load(open('envelope_creation.json'))['path'])")"
echo "    -> Signed envelope created at: $ENV_PATH"
echo "    -> Envelope signature metadata:"
python -c "
import json
env = json.load(open('envelope_creation.json'))['envelope']
print(f'       - Actor Type: {env[\"provenance\"][\"actor_type\"]}')
print(f'       - Tool:       {env[\"provenance\"][\"tool\"]}')
print(f'       - Scope:      {env[\"provenance\"][\"agent_scope\"]}')
print(f'       - Algorithm:  {env[\"signature\"][\"algorithm\"]}')
print(f'       - Public Key: {env[\"signature\"][\"public_key\"][:16]}...')
"

# 3. Create the commit in git
echo "[3] Creating the git commit..."
git commit -m "feat: implement addition function" -q
HEAD_SHA="$(git rev-parse HEAD)"
echo "    -> Commit created: $HEAD_SHA"

# Update envelope with actual commit ID to finalize
python -c "
import json, shutil
from pathlib import Path
from matrixscroll.git import sign_commit_envelope, save_envelope
res = json.load(open('envelope_creation.json'))
envelope = res['envelope']
envelope['commit']['actual_id'] = '$HEAD_SHA'
signed = sign_commit_envelope(envelope)
save_envelope(signed, Path('.'))
"
echo "    -> Finalized and bound envelope to SHA $HEAD_SHA"

# 4. Scroll Gate verifies the PR range
echo "[4] Scroll Gate verifying PR range ($BASE_SHA..$HEAD_SHA)..."
python -c "
from matrixscroll.mcp import verify_pr_range
import json
res = verify_pr_range('.', '$BASE_SHA', '$HEAD_SHA')
print(json.dumps(res, indent=2))
" > verification_result.json

# Check result
OK="$(python -c "import json; print(json.load(open('verification_result.json'))['ok'])")"
VERIFIED_COUNT="$(python -c "import json; print(json.load(open('verification_result.json'))['verified_count'])")"
AGENT_COUNT="$(python -c "import json; print(json.load(open('verification_result.json'))['agent_count'])")"

echo "    -> Range verification: $OK"
echo "    -> Verified Commits:  $VERIFIED_COUNT"
echo "    -> Agent Commits:     $AGENT_COUNT"

if [ "$OK" = "True" ]; then
  echo ""
  echo "================================================================"
  echo "  SUCCESS: Self-attestation verified offline!"
  echo "================================================================"
else
  echo ""
  echo "  FAILURE: Self-attestation verification failed."
  exit 1
fi
