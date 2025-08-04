# Porthole - Makefile

.ONESHELL:

# Configuration
REGISTRY = docker.io
REPO = jgoodier
IMAGE_NAME_APP = porthole
IMAGE_TAG_APP = 0.2.92
IMAGE_NAME_BASE = nginx-python-ubi-base
IMAGE_TAG_BASE = latest
NAMESPACE = porthole
DOCKER_FILE_BASE = docker/Dockerfile.nginx-python-ubi-base
DOCKER_FILE_APP = docker/Dockerfile.app-changes-only

# Docker image names (dynamically read IMAGE_TAG)
FULL_NAME_BASE_AMD64 = $(REGISTRY)/$(REPO)/$(IMAGE_NAME_BASE):latest-amd64
FULL_NAME_BASE_ARM64 = $(REGISTRY)/$(REPO)/$(IMAGE_NAME_BASE):latest-arm64
FULL_NAME_BASE_MULTI = $(REGISTRY)/$(REPO)/$(IMAGE_NAME_BASE):latest
FULL_NAME_APP_AMD64 = $(REGISTRY)/$(REPO)/$(IMAGE_NAME_APP):$(IMAGE_TAG_APP)-amd64
FULL_NAME_APP_ARM64 = $(REGISTRY)/$(REPO)/$(IMAGE_NAME_APP):$(IMAGE_TAG_APP)-arm64
FULL_NAME_APP_MULTI = $(REGISTRY)/$(REPO)/$(IMAGE_NAME_APP):$(IMAGE_TAG_APP)

# Default target
.PHONY: help
help: ## Show this help message
	@echo "Porthole - Available Commands:"
	@echo "=============================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


##@ Docker
.PHONY: build-base
build-base: ## Build base Docker image
	podman build --platform linux/amd64 -f $(DOCKER_FILE_BASE) -t "$(FULL_NAME_BASE_AMD64)" .
	podman build --platform linux/arm64 -f $(DOCKER_FILE_BASE) -t "$(FULL_NAME_BASE_ARM64)" .

.PHONY: push-base
push-base: build-base ## Push base Docker image
	podman push "$(FULL_NAME_BASE_AMD64)"
	podman push "$(FULL_NAME_BASE_ARM64)"

	echo "📦 Creating manifest list..."
	podman manifest rm "$(FULL_NAME_BASE_MULTI)" || true
	podman manifest create "$(FULL_NAME_BASE_MULTI)"
	echo "➕ Adding images to manifest..."
	podman manifest add "$(FULL_NAME_BASE_MULTI)" --arch amd64 "$(FULL_NAME_BASE_AMD64)"
	podman manifest add "$(FULL_NAME_BASE_MULTI)" --arch arm64 "$(FULL_NAME_BASE_ARM64)"

	echo "🔍 Inspecting manifest..."
	podman manifest inspect "$(FULL_NAME_BASE_MULTI)"

	echo "📤 Pushing multi-arch image to $(REGISTRY)..."
	podman manifest push --all "$(FULL_NAME_BASE_MULTI)"

	echo "✅ Done! Multi-arch image pushed to: $(FULL_NAME_BASE_MULTI)"

.PHONY: build-app
build-app: ## Build Docker image
	podman build --platform linux/amd64 -f $(DOCKER_FILE_APP) -t "$(FULL_NAME_APP_AMD64)" .
	podman build --platform linux/arm64 -f $(DOCKER_FILE_APP) -t "$(FULL_NAME_APP_ARM64)" .

.PHONY: push-app
push-app: build-app ## Push Docker image
	podman push "$(FULL_NAME_APP_AMD64)"
	podman push "$(FULL_NAME_APP_ARM64)"

	echo "📦 Creating manifest list..."
	podman manifest rm "$(FULL_NAME_APP_MULTI)" || true
	podman manifest create "$(FULL_NAME_APP_MULTI)"
	echo "➕ Adding images to manifest..."
	podman manifest add "$(FULL_NAME_APP_MULTI)" --arch amd64 "$(FULL_NAME_APP_AMD64)"
	podman manifest add "$(FULL_NAME_APP_MULTI)" --arch arm64 "$(FULL_NAME_APP_ARM64)"

	echo "🔍 Inspecting manifest..."
	podman manifest inspect "$(FULL_NAME_APP_MULTI)"

	echo "📤 Pushing multi-arch image to $(REGISTRY)..."
	podman manifest push --all "$(FULL_NAME_APP_MULTI)"

	echo "✅ Done! Multi-arch image pushed to: $(FULL_NAME_APP_MULTI)"

##@ Utilities
.PHONY: podman-prune
podman-prune: ## Prune podman
	podman system prune --force

.PHONY: clean
clean: podman-prune ## Clean up generated files
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

.PHONY: bump-patch
bump-patch: ## Bump patch version (0.1.7 -> 0.1.8)
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag patch
	uv sync

.PHONY: bump-minor
bump-minor: ## Bump minor version (0.1.7 -> 0.2.0)
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag minor
	uv sync

.PHONY: bump-major
bump-major: ## Bump major version (0.1.7 -> 1.0.0)
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag major
	uv sync
.PHONY: bump-dry-run
bump-dry-run: ## Test version bump without making changes
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag --dry-run patch

.PHONY: build-base-push
build-base-push: bump-dry-run bump-patch build-base push-base ## Build and push base Docker image

.PHONY: build-app-push
build-app-push: bump-dry-run bump-patch build-app push-app ## Build and push app Docker image

