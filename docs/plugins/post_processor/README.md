# PostProcessorPlugin

Центральный плагин для обработки публикаций ВКонтакте. Координирует работу фильтрации, дедупликации и обработки текста.

## Архитектура

PostProcessorPlugin является фасадом для трех подплагинов:
- **DeduplicationPlugin** - удаление дубликатов по ссылкам
- **TextProcessingPlugin** - очистка и нормализация текста
- **FilterPlugin** - фильтрация по ключевым словам

## Основные методы

### process_posts()
Стандартная обработка публикаций с полным циклом.

```python
result = post_processor.process_posts(
    posts=raw_posts,
    keywords=['keyword1', 'keyword2'],
    exact_match=True
)
```

## Оптимизированные методы

### 1. process_posts_optimized()
**Высокопроизводительная обработка с ленивой загрузкой**

```python
result = post_processor.process_posts_optimized(
    posts=posts,
    keywords=keywords,
    exact_match=True,
    early_termination=True,    # Ранний выход при лимите 5000 постов
    lazy_processing=True       # Обработка только потенциально подходящих постов
)
```

**Особенности:**
- ⚡ **Ленивая обработка**: текст обрабатывается только у постов с потенциально подходящими ключевыми словами
- 🛑 **Ранний выход**: автоматическое прерывание при достижении 5000 уникальных постов
- 🔍 **Быстрая предфильтрация**: проверка только первых 3 ключевых слов для ускорения
- 📊 **Детальная статистика**: количество пропущенных постов, время экономии

### 2. process_posts_in_batches()
**Батчевая обработка для больших объёмов**

```python
result = post_processor.process_posts_in_batches(
    posts=large_dataset,
    keywords=keywords,
    exact_match=True,
    batch_size=1000           # Размер батча (по умолчанию из конфига)
)
```

**Особенности:**
- 📦 **Батчевая обработка**: разбивка данных на управляемые порции
- 🔄 **Прогресс-мониторинг**: отчёт о прогрессе каждые 5 батчей
- 🔗 **Финальная дедупликация**: удаление дубликатов между батчами
- 💾 **Контроль памяти**: обработка по частям для больших датасетов

### 3. process_posts_with_cache()
**Обработка с кэшированием результатов**

```python
result = post_processor.process_posts_with_cache(
    posts=posts,
    keywords=keywords,
    exact_match=True,
    cache_results=True        # Сохранять результаты в кэш
)
```

**Особенности:**
- 💾 **Кэширование текста**: сохранение результатов очистки текста
- 🔍 **Кэширование фильтрации**: сохранение результатов проверки ключевых слов
- 🔗 **Кэширование дедупликации**: запоминание известных дубликатов
- 📈 **Метрики эффективности**: процент попаданий в кэш

### 4. process_posts_parallel()
**Параллельная многопоточная обработка**

```python
result = post_processor.process_posts_parallel(
    posts=posts,
    keywords=keywords,
    exact_match=True,
    max_workers=4            # Количество потоков (автоматически адаптируется)
)
```

**Особенности:**
- ⚡ **Многопоточность**: использование `ThreadPoolExecutor`
- 🧩 **Адаптивные чанки**: автоматическое разбиение на оптимальные порции
- 🔄 **Мониторинг прогресса**: отслеживание завершения потоков
- 🔗 **Финальная синхронизация**: дедупликация между потоками

## Сравнение производительности

| Метод | Время | Память | Лучший случай использования |
|-------|-------|--------|------------------------------|
| `process_posts()` | Базовое | Низкое | < 10,000 постов, стандартная обработка |
| `process_posts_optimized()` | **-30-50%** | Низкое | Любой размер, максимальная скорость |
| `process_posts_in_batches()` | +10-20% | **Очень низкое** | > 50,000 постов, ограниченная память |
| `process_posts_with_cache()` | **-60-80%** ² | Среднее | Повторяющиеся данные |
| `process_posts_parallel()` | **-40-70%** | Высокое | > 20,000 постов, многоядерный CPU |

² - При высоком проценте попаданий в кэш

## Рекомендации по использованию

### Выбор метода по объёму данных:
- **< 1,000 постов**: `process_posts()` (стандартный)
- **1,000 - 10,000 постов**: `process_posts_optimized()`
- **10,000 - 50,000 постов**: `process_posts_parallel()`
- **> 50,000 постов**: `process_posts_in_batches()`
- **Повторяющиеся данные**: `process_posts_with_cache()`

### Конфигурация производительности:

```python
# Высокая производительность
config = {
    "batch_size": 2000,           # Больше батчи для больших данных
    "enable_logging": False,      # Отключить детальное логирование
    "processing_order": ["deduplication", "text_processing", "filtering"]
}

# Экономия памяти
config = {
    "batch_size": 500,            # Меньше батчи
    "enable_logging": True,       # Мониторинг прогресса
}
```

## Конфигурация

```python
default_config = {
    "enable_filtering": True,
    "enable_deduplication": True,
    "filter_method": "keywords",
    "deduplication_method": "link_hash",
    "processing_order": ["deduplication", "text_processing", "filtering"],
    "batch_size": 1000,           # Размер батча для батчевой обработки
    "enable_logging": True,
    "cache_size_limit": 10000,    # Лимит элементов в кэше
    "parallel_threshold": 5000,   # Минимум постов для параллельной обработки
    "early_termination_limit": 5000  # Лимит для раннего выхода
}
```

## Мониторинг производительности

### Кэш-статистика:
```python
cache_stats = post_processor.get_cache_stats()
# {
#     "cache_enabled": True,
#     "text_cache_size": 1500,
#     "filter_cache_size": 800,
#     "duplicates_cache_size": 3200,
#     "total_memory_items": 5500
# }
```

### Очистка кэша:
```python
post_processor.clear_cache()  # Освобождение памяти
```

## Результат обработки

Все методы возвращают унифицированную структуру:

```python
{
    "original_count": 10000,        # Исходное количество
    "final_count": 2500,            # Финальное количество
    "duplicates_removed": 3000,     # Удалено дубликатов
    "text_processed": 7000,         # Обработано текстов
    "filtered_count": 4500,         # Отфильтровано постов
    "processing_time": 1.25,        # Время обработки (сек)
    "optimization_level": "high",   # Уровень оптимизации
    "final_posts": [...],           # Обработанные посты

    # Дополнительные метрики (зависят от метода)
    "cache_hits": {...},            # Статистика кэша
    "cache_efficiency": 85.2,       # Эффективность кэша (%)
    "early_exit": False,            # Был ли ранний выход
    "lazy_skips": 1200,             # Пропущено постов при ленивой обработке
    "batches_processed": 10,        # Количество обработанных батчей
    "threads_used": 4,              # Использовано потоков
    "cross_thread_duplicates": 50   # Дубликаты между потоками
}
```

## Интеграция с PluginManager

```python
# Получение плагина
post_processor = plugin_manager.get_plugin("post_processor")

# Автоматический выбор оптимального метода
if len(posts) > 50000:
    result = post_processor.process_posts_in_batches(posts, keywords)
elif len(posts) > 10000:
    result = post_processor.process_posts_parallel(posts, keywords)
else:
    result = post_processor.process_posts_optimized(posts, keywords)
```

## Архитектурная роль

- **Координация**: Управляет тремя подплагинами обработки
- **Оптимизация**: Предоставляет различные стратегии обработки
- **Кэширование**: Сохраняет результаты для повторного использования
- **Мониторинг**: Детальная статистика и метрики производительности
- **Масштабируемость**: Поддержка от малых до очень больших датасетов
