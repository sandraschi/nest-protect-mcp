# Multi-stage build for Nest Protect MCP
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Build stage
FROM base as builder

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy source code
WORKDIR /app
COPY src/ ./src/
COPY requirements.txt ./
COPY pyproject.toml ./
COPY .bumpversion.toml ./

# Build the wheel
RUN python -m build --wheel --no-isolation

# Runtime stage
FROM base as runtime

# Install runtime dependencies
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy built wheel and install
COPY --from=builder /app/dist/*.whl ./
RUN pip install --no-cache-dir *.whl

# Create directory for state and config
RUN mkdir -p /app/data /app/config && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import nest_protect_mcp; print('OK')" || exit 1

# Run the MCP server
CMD ["python", "-m", "nest_protect_mcp.server"]
