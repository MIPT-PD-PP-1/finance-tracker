.PHONY: db-up db-down install setup migrate run clean test test-db

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

test-db:
	@docker exec -it $$(docker compose ps -q db) psql -U $${POSTGRES_USER:-postgres} -c "CREATE DATABASE finance_tracker_test;" 2>/dev/null || true

test: db-up test-db
	export $$(cat .env.local | xargs) && \
	export TEST_DATABASE_URL="postgresql+asyncpg://$${POSTGRES_USER:-postgres}:$${POSTGRES_PASSWORD:-postgres}@localhost:5432/finance_tracker_test" && \
	. venv/bin/activate && pytest tests/ -v

