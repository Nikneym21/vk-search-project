# VK Search Project

Модульное приложение для поиска и анализа данных из социальной сети ВКонтакте с использованием плагинной архитектуры.

## 🚀 Возможности

- **Асинхронный поиск** в группах ВКонтакте
- **Модульная архитектура** с плагинами
- **Интеграция с Google Sheets** для экспорта данных
- **Обработка текста** с удалением эмодзи и хэштегов
- **Сравнение ссылок** между таблицами
- **Управление токенами** API
- **Графический интерфейс** на tkinter
- **Логирование** и мониторинг

## 📋 Требования

- Python 3.8+
- 2GB RAM
- 1GB свободного места
- Интернет-соединение

## 🛠 Установка

### 1. Клонирование репозитория

```bash
git clone <repository_url>
cd vk_search_project
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements/requirements.txt
```

### 4. Настройка конфигурации

```bash
cp config/plugins_config.json.example config/plugins_config.json
# Отредактируйте конфигурацию под ваши нужды
```

### 5. Запуск приложения

```bash
python src/main.py
```

## 📁 Структура проекта

```
vk_search_project/
├── src/
│   ├── core/                    # Ядро системы
│   ├── plugins/                 # Плагины
│   ├── gui/                     # Графический интерфейс
│   └── utils/                   # Утилиты
├── config/                      # Конфигурация
├── data/                        # Данные
├── logs/                        # Логи
├── tests/                       # Тесты
├── docs/                        # Документация
└── requirements/                # Зависимости
```

## 🔌 Плагины

### VKSearchPlugin
Поиск данных в VK API с поддержкой асинхронных запросов.

### DataManagerPlugin
Управление данными и SQLite базой данных.

### GoogleSheetsPlugin
Интеграция с Google Sheets для экспорта данных.

### TextProcessingPlugin
Обработка и очистка текста от эмодзи и хэштегов.

### LinkComparatorPlugin
Сравнение ссылок между таблицами.

### TokenManagerPlugin
Управление API токенами с безопасным хранением.

## ⚙️ Конфигурация

Основные настройки находятся в `config/plugins_config.json`:

```json
{
  "plugins": {
    "VKSearchPlugin": {
      "enabled": true,
      "config": {
        "api_version": "5.131",
        "rate_limit": 3,
        "search_limit": 100
      }
    }
  }
}
```

## 🎯 Использование

### Поиск постов

1. Запустите приложение
2. Введите название группы ВКонтакте
3. Укажите ключевые слова для поиска
4. Нажмите "Поиск"
5. Результаты отобразятся в таблице

### Экспорт данных

- **CSV**: Сохранение в формате CSV
- **JSON**: Экспорт в JSON формат
- **Google Sheets**: Загрузка в Google таблицы

### Обработка текста

- Удаление эмодзи и хэштегов
- Извлечение ссылок
- Анализ статистики текста

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest tests/

# Запуск конкретных тестов
pytest tests/unit/test_plugin_manager.py
pytest tests/integration/test_plugins_integration.py
```

## 📚 Документация

- [Техническая документация](docs/TECHNICAL_DOCUMENTATION.md)
- [Документация по плагинам](PLUGINS_README.md)
- [Руководство пользователя](docs/USER_GUIDE.md)

## 🤝 Разработка

### Создание нового плагина

1. Создайте класс, наследующий от `BasePlugin`
2. Реализуйте обязательные методы: `initialize()`, `shutdown()`
3. Добавьте валидацию конфигурации
4. Зарегистрируйте плагин в `src/plugins/__init__.py`
5. Добавьте конфигурацию в `config/plugins_config.json`

### Пример плагина

```python
from src.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "MyPlugin"
        self.version = "1.0.0"
    
    def initialize(self) -> None:
        self.log_info("Плагин инициализирован")
    
    def shutdown(self) -> None:
        self.log_info("Плагин завершен")
```

## 🐛 Отчеты об ошибках

Если вы нашли ошибку, создайте issue с описанием:
- Шаги для воспроизведения
- Ожидаемое поведение
- Фактическое поведение
- Версия Python и ОС

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 👥 Авторы

- Development Team

## 🙏 Благодарности

- VK API за предоставление доступа к данным
- Сообществу Python за отличные библиотеки
- Всем участникам проекта

---

**Версия:** 1.0.0  
**Последнее обновление:** 2024 