# MCP Registries Submission Guide

This guide details how to submit the `matrixscroll-mcp` server to all major MCP discovery surfaces to establish credibility and visibility.

---

## 1. Glama Registry
- **Status:** Integrated via `glama.json`.
- **How to Publish:** 
  1. Log in to [Glama.ai](https://glama.ai/mcp).
  2. Sync your repository `https://github.com/SSX360/matrixscroll`.
  3. Glama will automatically parse `glama.json` and score the tools (our tight, attestation-focused tool docstrings will secure an **A** grade).

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
