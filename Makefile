include .env
export

PYTHON = python3
VENV = venv
VENV_BIN = $(VENV)/bin

.PHONY: help venv install db-up db-down db-reset create-tables backend frontend dev docker-build docker-up docker-down docker-reset docker-logs docker-create-tables

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "Локальный запуск:"
	@echo "make venv                 - Создание виртуального окружения Python"
	@echo "make install              - Установка зависимостей"
	@echo "make db-up                - Запуск PostgreSQL в Docker"
	@echo "make db-down              - Остановка PostgreSQL"
	@echo "make db-reset             - Полный сброс базы данных"
	@echo "make create-tables        - Создание таблиц базы данных"
	@echo "make backend              - Запуск FastAPI backend"
	@echo "make frontend             - Запуск Streamlit frontend"
	@echo "make dev                  - Запуск backend и frontend вместе"
	@echo ""
	@echo "Docker-запуск всей системы:"
	@echo "make docker-build         - Сборка Docker-образов"
	@echo "make docker-up            - Запуск всей системы в Docker"
	@echo "make docker-down          - Остановка Docker-контейнеров"
	@echo "make docker-reset         - Полный пересозданный запуск Docker"
	@echo "make docker-logs          - Просмотр логов Docker"
	@echo "make docker-create-tables - Создание таблиц внутри Docker"

venv:
	$(PYTHON) -m venv $(VENV)
	@echo ""
	@echo "Виртуальное окружение создано."
	@echo "Активируйте его командой:"
	@echo "source venv/bin/activate"

install:
	$(VENV_BIN)/pip install -r requirements.txt

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d postgres

create-tables:
	$(VENV_BIN)/python -m backend.create_tables

backend:
	$(VENV_BIN)/uvicorn backend.main:app \
		--host $(API_HOST) \
		--port $(API_PORT)

frontend:
	$(VENV_BIN)/streamlit run frontend/app.py \
		--server.port $(STREAMLIT_PORT)

dev:
	@echo "Запуск backend и frontend..."
	@trap 'kill 0' INT; \
	$(VENV_BIN)/uvicorn backend.main:app --host $(API_HOST) --port $(API_PORT) & \
	$(VENV_BIN)/streamlit run frontend/app.py --server.port $(STREAMLIT_PORT) & \
	wait

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-reset:
	docker compose down -v
	docker compose up -d --build

docker-logs:
	docker compose logs -f

docker-create-tables:
	docker compose exec backend python -m backend.create_tables