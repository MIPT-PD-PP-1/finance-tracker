.PHONY: db-up db-down install setup migrate run clean test test-db test-wait

db-up:
	docker compose up -d db

db-down:
	docker compose down db

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

setup:
	@if [ ! -f .env.local ]; then \
		cp .env .env.local; \
		sed -i 's/@db:/@localhost:/g' .env.local; \
		sed -i 's/$${POSTGRES_USER}/your_user/g' .env.local; \
		sed -i 's/$${POSTGRES_PASSWORD}/your_password/g' .env.local; \
		sed -i '/^#/d' .env.local; \
		sed -i '/^$$/d' .env.local; \
	fi

migrate:
	export $$(cat .env.local | xargs) && . venv/bin/activate && alembic upgrade head

run: db-up install setup migrate
	export $$(cat .env.local | xargs) && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	docker compose down -v
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test-wait:
	@echo "Waiting for PostgreSQL to be ready..."
	@set -a; [ -f .env ] && . ./.env; set +a; \
	for i in 1 2 3 4 5 6 7 8 9 10; do \
		docker compose exec -T db pg_isready -U $${POSTGRES_USER:-postgres} && break || sleep 2; \
	done

test-db:
	@set -a; [ -f .env ] && . ./.env; set +a; \
	docker compose exec -T db psql -U $${POSTGRES_USER:-postgres} -d finance_tracker -c "CREATE DATABASE finance_tracker_test;" 2>/dev/null || true

test: db-up test-wait test-db
	@set -a; [ -f .env ] && . ./.env; set +a; \
	export POSTGRES_USER=$${POSTGRES_USER:-postgres}; \
	export POSTGRES_PASSWORD=$${POSTGRES_PASSWORD:-postgres}; \
	export SECRET_KEY=$${SECRET_KEY:-test-secret-key-for-testing-at-least-32-characters}; \
	export TEST_DATABASE_URL="postgresql+asyncpg://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@localhost:5432/finance_tracker_test"; \
	. venv/bin/activate && pytest tests/ -v

