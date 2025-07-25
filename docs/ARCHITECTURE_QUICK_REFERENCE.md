# 📋 АРХИТЕКТУРНЫЙ СПРАВОЧНИК

## 🎯 **КЛЮЧЕВЫЕ ПРИНЦИПЫ**

### **PluginManager как Ядро**
- Все плагины управляются через PluginManager
- Никаких прямых связей между плагинами
- Единообразный доступ к плагинам

### **Оптимизированная Цепочка Обработки**
```
PostProcessorPlugin → DatabasePlugin (получение данных)
    ↓
DeduplicationPlugin (удаление дубликатов по ссылкам)
    ↓
TextProcessingPlugin (очистка текста - только при необходимости)
    ↓
FilterPlugin (фильтрация по ключевым словам - только при наличии ключевых слов)
    ↓
PostProcessorPlugin (компиляция результатов)
    ↓
DatabasePlugin (сохранение через PluginManager)
```

---

## 🔧 **ОСНОВНЫЕ ПЛАГИНЫ**

| Плагин | Роль | Ответственность | Оптимизации |
|--------|------|-----------------|-------------|
| **PluginManager** | Ядро системы | Управление всеми плагинами | Централизованное управление |
| **PostProcessorPlugin** | Координатор обработки | Координация обработки публикаций | Ленивая обработка, батчевая обработка, кэширование |
| **DatabasePlugin** | Расширенное хранилище | SQLite БД + экспорт + статистика | Оптимизированные запросы, интегрированная статистика |
| **DeduplicationPlugin** | Дедупликация | Удаление дубликатов | Раннее отсечение дубликатов |
| **TextProcessingPlugin** | Обработка текста | Очистка и нормализация | Ленивая обработка |
| **FilterPlugin** | Фильтрация | Фильтрация по ключевым словам | Работа с очищенным текстом |
| **VKSearchPlugin** | Поиск в ВК | VK API запросы | Ротация токенов |
| **TokenManagerPlugin** | Управление токенами | Ротация VK токенов | Мониторинг лимитов |
| **GoogleSheetsPlugin** | Google Sheets | Интеграция с Google Sheets | Автоматическая синхронизация |
| **LinkComparatorPlugin** | Сравнение ссылок | Сравнение таблиц | Извлечение ссылок |
| **SettingsManagerPlugin** | Управление настройками | Сохранение настроек | Автосохранение |
| **LoggerPlugin** | Логирование | Централизованное логирование | Batch-логирование |
| **MonitoringPlugin** | Мониторинг | Метрики производительности | Дашборд мониторинга |

---

## 🔄 **ОПТИМИЗИРОВАННЫЙ ПОТОК ДАННЫХ**

### **Парсинг:**
```
VKSearchPlugin → TokenManagerPlugin → DatabasePlugin
```

### **Обработка:**
```
GUI → PluginManager → PostProcessorPlugin
    ↓
DeduplicationPlugin (раннее отсечение)
    ↓
TextProcessingPlugin (ленивая обработка)
    ↓
FilterPlugin (оптимизированная фильтрация)
    ↓
DatabasePlugin (сохранение результатов)
```

### **Экспорт:**
```
GUI → PluginManager → [DatabasePlugin/GoogleSheetsPlugin]
```

---

## 📁 **СТРУКТУРА ПРОЕКТА**

```
src/
├── core/plugin_manager.py          # Центральное ядро
├── plugins/
│   ├── post_processor/            # Обработка публикаций
│   │   ├── deduplication/         # Дедупликация (раннее отсечение)
│   │   ├── text_processing/       # Обработка текста (ленивая)
│   │   └── filter/               # Фильтрация (оптимизированная)
│   ├── database/                 # Расширенное хранилище данных
│   ├── vk_search/               # Поиск в ВК
│   ├── token_manager/           # Управление токенами
│   ├── google_sheets/           # Google Sheets
│   ├── link_comparator/         # Сравнение ссылок
│   ├── settings_manager/        # Управление настройками
│   ├── logger/                  # Логирование
│   ├── monitoring/              # Мониторинг
│   ├── todo_manager/            # Управление задачами (не реализован)
│   └── [другие плагины...]
└── gui/                        # Интерфейсы
```

---

## 🛠️ **ОСНОВНЫЕ МЕТОДЫ**

### **PluginManager:**
```python
get_plugin(name)           # Получить плагин
coordinate_search_and_filter()  # Координация поиска и фильтрации
setup_plugin_dependencies()     # Установка зависимостей
```

### **PostProcessorPlugin:**
```python
process_posts_optimized()       # Оптимизированная обработка
process_posts_in_batches()      # Батчевая обработка
process_posts_with_cache()      # Обработка с кэшированием
```

### **DatabasePlugin (расширенный):**
```python
create_task()                   # Создание задачи
save_posts()                    # Сохранение постов
get_statistics()                # Статистика
calculate_posts_statistics()    # Подсчет статистики (интегрировано)
export_task_to_csv()           # Экспорт в CSV
save_results_to_json()         # Экспорт в JSON
```

---

## ⚡ **ОПТИМИЗАЦИИ**

### **Ленивая Обработка:**
```python
# Пропуск ненужных этапов
if keywords:
    posts = text_processing.process(posts)
    posts = filter_plugin.filter(posts, keywords)
```

### **Раннее Отсечение:**
```python
# Удаление дубликатов в первую очередь
posts = deduplication_plugin.remove_duplicates(posts)
```

### **Батчевая Обработка:**
```python
# Обработка больших объемов батчами
for batch in batches:
    processed_batch = process_batch(batch)
```

### **Кэширование:**
```python
# Кэширование результатов
if cache_key in cache:
    return cache[cache_key]
```

---

## 🔗 **ПРИНЦИПЫ ИНТЕГРАЦИИ**

### **Доступ к плагинам:**
```python
# Правильно
plugin = plugin_manager.get_plugin('plugin_name')

# Неправильно
plugin = self.direct_plugin
```

### **Разделение ответственности:**
- Каждый плагин отвечает только за свою область
- Никаких пересечений функциональности
- Четкие интерфейсы между плагинами

### **Использование оптимизаций:**
- Ленивая обработка для пропуска ненужных этапов
- Кэширование для повторных операций
- Батчевая обработка для больших объемов
- Параллельная обработка для ускорения

---

## 🧪 **ТЕСТИРОВАНИЕ**

### **Интеграционные тесты:**
- Полный поток данных через PluginManager
- Корректность установки зависимостей
- Обработка ошибок

### **Тесты производительности:**
- Время выполнения операций
- Использование памяти
- Эффективность оптимизаций

### **Метрики производительности:**
- Время обработки батчей
- Эффективность кэширования
- Параллельная обработка
- Раннее отсечение

---

## 📊 **МОНИТОРИНГ**

### **Логирование:**
- Централизованное через LoggerPlugin
- Batch-логирование для больших объемов
- Структурированные логи

### **Метрики:**
- Время выполнения операций
- Использование ресурсов
- Статистика работы плагинов

---

## 🚀 **РАЗРАБОТКА**

### **Добавление плагина:**
1. Создать класс в соответствующей папке
2. Добавить в `src/plugins/__init__.py`
3. Настроить зависимости в PluginManager
4. Добавить тесты и оптимизации

### **Изменение архитектуры:**
1. Обновить документацию
2. Изменить зависимости
3. Обновить все файлы
4. Провести тестирование

---

## 📈 **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ**

### **Производительность (1000 постов):**
- **Без оптимизаций**: 5-10 сек, 50-100 МБ
- **С оптимизациями**: 2-5 сек, 20-50 МБ
- **Ускорение**: в 2-3 раза
- **Экономия памяти**: в 2-3 раза

---

## 🔄 **ИНТЕГРАЦИЯ СТАТИСТИКИ**

### **DatabasePlugin теперь включает:**
- **Хранение данных**: SQLite БД
- **Экспорт**: CSV/JSON форматы
- **Статистика**: интегрированная из StatsPlugin
- **Резервное копирование**: управление файлами

### **Удаленные плагины:**
- **DataManagerPlugin**: функциональность интегрирована в DatabasePlugin
- **StatsPlugin**: функциональность интегрирована в DatabasePlugin

---

**Версия:** 2.2 (с полной интеграцией)  
**Дата:** 27.07.2025  
**Статус:** Активная разработка с оптимизациями и интеграцией 