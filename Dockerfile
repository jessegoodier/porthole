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
COPY . /app
COPY scripts/kubectl-install-for-debug.sh /
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev \
    && apt-get update && apt-get install -y curl jq vim \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /app/scripts/*.sh \
    && groupadd --gid 1001 app \
    && useradd --uid 1001 --gid app --shell /bin/bash --create-home app \
    && chown -R app:app /app

# if debug, install kubectl
RUN bash /kubectl-install-for-debug.sh

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:/python/bin:$PATH"

# No port exposure needed - nginx handles web serving

# Run the smart entrypoint that chooses startup mode
CMD ["/app/scripts/entrypoint.sh"]