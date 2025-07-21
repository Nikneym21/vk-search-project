# Документация по плагинам VK Search Project

## Обзор

Проект использует модульную архитектуру с плагинами для разделения функциональности. Все плагины наследуются от базового класса `BasePlugin` и следуют единому интерфейсу.

## Список плагинов

### 1. VKSearchPlugin
**Расположение:** `src/plugins/vk_search/vk_search_plugin.py`

**Описание:** Основной плагин для поиска данных в VK API.

**Основные функции:**
- Асинхронный поиск постов в группах
- Поиск информации о пользователях
- Поиск по ключевым словам
- Ограничение скорости запросов
- Обработка ошибок API

**Конфигурация:**
```json
{
  "api_version": "5.131",
  "rate_limit": 3,
  "max_requests_per_second": 3,
  "timeout": 30,
  "retry_attempts": 3,
  "search_limit": 100
}
```

### 2. DataManagerPlugin
**Расположение:** `src/plugins/data_manager/data_manager_plugin.py`

**Описание:** Плагин для управления данными и SQLite базой данных.

**Основные функции:**
- Инициализация SQLite базы данных
- Сохранение результатов поиска
- Экспорт данных в CSV/JSON
- Автоматическое резервное копирование
- Управление схемой базы данных

**Конфигурация:**
```json
{
  "database_path": "data/vk_search.db",
  "auto_backup": true,
  "backup_interval": 3600,
  "max_backup_files": 10
}
```

### 3. DatabasePlugin
**Расположение:** `src/plugins/database/database_plugin.py`

**Описание:** Плагин для работы с файловой системой и сохранения результатов.

**Основные функции:**
- Сохранение результатов в CSV/JSON
- Загрузка данных из файлов
- Управление файлами результатов
- Получение информации о файлах
- Автоматическое создание директорий

**Конфигурация:**
```json
{
  "data_dir": "data/results",
  "backup_enabled": true,
  "auto_save": true,
  "max_file_size": "100MB"
}
```

### 4. GoogleSheetsPlugin
**Расположение:** `src/plugins/google_sheets/google_sheets_plugin.py`

**Описание:** Плагин для интеграции с Google Sheets API.

**Основные функции:**
- Подключение к Google Sheets API
- Загрузка данных в таблицы
- Выгрузка данных из таблиц
- Создание новых таблиц
- Управление листами

**Конфигурация:**
```json
{
  "service_account_path": "config/service_account.json",
  "scopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
  ],
  "auto_backup": true,
  "max_rows_per_request": 1000
}
```

### 5. TextProcessingPlugin
**Расположение:** `src/plugins/text_processing/text_processing_plugin.py`

**Описание:** Плагин для обработки и очистки текста.

**Основные функции:**
- Удаление эмодзи и хэштегов
- Извлечение ссылок из текста
- Анализ текста и статистика
- Пакетная обработка текстов
- Нормализация пробелов

**Конфигурация:**
```json
{
  "remove_emojis": true,
  "remove_hashtags": true,
  "remove_urls": false,
  "remove_mentions": true,
  "normalize_whitespace": true,
  "min_text_length": 3,
  "max_text_length": 10000
}
```

### 6. LinkComparatorPlugin
**Расположение:** `src/plugins/link_comparator/link_comparator_plugin.py`

**Описание:** Плагин для сравнения ссылок между таблицами.

**Основные функции:**
- Загрузка таблиц из CSV/Excel
- Извлечение ссылок из колонок
- Сравнение ссылок между таблицами
- Сохранение результатов сравнения
- Анализ статистики ссылок

**Конфигурация:**
```json
{
  "output_dir": "data/results",
  "link_patterns": [
    "https?://[^\\s<>\"]+",
    "www\\.[^\\s<>\"]+",
    "vk\\.com/[^\\s<>\"]+"
  ],
  "case_sensitive": false,
  "ignore_duplicates": true
}
```

### 7. TokenManagerPlugin
**Расположение:** `src/plugins/token_manager/token_manager_plugin.py`

**Описание:** Плагин для управления API токенами.

**Основные функции:**
- Загрузка и сохранение токенов
- Валидация токенов
- Резервное копирование токенов
- Автоматическая проверка токенов
- Безопасное хранение

**Конфигурация:**
```json
{
  "tokens_file": "config/tokens.json",
  "backup_enabled": true,
  "auto_validation": true,
  "validation_interval": 3600
}
```

## Архитектура плагинов

### Базовый класс BasePlugin

Все плагины наследуются от `BasePlugin`, который предоставляет:

- **Жизненный цикл:** `initialize()`, `shutdown()`
- **Логирование:** `log_info()`, `log_error()`, `log_warning()`
- **События:** `emit_event()` для отправки событий
- **Конфигурация:** `validate_config()`, `get_required_config_keys()`
- **Статистика:** `get_statistics()`

### Система событий

Плагины используют систему событий для взаимодействия:

- `PLUGIN_LOADED` - плагин загружен
- `PLUGIN_UNLOADED` - плагин выгружен
- `DATA_UPDATED` - данные обновлены
- `SEARCH_STARTED` - поиск начат
- `SEARCH_COMPLETED` - поиск завершен
- `ERROR_OCCURRED` - произошла ошибка

### Менеджер плагинов

`PluginManager` отвечает за:

- Динамическую загрузку плагинов
- Управление жизненным циклом
- Вызов методов плагинов
- Обработку ошибок

## Использование плагинов

### Загрузка плагина

```python
from src.core.plugin_manager import PluginManager

plugin_manager = PluginManager()
plugin_manager.initialize()

# Загрузка плагина с конфигурацией
config = {"api_version": "5.131", "rate_limit": 3}
plugin_manager.load_plugin("VKSearchPlugin", config)
```

### Вызов методов плагина

```python
# Получение экземпляра плагина
vk_plugin = plugin_manager.get_plugin("VKSearchPlugin")

# Вызов метода
results = vk_plugin.search_posts("group_name", "keyword")
```

### Обработка событий

```python
from src.core.event_system import EventType, event_system

def on_data_updated(event):
    print(f"Данные обновлены: {event.data}")

event_system.subscribe(EventType.DATA_UPDATED, on_data_updated)
```

## Конфигурация

Все плагины настраиваются через файл `config/plugins_config.json`:

```json
{
  "plugins": {
    "PluginName": {
      "enabled": true,
      "config": {
        "param1": "value1",
        "param2": "value2"
      }
    }
  }
}
```

## Разработка новых плагинов

Для создания нового плагина:

1. Создайте класс, наследующий от `BasePlugin`
2. Реализуйте обязательные методы: `initialize()`, `shutdown()`
3. Добавьте валидацию конфигурации в `validate_config()`
4. Зарегистрируйте плагин в `src/plugins/__init__.py`
5. Добавьте конфигурацию в `config/plugins_config.json`

## Зависимости

Основные зависимости для всех плагинов:

- `aiohttp` - для асинхронных HTTP запросов
- `pandas` - для работы с данными
- `loguru` - для логирования
- `pydantic` - для валидации конфигурации
- `gspread` - для Google Sheets
- `emoji` - для обработки эмодзи
- `openpyxl` - для работы с Excel файлами 