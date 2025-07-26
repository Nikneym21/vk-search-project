# Настройка дебаггера и автотестов

## Обзор

Этот документ описывает настройку системы отладки и автоматического тестирования для проекта.

## GitHub Actions

### Основные Workflows

#### 1. Tests (`test.yml`)
- **Триггер**: Push в `main`/`develop`, Pull Request в `main`
- **Python версии**: 3.9, 3.10, 3.11, 3.12
- **Задачи**:
  - Установка зависимостей
  - Создание тестового окружения
  - Запуск тестов с покрытием
  - Загрузка отчета в Codecov
  - Линтинг кода (flake8, black, isort, mypy)
  - Проверка безопасности (bandit, safety)

#### 2. Debug and Performance (`debug.yml`)
- **Триггер**: Push в `main`, ручной запуск, ежедневно в 2:00 UTC
- **Задачи**:
  - Отладка и профилирование памяти
  - Проверка утечек памяти
  - Бенчмарки производительности
  - Профилирование операций БД
  - Мониторинг системы
  - Проверка здоровья плагинов

### Настройка Secrets

Для работы с GitHub Actions добавьте следующие secrets в настройках репозитория:

```bash
# VK API токены (если нужны для тестов)
VK_ACCESS_TOKEN=your_vk_token
VK_SERVICE_TOKEN=your_service_token

# Google Sheets (если нужны для тестов)
GOOGLE_SHEETS_CREDENTIALS=your_google_credentials

# Codecov (для отчетов о покрытии)
CODECOV_TOKEN=your_codecov_token
```

## VS Code Настройка

### Расширения

Установите рекомендуемые расширения из `.vscode/extensions.json`:

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.isort
code --install-extension ms-python.flake8
code --install-extension ms-python.mypy-type-checker
code --install-extension ms-python.pytest-adapter
```

### Конфигурация дебаггера

В `.vscode/launch.json` настроены следующие конфигурации:

1. **Python: Main Application** - запуск основного приложения
2. **Python: Current File** - запуск текущего файла
3. **Python: Debug Tests** - отладка тестов
4. **Python: Debug Plugin Manager** - отладка менеджера плагинов
5. **Python: Debug Database Plugin** - отладка плагина БД
6. **Python: Debug VK Search Plugin** - отладка плагина VK

### Горячие клавиши

- `F5` - запуск дебаггера
- `Ctrl+Shift+P` → "Python: Select Interpreter" - выбор интерпретатора
- `Ctrl+Shift+P` → "Python: Run Tests" - запуск тестов
- `Ctrl+Shift+P` → "Python: Run Linting" - линтинг

## Локальная разработка

### Установка зависимостей

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements/requirements.txt

# Установка pre-commit hooks
pre-commit install
```

### Команды Makefile

```bash
# Справка
make help

# Настройка проекта
make setup

# Установка зависимостей
make install

# Запуск тестов
make test
make test-fast
make test-coverage

# Линтинг и форматирование
make lint
make format

# Проверка безопасности
make security

# Полная проверка
make check-all

# Очистка
make clean

# Запуск приложения
make run
make debug
```

### Pre-commit Hooks

Автоматически выполняются при каждом коммите:

- Форматирование кода (black, isort)
- Линтинг (flake8, mypy)
- Проверка безопасности (bandit)
- Запуск тестов (pytest)

## Конфигурационные файлы

### Линтинг и форматирование

- `.flake8` - настройки flake8
- `pyproject.toml` - настройки black, isort, pytest, mypy
- `.bandit` - настройки проверки безопасности

### Покрытие кода

- `.coveragerc` - настройки coverage.py
- Отчеты сохраняются в `htmlcov/`

### VS Code

- `.vscode/settings.json` - настройки редактора
- `.vscode/launch.json` - конфигурации дебаггера
- `.vscode/tasks.json` - задачи для VS Code
- `.vscode/extensions.json` - рекомендуемые расширения

## Мониторинг и профилирование

### Профилирование памяти

```bash
# Профилирование с memory-profiler
python -m memory_profiler your_script.py

# Профилирование с cProfile
python -m cProfile -o profile.prof your_script.py
python -c "import pstats; pstats.Stats('profile.prof').sort_stats('cumulative').print_stats(20)"
```

### Мониторинг системы

```bash
# Проверка использования ресурсов
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
```

## Отладка плагинов

### Отладка PluginManager

```python
# В коде добавьте точки останова
import pdb; pdb.set_trace()

# Или используйте logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Отладка асинхронного кода

```python
# Для отладки async функций
import asyncio
import pdb

async def debug_async():
    pdb.set_trace()
    # ваш код

# Запуск
asyncio.run(debug_async())
```

## Полезные команды

### Проверка импортов

```bash
# Проверка всех импортов
python -c "import src.main; print('All imports OK')"

# Проверка конкретного плагина
python -c "from src.plugins.database.database_plugin import DatabasePlugin; print('Database plugin OK')"
```

### Тестирование производительности

```bash
# Бенчмарки
pytest test/performance/ -v --benchmark-only

# Профилирование
python -m cProfile -o profile.prof main.py
```

### Проверка безопасности

```bash
# Bandit
bandit -r src/ -f json -o bandit-report.json

# Safety
safety check --json --output safety-report.json
```

## Troubleshooting

### Проблемы с импортами

1. Проверьте `PYTHONPATH`:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. Проверьте структуру проекта:
   ```bash
   find src/ -name "*.py" -exec python -c "import {}" \;
   ```

### Проблемы с тестами

1. Проверьте зависимости:
   ```bash
   pip install pytest pytest-cov pytest-asyncio
   ```

2. Проверьте конфигурацию:
   ```bash
   pytest --collect-only
   ```

### Проблемы с дебаггером

1. Проверьте интерпретатор Python в VS Code
2. Убедитесь, что установлен `debugpy`
3. Проверьте настройки в `launch.json`

## Интеграция с IDE

### PyCharm

1. Откройте проект в PyCharm
2. Настройте интерпретатор Python
3. Настройте тесты: `File` → `Settings` → `Tools` → `Python Integrated Tools`
4. Настройте дебаггер: `Run` → `Edit Configurations`

### VS Code

1. Установите Python расширение
2. Выберите интерпретатор: `Ctrl+Shift+P` → `Python: Select Interpreter`
3. Настройте тесты: `Ctrl+Shift+P` → `Python: Configure Tests`
4. Запустите дебаггер: `F5`

## Заключение

Эта настройка обеспечивает:

- ✅ Автоматическое тестирование при каждом push
- ✅ Проверку качества кода
- ✅ Отладку в VS Code
- ✅ Профилирование производительности
- ✅ Мониторинг безопасности
- ✅ Покрытие кода тестами

Для начала работы выполните:

```bash
make setup
make test
```
