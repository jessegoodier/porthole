# Stage 1: Build the Python application
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.13

WORKDIR /app
COPY . /app/
COPY scripts/kubectl-install-for-debug.sh /app/scripts/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev \
    && chmod +x /app/scripts/*.sh \
    && groupadd --gid 1001 app \
    && useradd --uid 1001 --gid app --shell /bin/bash --create-home app \
    && chown -R app:app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:/python/bin:$PATH"

# Stage 2: Final image with nginx and tools
FROM nginxinc/nginx-unprivileged:alpine

USER root

# Install necessary tools
RUN apk add --no-cache \
    inotify-tools \
    curl \
    jq \
    vim \
    bash \
    python3 \
    py3-pip \
    py3-wheel \
    py3-setuptools \
    && rm -rf /var/cache/apk/*

# Copy Python application from builder stage
COPY --from=builder /python /python
COPY --from=builder /app /app
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Set environment variables  
ENV PYTHONPATH="/app/src"
ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx

# Install Python dependencies using system Python
RUN cd /app && \
    pip3 install --break-system-packages --no-cache-dir -e . && \
    python3 -c "import porthole; print('porthole package installed successfully')"

# Create necessary directories and set permissions
RUN mkdir -p /app/generated-output /app/shared-configs \
    && chown -R app:app /app \
    && chown -R app:app /var/cache/nginx \
    && chown -R app:app /var/log/nginx \
    && chown -R app:app /etc/nginx \
    && bash /app/scripts/kubectl-install-for-debug.sh

# Expose port 7070 for nginx
EXPOSE 7070

# Switch to non-root user
USER app

# Run the smart entrypoint that chooses startup mode
CMD ["/app/scripts/entrypoint.sh"]