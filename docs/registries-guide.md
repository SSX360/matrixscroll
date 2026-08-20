# MCP Registries Submission Guide

This guide details how to submit the `matrixscroll-mcp` server to all major MCP discovery surfaces to establish credibility and visibility.

---

## 1. Glama Registry
- **Status:** live, quality **A** on [matrixscroll Glama listing](https://glama.ai/mcp/servers/SSX360/matrixscroll) (license A, maintenance A, TDQS tool-set A as of 2026-06-29).
- **Listing:** [matrixscroll on Glama](https://glama.ai/mcp/servers/SSX360/matrixscroll)
- **TDQS checklist (quality A):**
  1. Every `@mcp.tool()` declares MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).
  2. Tool docstrings include **when to use**, **when not to use**, sibling alternatives, side effects, and return shape.
  3. Pydantic `Field(description=...)` on every parameter (Glama introspection reads `tools/list` JSON Schema).
  4. CI guard: `tests/test_mcp_server.py::MCPToolDefinitionTests` asserts â‰¥80% schema description coverage.
- **How to publish / re-sync:**
  1. **Publish to PyPI first**, then bump `glama.json` `packages[].version` (Glama installs the PyPI pin, and a pin ahead of PyPI fails the build, as in commit `453a3ef`).
  2. CI guards: `scripts/validate_glama_pypi.py` and `scripts/glama_stdio_smoke.py` (PyPI install + stdio `tools/list`).
  3. Log in to [Glama.ai](https://glama.ai/mcp).
  4. Sync repository `https://github.com/SSX360/matrixscroll` (automatic on push). Use **Sync Server** manually if a failed build predates the PyPI release.
  5. Confirm per-tool TDQS â‰¥ B and server quality **A** on the listing page.

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
