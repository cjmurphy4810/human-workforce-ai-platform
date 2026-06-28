.PHONY: help setup setup-dev dev test test-unit test-integration lint format \
        type-check clean docker-build docker-up docker-down docker-logs \
        db-migrate db-upgrade db-downgrade \
        dashboard-install dashboard-dev dashboard-build

PYTHON     := python3.12
VENV       := .venv
VENV_BIN   := $(VENV)/bin
VENV_PY    := $(VENV_BIN)/python
VENV_PIP   := $(VENV_BIN)/pip

# ── Help ──────────────────────────────────────────────────────────────────────
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ── Python Environment ────────────────────────────────────────────────────────
$(VENV_BIN)/activate:
	$(PYTHON) -m venv $(VENV)

setup: $(VENV_BIN)/activate ## Install production dependencies
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e .

setup-dev: $(VENV_BIN)/activate ## Install all dependencies including dev tools
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e ".[dev]"
	$(VENV_PY) -m pre_commit install

# ── Development Servers ───────────────────────────────────────────────────────
dev: ## Start Human Workforce AI API with hot-reload (port 8000)
	$(VENV_BIN)/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

api: dev ## Alias for dev

research: ## Run Agent 1 research pipeline once
	cd agent1-research && $(VENV_PY) main.py

# ── Testing ───────────────────────────────────────────────────────────────────
test: ## Run full test suite with coverage
	$(VENV_BIN)/pytest

test-unit: ## Run unit tests only
	$(VENV_BIN)/pytest tests/unit/ -v

test-integration: ## Run integration tests only
	$(VENV_BIN)/pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	$(VENV_BIN)/pytest tests/e2e/ -v

# ── Code Quality ──────────────────────────────────────────────────────────────
lint: ## Run ruff linter
	$(VENV_BIN)/ruff check .

format: ## Auto-format code with ruff
	$(VENV_BIN)/ruff format .

type-check: ## Run mypy type checker
	$(VENV_BIN)/mypy .

check: lint type-check ## Run all static analysis checks

# ── Database ──────────────────────────────────────────────────────────────────
db-migrate: ## Generate a new migration (usage: make db-migrate message="add users table")
	$(VENV_BIN)/alembic revision --autogenerate -m "$(message)"

db-upgrade: ## Apply all pending migrations
	$(VENV_BIN)/alembic upgrade head

db-downgrade: ## Roll back one migration
	$(VENV_BIN)/alembic downgrade -1

db-history: ## Show migration history
	$(VENV_BIN)/alembic history --verbose

# ── Docker ────────────────────────────────────────────────────────────────────
docker-build: ## Build Docker image
	docker build -t human-workforce-ai-platform:latest .

docker-up: ## Start all services via Docker Compose
	docker compose up -d

docker-down: ## Stop and remove all Docker Compose containers
	docker compose down

docker-logs: ## Tail Docker Compose logs
	docker compose logs -f

docker-clean: ## Remove containers, volumes, and images
	docker compose down -v --rmi local

# ── Dashboard ─────────────────────────────────────────────────────────────────
dashboard-install: ## Install dashboard npm dependencies
	cd dashboard && npm install

dashboard-dev: ## Start dashboard Vite dev server
	cd dashboard && npm run dev

dashboard-build: ## Build dashboard for production
	cd dashboard && npm run build

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: ## Remove all build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov"      -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f .coverage coverage.xml
