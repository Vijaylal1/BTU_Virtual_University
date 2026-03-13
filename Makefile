.PHONY: install dev test lint format migrate docker-up docker-down ingest

install:
	poetry install

dev:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8080

test:
	pytest tests/ -v --asyncio-mode=auto

lint:
	ruff check . && mypy .

format:
	ruff format .

migrate:
	psql "$(DATABASE_URL)" -f schema.sql

docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

ingest:
	python -m rag.ingest --source data/chapters/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
