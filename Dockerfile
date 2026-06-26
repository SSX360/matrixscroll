# Dockerfile for Glama.ai MCP compliance checks
FROM python:3.11-slim-bookworm

# Install UV for fast pip installations
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the codebase
COPY . /app

# Install the package locally
RUN uv pip install --system .

# Command to launch the Matrix Scroll MCP stdio server
ENTRYPOINT ["python", "-m", "matrixscroll.mcp"]
