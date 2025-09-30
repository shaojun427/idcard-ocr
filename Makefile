PYTHON ?= python3
PIP ?= pip

.PHONY: install format lint test dev-up dev-down docker-build docker-run

install:
	$(PIP) install -r requirements-dev.txt

format:
	ruff check src tests --fix
	black src tests

lint:
	ruff check src tests
	black --check src tests

test:
	pytest

dev-up:
	docker-compose -f docker-compose.dev.yml up --build

dev-down:
	docker-compose -f docker-compose.dev.yml down

docker-build:
	docker build -t idcard-ocr:latest .

docker-run:
	docker run --d --name idcard-ocr-api -p 8080:8080 idcard-ocr:latest

docker-restart:
	docker stop idcard-ocr-api
	docker rm idcard-ocr-api
	docker run --rm --name idcard-ocr-api -p 8080:8080 idcard-ocr:latest