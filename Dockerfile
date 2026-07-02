# Dockerfile for Glama.ai MCP compliance checks
FROM python:3.11-slim-bookworm

# Install UV for fast pip installations
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Git is required for provenance MCP tools (create_envelope, verify_pr_range, etc.).
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the codebase
COPY . /app

# Install the package locally with MCP extra dependencies
RUN uv pip install --system .[mcp]

# Command to launch the Matrix Scroll MCP stdio server
ENTRYPOINT ["python", "-m", "matrixscroll.mcp"]
