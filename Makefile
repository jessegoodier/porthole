# Kubernetes Service Proxy - Makefile

# Configuration
IMAGE_NAME = jgoodier/porthole
IMAGE_TAG = 0.2.18
NAMESPACE = porthole

# Docker image names (dynamically read IMAGE_TAG)
REGISTRY = docker.io
GET_VERSION = $(shell grep '^IMAGE_TAG' Makefile | cut -d' ' -f3)
FULL_NAME_AMD64 = $(REGISTRY)/$(IMAGE_NAME):$(GET_VERSION)-amd64
FULL_NAME_ARM64 = $(REGISTRY)/$(IMAGE_NAME):$(GET_VERSION)-arm64
MANIFEST_NAME = $(REGISTRY)/$(IMAGE_NAME):$(GET_VERSION)
FULL_NAME_MULTI = $(REGISTRY)/$(IMAGE_NAME):$(GET_VERSION)
LATEST_NAME = $(REGISTRY)/$(IMAGE_NAME):latest


# Default target
.PHONY: help
help: ## Show this help message
	@echo "Kubernetes Service Proxy - Available Commands:"
	@echo "=============================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development
.PHONY: install
install: ## Install dependencies
	uv sync

.PHONY: format
format: ## Format code
	uv run task format

.PHONY: lint
lint: ## Lint code
	uv run task lint

.PHONY: type
type: ## Type check code
	uv run task type

.PHONY: test
test: ## Run tests
	uv run task tests

.PHONY: dev
dev: ## Generate portal files for development
	uv run python -m porthole.porthole generate

##@ Docker
.PHONY: build
build: ## Build Docker image
	podman build --arch amd64 -f Dockerfile -t "$(FULL_NAME_AMD64)" .
	podman build --arch arm64 -f Dockerfile -t "$(FULL_NAME_ARM64)" .

.PHONY: push
push: ## Push Docker image
	podman push "$(FULL_NAME_AMD64)"
	podman push "$(FULL_NAME_ARM64)"

	echo "📦 Creating manifest list..."
	podman manifest create "$(MANIFEST_NAME)"
	echo "➕ Adding images to manifest..."
	podman manifest add "$(MANIFEST_NAME)" "$(FULL_NAME_AMD64)"
	podman manifest add "$(MANIFEST_NAME)" "$(FULL_NAME_ARM64)"

	# --- TAG AND PUSH MANIFEST ---
	echo "🏷️ Tagging manifest as $(FULL_NAME_MULTI)..."
	podman tag "$(MANIFEST_NAME)" "$(FULL_NAME_MULTI)"
	echo "📤 Pushing multi-arch image to $(REGISTRY)..."
	podman manifest push --all "$(FULL_NAME_MULTI)"

	echo "🏷️  Tagging manifest as latest..."
	podman tag "$(MANIFEST_NAME)" "$(LATEST_NAME)"
	echo "📤 Pushing latest multi-arch image to $(REGISTRY)..."
	podman manifest push --all "$(LATEST_NAME)"

	echo "✅ Done! Multi-arch image pushed to: $(FULL_NAME_MULTI) and $(LATEST_NAME)"

.PHONY: run-docker

.PHONY: build-app-only
build-app-only: ## Build Docker image
	podman build --arch amd64 -f Dockerfile-app-only -t "$(FULL_NAME_AMD64)" .
	podman build --arch arm64 -f Dockerfile-app-only -t "$(FULL_NAME_ARM64)" .

.PHONY: push-app-only
push-app-only: ## Push Docker image
	podman push "$(FULL_NAME_AMD64)"
	podman push "$(FULL_NAME_ARM64)"

	echo "📦 Creating manifest list..."
	podman manifest create "$(MANIFEST_NAME)"
	echo "➕ Adding images to manifest..."
	podman manifest add "$(MANIFEST_NAME)" "$(FULL_NAME_AMD64)"
	podman manifest add "$(MANIFEST_NAME)" "$(FULL_NAME_ARM64)"

	# --- TAG AND PUSH MANIFEST ---
	echo "🏷️ Tagging manifest as $(FULL_NAME_MULTI)..."
	podman tag "$(MANIFEST_NAME)" "$(FULL_NAME_MULTI)"
	echo "📤 Pushing multi-arch image to $(REGISTRY)..."
	podman manifest push --all "$(FULL_NAME_MULTI)"

	echo "🏷️  Tagging manifest as latest..."
	podman tag "$(MANIFEST_NAME)" "$(LATEST_NAME)"
	echo "📤 Pushing latest multi-arch image to $(REGISTRY)..."
	podman manifest push --all "$(LATEST_NAME)"

	echo "✅ Done! Multi-arch image pushed to: $(FULL_NAME_MULTI) and $(LATEST_NAME)"

.PHONY: run-docker
run-docker: ## Run Docker container locally (note: no web server - generates files only)
	docker run --rm -it $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: debug
debug: ## Enable debug mode
	kubectl -n $(NAMESPACE) set env deployment/porthole DEBUG=true

##@ Utilities
.PHONY: clean
clean: ## Clean up generated files
	rm -rf output/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: discover
discover: ## Discover services (table format)
	uv run task run discover --format table

.PHONY: generate
generate: ## Generate portal and configs
	uv run task run generate

.PHONY: info
info: ## Show cluster info
	uv run task run info

##@ CI/CD
.PHONY: ci
ci: install # format lint type test ## Run all CI checks

.PHONY: bump-patch
bump-patch: ## Bump patch version (0.1.7 -> 0.1.8)
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag patch

.PHONY: bump-minor
bump-minor: ## Bump minor version (0.1.7 -> 0.2.0)
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag minor

.PHONY: bump-major
bump-major: ## Bump major version (0.1.7 -> 1.0.0)
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag major

.PHONY: bump-dry-run
bump-dry-run: ## Test version bump without making changes
	uv run bump-my-version bump --allow-dirty --no-commit --no-tag --dry-run patch

.PHONY: show-version
show-version: ## Show current version that will be used for building
	@echo "Current IMAGE_TAG: $(IMAGE_TAG)"
	@echo "Dynamic GET_VERSION: $(GET_VERSION)"
	@echo "Will build: $(FULL_NAME_AMD64)"

.PHONY: build-push
build-push: bump-patch build push ## Bump version, build and push Docker image

.PHONY: build-push-only-app-changes
build-push-only-app-changes: bump-patch build-app-only push-app-only ## Bump version, build only app changes and push

.PHONY: build-push-dry-run
build-push-dry-run: ## Test the complete build-push workflow without actually executing
	@echo "Would run: make bump-patch"
	@echo "Current version: $(GET_VERSION)"
	@uv run bump-my-version bump --allow-dirty --no-commit --no-tag --dry-run patch | head -5
	@echo ""
	@echo "Would run: make build"
	@make build --dry-run
	@echo ""
	@echo "Would run: make push" 
	@make push --dry-run

.PHONY: full-deploy
full-deploy: ci build-push deploy ## Full deployment pipeline