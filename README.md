# VK Search Project

Модульная система для поиска и анализа данных ВКонтакте с плагинной архитектурой.

## Структура проекта

```
vk_search_project/
├── src/
│   ├── core/           # Ядро системы
│   ├── plugins/        # Плагины для бизнес-логики
│   ├── gui/           # Пользовательский интерфейс
│   └── utils/         # Утилиты и хелперы
├── tests/             # Тесты
├── docs/              # Документация
├── config/            # Конфигурационные файлы
├── data/              # Данные и результаты
└── requirements/      # Зависимости
```

## Плагины

- **vk_search** - Поиск данных ВКонтакте
- **data_manager** - Управление данными
- **google_sheets** - Интеграция с Google Sheets
- **link_comparator** - Сравнение ссылок
- **text_processor** - Обработка текста
- **token_manager** - Управление токенами

## Установка

```bash
pip install -r requirements/requirements.txt
```

## Запуск

```bash
python src/main.py
```

## Разработка

Для добавления нового плагина создайте папку в `src/plugins/` и реализуйте интерфейс `BasePlugin`. 