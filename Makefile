include .env
export

PYTHON = python3
VENV = venv
VENV_BIN = $(VENV)/bin

.PHONY: help venv install db-up db-down db-reset create-tables backend frontend run

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "make venv            - Создание виртуального окружения Python"
	@echo "make install         - Установка зависимостей"
	@echo "make db-up           - Запуск PostgreSQL в Docker"
	@echo "make db-down         - Остановка Docker-контейнеров"
	@echo "make db-reset        - Полный сброс базы данных"
	@echo "make create-tables   - Создание таблиц базы данных"
	@echo "make backend         - Запуск FastAPI backend"
	@echo "make frontend        - Запуск Streamlit frontend"
	@echo "make run             - Запуск Docker и создание таблиц"

venv:
	$(PYTHON) -m venv $(VENV)
	@echo ""
	@echo "Виртуальное окружение создано."
	@echo "Активируйте его командой:"
	@echo "source venv/bin/activate"

install:
	$(VENV_BIN)/pip install -r requirements.txt

db-up:
	docker compose up -d

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d

create-tables:
	$(VENV_BIN)/python -m backend.create_tables

backend:
	$(VENV_BIN)/uvicorn backend.main:app \
		--reload \
		--host $(API_HOST) \
		--port $(API_PORT)

frontend:
	$(VENV_BIN)/streamlit run frontend/app.py \
		--server.port $(STREAMLIT_PORT)

run:
	docker compose up -d
	$(VENV_BIN)/python -m backend.create_tables