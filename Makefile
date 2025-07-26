.PHONY: help install test lint format clean setup dev run debug

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Настройка проекта
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements/requirements.txt
	pre-commit install

install: ## Установка зависимостей
	pip install -r requirements/requirements.txt

dev: ## Установка зависимостей для разработки
	pip install -r requirements/requirements.txt
	pre-commit install

test: ## Запуск тестов
	pytest test/ -v --cov=src --cov-report=html --cov-report=term-missing

test-fast: ## Быстрые тесты
	pytest test/ -v --tb=short --no-cov

test-coverage: ## Тесты с покрытием
	pytest test/ -v --cov=src --cov-report=html --cov-report=xml

lint: ## Проверка кода
	flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	black --check src/
	isort --check-only src/
	mypy src/ --ignore-missing-imports

format: ## Форматирование кода
	black src/
	isort src/

security: ## Проверка безопасности
	bandit -r src/ -f json -o bandit-report.json
	safety check

clean: ## Очистка
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "bandit-report.json" -delete
	find . -type f -name "safety-report.json" -delete

run: ## Запуск приложения
	python main.py

debug: ## Запуск в режиме отладки
	python -m pdb main.py

profile: ## Профилирование
	python -m cProfile -o profile.prof main.py

benchmark: ## Бенчмарки
	pytest test/performance/ -v --benchmark-only

check-all: ## Полная проверка
	make lint
	make security
	make test
	make format

ci: ## Команды для CI/CD
	pytest test/ -v --cov=src --cov-report=xml
	flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127
	black --check src/
	isort --check-only src/
	mypy src/ --ignore-missing-imports
	bandit -r src/ -f json -o bandit-report.json || true
