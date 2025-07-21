# Настройка GitHub репозитория

## Шаги для создания репозитория на GitHub

### 1. Создание репозитория на GitHub

1. Перейдите на [GitHub](https://github.com)
2. Нажмите кнопку "New" или "+" в правом верхнем углу
3. Выберите "New repository"
4. Заполните форму:
   - **Repository name**: `vk-search-project`
   - **Description**: `Модульное приложение для поиска данных в ВКонтакте с плагинной архитектурой`
   - **Visibility**: Public или Private (по вашему выбору)
   - **Initialize with**: НЕ ставьте галочки (у нас уже есть файлы)
5. Нажмите "Create repository"

### 2. Подключение локального репозитория к GitHub

После создания репозитория на GitHub, выполните следующие команды:

```bash
# Добавление удаленного репозитория
git remote add origin https://github.com/YOUR_USERNAME/vk-search-project.git

# Проверка подключения
git remote -v

# Пуш в GitHub
git push -u origin main
```

### 3. Альтернативный способ (если у вас есть GitHub CLI)

```bash
# Создание репозитория через GitHub CLI
gh repo create vk-search-project --public --description "Модульное приложение для поиска данных в ВКонтакте"

# Пуш в созданный репозиторий
git push -u origin main
```

## Структура проекта в репозитории

После пуша в репозитории будет доступна следующая структура:

```
vk-search-project/
├── README.md                    # Основная документация
├── PLUGINS_README.md           # Документация по плагинам
├── docs/
│   └── TECHNICAL_DOCUMENTATION.md  # Техническая документация
├── src/
│   ├── core/                   # Ядро системы
│   ├── plugins/                # Плагины
│   ├── gui/                    # Графический интерфейс
│   └── utils/                  # Утилиты
├── config/
│   └── plugins_config.json     # Конфигурация плагинов
├── requirements/
│   └── requirements.txt        # Зависимости
├── data/
│   └── results/               # Результаты поиска
├── logs/                      # Логи приложения
├── tests/                     # Тесты
└── .gitignore                 # Исключения для git
```

## Дополнительные настройки

### Настройка GitHub Pages (опционально)

Для создания сайта документации:

1. Перейдите в Settings репозитория
2. Прокрутите до раздела "Pages"
3. В "Source" выберите "Deploy from a branch"
4. Выберите ветку "main" и папку "/docs"
5. Нажмите "Save"

### Настройка Actions (опционально)

Создайте файл `.github/workflows/ci.yml` для автоматического тестирования:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10"]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/requirements.txt
    - name: Run tests
      run: |
        pytest tests/
```

## Полезные команды

```bash
# Проверка статуса
git status

# Просмотр истории коммитов
git log --oneline

# Создание новой ветки
git checkout -b feature/new-feature

# Слияние изменений
git merge feature/new-feature

# Обновление с удаленного репозитория
git pull origin main

# Просмотр изменений
git diff
```

## Контакты

Если у вас возникли вопросы по настройке репозитория, создайте issue в репозитории или обратитесь к документации GitHub. 