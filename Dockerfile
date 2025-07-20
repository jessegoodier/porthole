# Stage 1 -----------------------------------------------------------

# Build the application in the `/app` directory
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.13

WORKDIR /app
COPY . ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev \
    && apt-get update && apt-get install -y curl

# Stage 2 -----------------------------------------------------------

# Use a final image without uv
FROM debian:bookworm-slim

# Create non-root user
RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid app --shell /bin/bash --create-home app

# Copy the Python version
COPY --from=builder --chown=app:app ./python /python

# Copy the application from the builder
COPY --from=builder --chown=app:app ./app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:/python/bin:$PATH"

# Create output directory and make scripts executable
RUN mkdir -p /app/output && chown app:app /app/output && \
    chmod +x /app/scripts/*.sh

# Set working directory
WORKDIR /app

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:6060', timeout=5)" || exit 1

# Expose port
EXPOSE 6060

# Run the smart entrypoint that chooses startup mode
CMD ["/app/scripts/entrypoint.sh"]