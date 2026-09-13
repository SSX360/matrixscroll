# MCP Registries Submission Guide

This guide details how to submit the `matrixscroll-mcp` server to all major MCP discovery surfaces to establish credibility and visibility.

---

## 1. Glama Registry
- **Status:** live listing at [matrixscroll on Glama](https://glama.ai/mcp/servers/SSX360/matrixscroll). After August 2026 tombstone work, **re-sync manually** if the page shows stale description, wrong tools, or old `matrixscroll.com/docs` links.
- **Source of truth:** [`glama.json`](../glama.json) in this repository (`documentation` → GitHub docs, `homepage` → matrixscroll.com tombstone).
- **TDQS checklist (quality A):**
  1. Every `@mcp.tool()` declares MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).
  2. Tool docstrings include **when to use**, **when not to use**, sibling alternatives, side effects, and return shape.
  3. Pydantic `Field(description=...)` on every parameter (Glama introspection reads `tools/list` JSON Schema).
  4. CI guard: `tests/test_mcp_server.py::MCPToolDefinitionTests` asserts >=80% schema description coverage.
- **How to publish / re-sync:**
  1. **Publish to PyPI first**, then bump `glama.json` `packages[].version` (Glama installs the PyPI pin, and a pin ahead of PyPI fails the build, as in commit `453a3ef`).
  2. CI guards: `scripts/validate_glama_pypi.py` and `scripts/glama_stdio_smoke.py` (PyPI install + stdio `tools/list`).
  3. Log in to [Glama.ai](https://glama.ai/mcp).
  4. Open [SSX360/matrixscroll](https://glama.ai/mcp/servers/SSX360/matrixscroll) and click **Sync Server** so Glama reinstalls from PyPI and re-reads `glama.json` from GitHub.
  5. Confirm the listing shows the **14 Matrix Scroll MCP tools** (`create_envelope`, `verify_envelope`, `scan_mcp_server`, etc.), not unrelated workspace-scaffolding tools.
  6. Confirm per-tool TDQS is at least B and server quality on the listing page.

## 2. Official MCP Registry (Model Context Protocol)
- **Status:** ready for submission.
- **Repository:** `https://github.com/modelcontextprotocol/servers`
- **Submission steps:**
  1. Fork the official registry repository.
  2. Create a new entry under `src/matrixscroll/` or update the registry JSON files.
  3. Reference our Python launch command: `python -m matrixscroll.mcp`.
  4. Submit a Pull Request.

## 3. Smithery Registry
- **Status:** integrated via `smithery.yaml`.
- **How to Publish:**
  1. Go to [Smithery.ai](https://smithery.ai/).
  2. Connect your GitHub repository.
  3. Smithery will detect `smithery.yaml` and the `Dockerfile` to automatically publish and host the containerized server.

## 4. Cursor Directory
- **Status:** ready for submission.
- **Submission steps:**
  1. Open the Cursor Directory submission form. Confirm the current URL first: the
     `cursor.sh/mcp` address this guide used to name now returns 404.
  2. Provide the listing details:
     - **Name:** Matrix Scroll MCP
     - **Command:** `python -m matrixscroll.mcp`
     - **Type:** `stdio`
     - **Env:** `COPILOT_WORKSPACE=${workspaceFolder}`
     - **Description:** "Signed machine-action records and offline Git range verification."

## 5. PulseMCP
- **Status:** ready for submission.
- **Submission steps:**
  1. Visit [PulseMCP](https://pulsemcp.com/) and click **Submit a Server**.
  2. Enter the repository URL: `https://github.com/SSX360/matrixscroll` and description details.

## 6. mcp.so
- **Status:** ready for submission.
- **Submission steps:**
  1. Visit [mcp.so](https://mcp.so/) and click **Submit MCP**.
  2. Provide the GitHub link and tag it under **Security / Version Control / Developer Tools**.
