DOCKER := $(shell \
	if command -v docker-compose >/dev/null 2>&1; then \
		echo docker-compose; \
	elif docker compose version >/dev/null 2>&1; then \
		echo "docker compose"; \
	else \
		echo "ERROR: docker compose not found" >&2; exit 1; \
	fi \
)

# ==========================================
# Development
# ==========================================

.PHONY: run dev install install-dev

run:
	$(DOCKER) -f infra/database.yml up -d db
	uv run -- flask --app app run --debug

dev: run  # Alias for run

install:
	uv sync

install-dev:
	uv sync --extra dev
	uv run pre-commit install

# ==========================================
# Database
# ==========================================

.PHONY: db-up db-down db-reset db-shell initdb seed migrate migrate-create

db-up:
	$(DOCKER) -f infra/database.yml up -d db

db-down:
	$(DOCKER) -f infra/database.yml down

db-reset:
	$(DOCKER) -f infra/database.yml down --volumes
	$(DOCKER) -f infra/database.yml rm -f
	$(DOCKER) -f infra/database.yml up -d db
	sleep 5
	uv run -- flask --app app init-db

db-shell:
	psql -h localhost -p 5432 -U buska_user -d buska_db

initdb:
	$(DOCKER) -f infra/database.yml up -d db
	sleep 5
	uv run -- flask --app app init-db

seed:
	uv run python seed.py

# Alembic migrations
migrate:
	uv run alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

migrate-history:
	uv run alembic history

migrate-downgrade:
	uv run alembic downgrade -1

# ==========================================
# Code Quality
# ==========================================

.PHONY: lint format typecheck check

lint:
	uv run ruff check app/

format:
	uv run black app/ tests/
	uv run ruff check --fix app/

typecheck:
	uv run mypy app/

check: lint typecheck  # Run all checks

# ==========================================
# Testing
# ==========================================

.PHONY: test test-cov test-unit test-integration

test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=term-missing

test-unit:
	uv run pytest tests/unit/

test-integration:
	uv run pytest tests/integration/

# ==========================================
# Cleanup
# ==========================================

.PHONY: clean

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# ==========================================
# Help
# ==========================================

.PHONY: help

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  run / dev       Start the development server"
	@echo "  install         Install production dependencies"
	@echo "  install-dev     Install dev dependencies + pre-commit hooks"
	@echo ""
	@echo "Database:"
	@echo "  db-up           Start database container"
	@echo "  db-down         Stop database container"
	@echo "  db-reset        Reset database (delete + recreate)"
	@echo "  db-shell        Connect to database via psql"
	@echo "  initdb          Initialize database with populate.sql"
	@echo "  seed            Run seed.py script"
	@echo "  migrate         Run pending migrations"
	@echo "  migrate-create  Create a new migration"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint            Run ruff linter"
	@echo "  format          Format code with black + ruff"
	@echo "  typecheck       Run mypy type checker"
	@echo "  check           Run all checks (lint + typecheck)"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run all tests"
	@echo "  test-cov        Run tests with coverage report"
	@echo "  test-unit       Run unit tests only"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean           Remove cache files"