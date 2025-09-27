COMPOSE ?= docker compose
SERVICE ?= bot
DB_SERVICE ?= db
ENV_FILE ?= .env

.PHONY: help create-env build start full up down rebuild migrate logs logs-bot shell test lint format ps pull clean

help:
	@echo "Makefile commands:"
	@echo ""
	@echo "  make help                — показать эту помощь (эта страница)"
	@echo "  make create-env          — создать .env из .env.template (если .env отсутствует)"
	@echo "  make build               — собрать образы (без кэша)"
	@echo "  make start               — build + up -d (поднять сервисы)"
	@echo "  make full                — build -> up -d -> migrate -> logs (полный запуск)"
	@echo "  make up                  — поднять контейнеры в фоне (docker compose up -d)"
	@echo "  make down                — остановить контейнеры и удалить тома"
	@echo ""
	@echo "  make migrate [ARGS...]   — управление миграциями (через scripts/migrate.sh):"
	@echo "      make migrate              -> alembic upgrade head"
	@echo "      make migrate down         -> alembic downgrade -1"
	@echo "      make migrate down 2       -> alembic downgrade -2"
	@echo "      make migrate up 3         -> alembic upgrade +3"
	@echo "      make migrate to head-2    -> alembic upgrade head-2"
	@echo ""
	@echo "  make logs                 — смотреть логи всех сервисов (follow)"
	@echo "  make logs-bot             — смотреть логи сервиса bot"
	@echo "  make shell                — открыть shell в контейнере bot"
	@echo "  make test                 — запустить pytest внутри контейнера bot"
	@echo "  make lint                 — ruff check + black --check (локально)"
	@echo "  make format               — ruff --fix + black . (локально)"
	@echo ""
	@echo "Примеры:"
	@echo "  make create-env"
	@echo "  make start"
	@echo "  make migrate down 2"
	@echo "  make migrate to 60f3a1c"
	@echo ""

create-env:
	@if [ -f "$(ENV_FILE)" ]; then \
		echo "$(ENV_FILE) already exists — skipping"; \
	else \
		if [ -f ".env.template" ]; then \
			cp .env.template $(ENV_FILE); \
			echo "Created $(ENV_FILE) from .env.template; please edit BOT_TOKEN etc."; \
		else \
			echo ".env.template not found — create .env manually."; \
			exit 1; \
		fi \
	fi

build:
	@echo "Building images (no-cache)..."
	$(COMPOSE) build --no-cache

start: build up

full: build up
	@echo "Running migrations (make migrate)..."
	@$(MAKE) migrate
	@echo "Following logs..."
	$(COMPOSE) logs -f --tail=200

up:
	@echo "Starting containers..."
	$(COMPOSE) up -d

down:
	@echo "Stopping and removing containers and volumes..."
	$(COMPOSE) down --volumes --remove-orphans

rebuild: down build up

migrate:
	@echo "Invoking migrate script (scripts/migrate.sh) with args: $(filter-out migrate,$(MAKECMDGOALS))"
	ARGS="$(filter-out migrate,$(MAKECMDGOALS))"; ./scripts/migrate.sh $$ARGS

logs:
	$(COMPOSE) logs -f --tail=200

logs-bot:
	$(COMPOSE) logs -f --tail=200 $(SERVICE)

shell:
	$(COMPOSE) exec $(SERVICE) sh

test:
	@echo "Running pytest inside $(SERVICE)..."
	$(COMPOSE) run --rm $(SERVICE) pytest -q

lint:
	@echo "Running ruff + black checks locally..."
	python -m pip install --quiet ruff black || true
	ruff check .
	black --check .

format:
	@echo "Autofix ruff and format with black locally..."
	python -m pip install --quiet ruff black || true
	ruff check . --fix --show-fixes || true
	black .

ps:
	$(COMPOSE) ps

pull:
	$(COMPOSE) pull

clean:
	@echo "Cleaning __pycache__ and .pyc ..."
	find . -type d -name "__pycache__" -print0 | xargs -0 -r rm -rf
	find . -type f -name "*.pyc" -print0 | xargs -0 -r rm -f
	@echo "Done."
