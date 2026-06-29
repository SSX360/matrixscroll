# MCP Registries Submission Guide

This guide details how to submit the `matrixscroll-mcp` server to all major MCP discovery surfaces to establish credibility and visibility.

---

## 1. Glama Registry
- **Status:** Integrated via `glama.json`.
- **Listing:** [matrixscroll on Glama](https://glama.ai/mcp/servers/SSX360/matrixscroll)
- **Internal only:** Do **not** submit `digital-rain-mcp` (private SSX360 repo intelligence). If it appears on Glama from an old public scrape, delist via the Glama maintainer dashboard and revoke Glama GitHub App access to `SSX360/digital-rain`.
- **TDQS checklist (quality A):**
  1. Every `@mcp.tool()` declares MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).
  2. Tool docstrings include **when to use**, **when not to use**, sibling alternatives, side effects, and return shape.
  3. Pydantic `Field(description=...)` on every parameter (Glama introspection reads `tools/list` JSON Schema).
  4. CI guard: `tests/test_mcp_server.py::MCPToolDefinitionTests` asserts ≥80% schema description coverage.
- **How to publish / re-sync:**
  1. Log in to [Glama.ai](https://glama.ai/mcp).
  2. Sync repository `https://github.com/SSX360/matrixscroll` (auto on push; manual sync if stale).
  3. Confirm per-tool TDQS ≥ B and server quality **A** on the listing page.

## 2. Official MCP Registry (Model Context Protocol)
- **Status:** Ready for submission.
- **Repository:** `https://github.com/modelcontextprotocol/servers`
- **Submission steps:**
  1. Fork the official registry repository.
  2. Create a new entry under `src/matrixscroll/` or update the registry JSON files.
  3. Reference our Python launch command: `python -m matrixscroll.mcp`.
  4. Submit a Pull Request.

## 3. Smithery Registry
- **Status:** Integrated via `smithery.yaml`.
- **How to Publish:**
  1. Go to [Smithery.ai](https://smithery.ai/).
  2. Connect your GitHub repository.
  3. Smithery will detect `smithery.yaml` and the `Dockerfile` to automatically publish and host the containerized server.

## 4. Cursor Directory
- **Status:** Ready for submission.
- **Submission steps:**
  1. Go to the [Cursor Directory submission page](https://cursor.sh/mcp or general submission form).
  2. Provide the listing details:
     - **Name:** Matrix Scroll MCP
     - **Command:** `python -m matrixscroll.mcp`
     - **Type:** `stdio`
     - **Env:** `COPILOT_WORKSPACE=${workspaceFolder}`
     - **Description:** "Cryptographic self-attestation and range verification for agent-assisted Git commits."

## 5. PulseMCP
- **Status:** Ready for submission.
- **Submission steps:**
  1. Visit [PulseMCP](https://pulsemcp.com/) and click "Submit a Server".
  2. Enter the repository URL: `https://github.com/SSX360/matrixscroll` and description details.

## 6. mcp.so
- **Status:** Ready for submission.
- **Submission steps:**
  1. Visit [mcp.so](https://mcp.so/) and click "Submit MCP".
  2. Provide the GitHub link and tag it under **Security / Version Control / Developer Tools**.
