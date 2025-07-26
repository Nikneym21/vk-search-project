# 🔌 PLUGINS README

**Документация всех плагинов системы VK Search Project**

---

## 📋 **ОБЗОР ПЛАГИНОВ**

Система содержит **12 активных плагинов**, управляемых через **PluginManager-as-Core архитектуру**.

### **Иерархия плагинов:**
```
PluginManager (ядро)
├── VKSearchPlugin (поиск данных)
├── DatabasePlugin (хранение данных)
├── PostProcessorPlugin (обработка данных)
│   ├── DeduplicationPlugin
│   ├── TextProcessingPlugin
│   └── FilterPlugin
├── TokenManagerPlugin (управление токенами)
├── GoogleSheetsPlugin (экспорт)
├── LinkComparatorPlugin (сравнение)
├── SettingsManagerPlugin (настройки)
├── LoggerPlugin (логирование)
└── MonitoringPlugin (мониторинг)
```

---

## 🚀 **ОСНОВНЫЕ ПЛАГИНЫ**

### 1. **VKSearchPlugin** 🔍

**Расположение:** `src/plugins/vk_search/`

**Ответственность:**
- Поиск публикаций в VKontakte через VK API
- Асинхронная обработка запросов
- Управление кэшированием результатов
- Адаптивная ротация токенов

**Ключевые методы:**
```python
async def mass_search_with_tokens(keyword_token_pairs, start_date, end_date)
async def search_multiple_queries(queries, start_date, end_date)
def set_token_manager(token_manager)  # Интеграция с TokenManager
```

**Интеграция:**
- Использует `vk_time_utils.py` для работы с временными зонами
- Получает токены от `TokenManagerPlugin`
- Сохраняет результаты через `DatabasePlugin`

### 2. **DatabasePlugin** 🗄️

**Расположение:** `src/plugins/database/`

**Ответственность:**
- Управление SQLite базой данных
- Сохранение и извлечение задач парсинга
- Экспорт данных в CSV формат
- Управление метаданными задач

**Ключевые методы:**
```python
def create_task(keywords, start_date, end_date) -> int
def save_posts(task_id, posts)
def export_task_to_csv(task_id, filepath)
def get_tasks() -> List[Dict]
```

**Замена:** Заменил устаревший `DataManagerPlugin`

### 3. **PostProcessorPlugin** ⚙️

**Расположение:** `src/plugins/post_processor/`

**Ответственность:**
- Координация обработки постов
- Управление тремя подплагинами
- Обеспечение правильного порядка обработки
- Предоставление единого API для обработки

**Подплагины:**
```python
self.deduplication_plugin    # Удаление дублей
self.text_processing_plugin  # Очистка текста
self.filter_plugin          # Фильтрация
```

**Порядок обработки:**
1. **Deduplication** → удаление дублей по ссылкам
2. **TextProcessing** → очистка и нормализация текста
3. **Filtering** → фильтрация по ключевым словам

**Ключевые методы:**
```python
def process_posts(posts, keywords) -> List[Dict]
def get_statistics() -> Dict
```

---

## 🔧 **СЛУЖЕБНЫЕ ПЛАГИНЫ**

### 4. **TokenManagerPlugin** 🔑

**Расположение:** `src/plugins/token_manager/`

**Ответственность:**
- Управление VK API токенами
- Ротация токенов по лимитам
- Безопасное хранение токенов
- Мониторинг состояния токенов

**Ключевые методы:**
```python
def get_token(service="vk") -> str
def add_token(service, token, metadata)
def list_tokens() -> List[Dict]
```

### 5. **GoogleSheetsPlugin** 📊

**Расположение:** `src/plugins/google_sheets/`

**Ответственность:**
- Интеграция с Google Sheets API
- Экспорт обработанных данных
- Автоматическая синхронизация
- Управление доступом к таблицам

**Ключевые методы:**
```python
def export_to_sheets(data, spreadsheet_id)
def create_spreadsheet(title) -> str
def get_sheet_data(spreadsheet_id) -> List[List]
```

### 6. **LinkComparatorPlugin** 🔗

**Расположение:** `src/plugins/link_comparator/`

**Ответственность:**
- Сравнение ссылок между таблицами
- Поиск пересечений и различий
- Анализ уникальности контента
- Интеграция с DatabasePlugin для сохранения

**Ключевые методы:**
```python
def compare_links(source_links, target_links) -> Dict
def find_unique_links(links_list) -> List
def save_comparison_results(results)
```

---

## ⚙️ **СИСТЕМНЫЕ ПЛАГИНЫ**

### 7. **SettingsManagerPlugin** ⚙️

**Расположение:** `src/plugins/settings_manager/`

**Ответственность:**
- Управление настройками приложения
- Центральное хранение конфигурации
- Валидация настроек
- Автоматическое сохранение изменений

**Ключевые методы:**
```python
def get_setting(key, default=None)
def set_setting(key, value)
def save_settings()
def load_settings()
```

### 8. **LoggerPlugin** 📝

**Расположение:** `src/plugins/logger/`

**Ответственность:**
- Централизованное логирование
- Управление уровнями логов
- Ротация файлов логов
- Интеграция со всеми плагинами

**Ключевые методы:**
```python
def log_info(message, component=None)
def log_error(message, component=None)
def log_warning(message, component=None)
def get_logs(level=None) -> List[str]
```

### 9. **MonitoringPlugin** 📈

**Расположение:** `src/plugins/monitoring/`

**Ответственность:**
- Мониторинг производительности в реальном времени
- Сбор метрик от других плагинов
- Алерты при проблемах
- Безопасная работа с async задачами

**Ключевые методы:**
```python
def get_system_metrics() -> Dict
def start_monitoring_if_needed()
def get_performance_stats() -> Dict
```

**Исправления:** Устранена проблема "no running event loop"

---

## 🏗️ **ПОДПЛАГИНЫ PostProcessorPlugin**

### 10. **DeduplicationPlugin** 🔄

**Расположение:** `src/plugins/post_processor/deduplication/`

**Ответственность:**
- Удаление дублирующихся постов
- Сравнение по ссылкам (link_hash)
- Сохранение уникальных записей
- Первый этап обработки

**Алгоритм:**
```python
# Создание хэша ссылки
link_hash = hashlib.md5(link.encode(), usedforsecurity=False).hexdigest()

# Фильтрация дублей
unique_posts = [post for post in posts if post['link_hash'] not in seen_hashes]
```

### 11. **TextProcessingPlugin** 📝

**Расположение:** `src/plugins/post_processor/text_processing/`

**Ответственность:**
- Очистка текста от эмодзи и спецсимволов
- Нормализация текста для фильтрации
- Подготовка данных для FilterPlugin
- Второй этап обработки

**Операции:**
- Удаление эмодзи
- Очистка HTML тегов
- Нормализация пробелов
- Приведение к нижнему регистру

### 12. **FilterPlugin** 🎯

**Расположение:** `src/plugins/post_processor/filter/`

**Ответственность:**
- Фильтрация постов по ключевым словам
- Точное и нечеткое совпадение
- Обработка минус-слов
- Третий (финальный) этап обработки

**Алгоритм:**
```python
# Получает уже очищенный текст от TextProcessingPlugin
# Применяет фильтры по ключевым словам
# Возвращает только релевантные посты
```

---

## 🔗 **ИНТЕГРАЦИЯ ПЛАГИНОВ**

### **Принципы взаимодействия:**

1. **Все плагины получаются через PluginManager:**
```python
plugin_manager = PluginManager()
vk_search = plugin_manager.get_plugin("vk_search")
database = plugin_manager.get_plugin("database")
```

2. **Зависимости устанавливаются в PluginManager:**
```python
def setup_plugin_dependencies(self):
    vk_search.set_token_manager(token_manager)
    post_processor.set_text_processing_plugin(text_processing)
```

3. **Строгий порядок обработки данных:**
   - VKSearch → Database → PostProcessor → Database → Export

### **Запрещенные практики:**
- ❌ Прямые импорты плагинов в GUI
- ❌ Создание экземпляров плагинов напрямую
- ❌ Обход PluginManager при получении плагинов

---

## 📊 **СТАТИСТИКА ПЛАГИНОВ**

**Всего плагинов:** 12
**Основных:** 3 (VKSearch, Database, PostProcessor)
**Служебных:** 3 (TokenManager, GoogleSheets, LinkComparator)
**Системных:** 3 (Settings, Logger, Monitoring)
**Подплагинов:** 3 (Deduplication, TextProcessing, Filter)

**Архитектурное соответствие:** 100% ✅
**PluginManager-as-Core:** Полностью реализовано ✅
**Порядок обработки:** Строго соблюдается ✅

---

**Документация обновлена:** 27.07.2025
**Версия системы:** 2.3
**Статус:** ✅ Все плагины соответствуют архитектуре
