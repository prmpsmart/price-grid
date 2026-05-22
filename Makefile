.PHONY: help build up down restart logs shell \
	test-up test test-unit test-integration test-file coverage coverage-html \
	migrate migrate-create migrate-down migrate-history migrate-current \
	db-shell redis-shell \
	lint lint-fix format format-check typecheck \
	install add add-dev remove \
	dev reset seed clean clean-all

# ── Config ────────────────────────────────────────────────────────────────────
API_SERVICE = pricegrid-api
DB_SERVICE = pricegrid-db
CACHE_SERVICE = pricegrid-cache
COMPOSE = docker-compose
COMPOSE_TEST = $(COMPOSE) --profile test
EXEC = $(COMPOSE) exec $(API_SERVICE)

# ── Help ──────────────────────────────────────────────────────────────────────
help: ## Show this help message
	@echo ""
	@echo "  PriceGrid — available commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Docker ────────────────────────────────────────────────────────────────────
build: ## Build all Docker images
	$(COMPOSE) build

up: ## Start all services (detached)
	$(COMPOSE) up -d

up-logs: ## Start all services and follow logs
	$(COMPOSE) up

down: ## Stop all services
	$(COMPOSE) down

down-v: ## Stop all services and remove volumes (wipes database)
	$(COMPOSE) down -v

restart: ## Restart the API service only
	$(COMPOSE) restart $(API_SERVICE)

restart-all: ## Restart all services
	$(COMPOSE) restart

logs: ## Follow API logs
	$(COMPOSE) logs -f $(API_SERVICE)

logs-all: ## Follow logs from all services
	$(COMPOSE) logs -f

ps: ## Show running containers
	$(COMPOSE) ps

# ── Shell Access ──────────────────────────────────────────────────────────────
shell: ## Open a bash shell inside the API container
	$(EXEC) bash

db-shell: ## Open a psql shell inside the database container
	$(COMPOSE) exec $(DB_SERVICE) psql -U pricegrid -d pricegrid

redis-shell: ## Open a redis-cli shell inside the Redis container
	$(COMPOSE) exec $(CACHE_SERVICE) redis-cli

# ── Migrations ────────────────────────────────────────────────────────────────
migrate: ## Apply all pending migrations
	$(EXEC) alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="your message")
	$(EXEC) alembic revision --autogenerate -m "$(msg)"

migrate-down: ## Roll back the last migration
	$(EXEC) alembic downgrade -1

migrate-history: ## Show migration history
	$(EXEC) alembic history --verbose

migrate-current: ## Show current migration revision
	$(EXEC) alembic current

# ── Testing ───────────────────────────────────────────────────────────────────
test-up: ## Start all services including the ephemeral test database
	$(COMPOSE_TEST) up -d

test: test-up ## Run all tests (spins up test DB automatically)
	$(EXEC) pytest -vs

test-unit: ## Run unit tests only (no test database needed)
	$(EXEC) pytest tests/unit -vs

test-integration: test-up ## Run integration tests (spins up test DB automatically)
	$(EXEC) pytest tests/integration -vs

test-file: ## Run a specific test file (usage: make test-file f=tests/unit/test_price_service.py)
	$(EXEC) pytest $(f) -vs

coverage: test-up ## Run all tests with coverage report (spins up test DB automatically)
	$(EXEC) pytest --cov=app --cov-report=term-missing --cov-report=html

coverage-html: ## Open HTML coverage report (macOS)
	open htmlcov/index.html

# ── Code Quality ──────────────────────────────────────────────────────────────
lint: ## Run ruff linter
	$(EXEC) ruff check app tests

lint-fix: ## Run ruff linter, sort imports, and auto-fix issues
	$(EXEC) ruff check app tests --fix
	$(EXEC) ruff check app tests --select I --fix

format: ## Format code and organize imports with ruff
	$(EXEC) ruff format app tests
	$(EXEC) ruff check app tests --select I --fix

format-check: ## Check formatting without applying changes
	$(EXEC) ruff format app tests --check
	$(EXEC) ruff check app tests --select I --check

typecheck: ## Run pyright type checker (configured in pyproject.toml)
	$(EXEC) pyright

# ── Dependencies (local only — updates pyproject.toml + uv.lock, then rebuild) ─
# These are the only commands that run on your host machine, not in Docker.
# Workflow: make add pkg=X  →  make build  →  make up
install: ## [LOCAL] Sync local .venv for IDE support
	uv sync

add: ## [LOCAL] Add a runtime dep and update lockfile (usage: make add pkg=fastapi)
	uv add $(pkg)

add-dev: ## [LOCAL] Add a dev-only dep and update lockfile (usage: make add-dev pkg=pytest)
	uv add --dev $(pkg)

remove: ## [LOCAL] Remove a dep and update lockfile (usage: make remove pkg=somepackage)
	uv remove $(pkg)

# ── Dev Shortcuts ─────────────────────────────────────────────────────────────
dev: ## Start services, run migrations, follow API logs
	$(COMPOSE) up -d $(DB_SERVICE) $(CACHE_SERVICE)
	@echo "Waiting for services to be healthy..."
	@sleep 3
	$(COMPOSE) up -d $(API_SERVICE)
	$(COMPOSE) run --rm pricegrid-migrate
	$(COMPOSE) logs -f $(API_SERVICE)

reset: ## Full reset — wipe volumes, rebuild images, start fresh
	$(COMPOSE) down -v
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

seed: ## Run database seed script (if exists)
	$(EXEC) python scripts/seed.py

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: ## Remove Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
	find . -type f -name "*.pyc" -delete 2>/dev/null; \
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null; \
	find . -type f -name ".coverage" -delete 2>/dev/null; \
	echo "Cleaned."

clean-all: down-v clean ## Stop services, wipe volumes, remove cache files

# ── Database Reset ────────────────────────────────────────────────────────────
db-reset-migrations: ## Rollback migrations to base and upgrade back to head
	$(EXEC) alembic downgrade base
	$(EXEC) alembic upgrade head

db-wipe-volume: ## Completely destroy the database containers, volumes, and rebuild fresh
	docker-compose down -v
	docker-compose up -d --build
	@echo "Waiting for DB to start up cleanly..."
	sleep 3
	$(MAKE) migrate

db-clear-data: ## Truncate all table rows instantly while keeping schema structures
	docker-compose exec pricegrid-db psql -U pricegrid -d pricegrid -c \
	"TRUNCATE TABLE good, market, pricerecord, user, vendor CASCADE;"

db-fresh-reset: ## Clear out everything (schemas, data, tables) but keep the physical volume
	docker-compose exec pricegrid-db psql -U pricegrid -d pricegrid -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	@echo "Database completely emptied. Re-running migrations..."
	$(MAKE) migrate-create
	$(MAKE) migrate