# 📋 АРХИТЕКТУРНАЯ ДОКУМЕНТАЦИЯ СИСТЕМЫ

## 🎯 **ОСНОВНЫЕ ПРИНЦИПЫ АРХИТЕКТУРЫ**

### **1. PluginManager как Центральное Ядро**
- **PluginManager** является единственным центром управления всеми плагинами
- Все плагины получают доступ к другим плагинам **ТОЛЬКО через PluginManager**
- Никаких прямых связей между плагинами не допускается
- Единообразная архитектура управления зависимостями

### **2. Правильная Иерархия Управления**
```
GUI → PluginManager → [Все плагины]
                ↓
            DatabasePlugin
                ↓
            PostProcessorPlugin
                ↓
        [DeduplicationPlugin → TextProcessingPlugin → FilterPlugin]
```

### **3. Оптимизированная Цепочка Обработки Данных**
```
PostProcessorPlugin → DatabasePlugin (получение данных)
    ↓
DeduplicationPlugin (удаление дубликатов по ссылкам)
    ↓
TextProcessingPlugin (очистка и подготовка текста)
    ↓
FilterPlugin (фильтрация по ключевым словам)
    ↓
PostProcessorPlugin (компиляция результатов)
    ↓
DatabasePlugin (сохранение через PluginManager)
```

### **4. Принцип Единой Точки Доступа**
- Все плагины получают другие плагины через `plugin_manager.get_plugin('plugin_name')`
- Централизованное управление жизненным циклом плагинов
- Единообразная система конфигурации и инициализации

---

## 🏗️ **СТРУКТУРА СИСТЕМЫ**

### **Ключевые Компоненты:**

#### **1. PluginManager (Ядро системы)**
- **Роль**: Центральный координатор всех плагинов
- **Ответственность**: 
  - Загрузка и инициализация плагинов
  - Управление зависимостями между плагинами
  - Предоставление доступа к плагинам через единый интерфейс
  - Управление жизненным циклом плагинов

#### **2. PostProcessorPlugin (Координатор обработки)**
- **Роль**: Центральный координатор обработки публикаций
- **Ответственность**:
  - Координация работы DeduplicationPlugin → TextProcessingPlugin → FilterPlugin
  - Получение данных из DatabasePlugin через PluginManager
  - Сохранение обработанных данных в DatabasePlugin через PluginManager
  - Управление порядком обработки данных
  - **Оптимизация**: Ленивая обработка, батчевая обработка, кэширование

#### **3. DatabasePlugin (Хранилище данных)**
- **Роль**: Единственное хранилище данных системы
- **Ответственность**:
  - Управление SQLite базой данных
  - Сохранение и извлечение задач парсинга
  - Сохранение и извлечение публикаций
  - Предоставление статистики и экспорта данных
  - **Подчиняется PluginManager**

#### **4. DeduplicationPlugin (Дедупликация)**
- **Роль**: Удаление дубликатов публикаций
- **Ответственность**:
  - Удаление дубликатов по хешу ссылок (link_hash)
  - Удаление дубликатов по хешу текста (text_hash)
  - Статистика дубликатов
  - **Управляется PostProcessorPlugin**
  - **Оптимизация**: Раннее отсечение дубликатов для снижения нагрузки

#### **5. TextProcessingPlugin (Обработка текста)**
- **Роль**: Очистка и нормализация текста
- **Ответственность**:
  - Удаление HTML-тегов, эмодзи, специальных символов
  - Нормализация пробелов и символов
  - Подготовка текста для анализа
  - **Управляется PostProcessorPlugin**
  - **Оптимизация**: Обработка только при необходимости фильтрации

#### **6. FilterPlugin (Фильтрация)**
- **Роль**: Фильтрация публикаций по ключевым словам
- **Ответственность**:
  - Фильтрация по точному и неточному совпадению
  - Работа с множественными ключевыми словами
  - **Управляется PostProcessorPlugin**
  - **Оптимизация**: Работа с предварительно очищенным текстом

#### **7. VKSearchPlugin (Поиск в ВК)**
- **Роль**: Поиск публикаций в ВКонтакте
- **Ответственность**:
  - Выполнение поисковых запросов к VK API
  - Обработка результатов поиска
  - Управление токенами через TokenManagerPlugin
  - **Подчиняется PluginManager**

#### **8. TokenManagerPlugin (Управление токенами)**
- **Роль**: Управление VK API токенами
- **Ответственность**:
  - Ротация токенов
  - Мониторинг лимитов API
  - Предоставление токенов VKSearchPlugin
  - **Подчиняется PluginManager**

---

## 🔄 **ОПТИМИЗИРОВАННЫЙ ПОТОК ДАННЫХ**

### **1. Парсинг данных:**
```
VKSearchPlugin → TokenManagerPlugin (через PluginManager)
VKSearchPlugin → DatabasePlugin (через PluginManager) - сохранение результатов
```

### **2. Обработка данных (оптимизированная цепочка):**
```
GUI → PluginManager → PostProcessorPlugin
PostProcessorPlugin → PluginManager → DatabasePlugin (получение данных)
    ↓
DeduplicationPlugin (удаление дубликатов по ссылкам)
    ↓
TextProcessingPlugin (очистка текста - только при необходимости)
    ↓
FilterPlugin (фильтрация по ключевым словам - только при наличии ключевых слов)
    ↓
PostProcessorPlugin (компиляция результатов)
    ↓
PluginManager → DatabasePlugin (сохранение результатов)
```

### **3. Экспорт данных:**
```
GUI → PluginManager → DatabasePlugin → CSV/JSON экспорт
```

---

## ⚡ **ОПТИМИЗАЦИОННЫЕ МЕРОПРИЯТИЯ**

### **1. Ленивая Обработка (Lazy Processing)**
```python
def process_posts_optimized(self, posts, keywords=None, exact_match=True, remove_duplicates=True):
    """Оптимизированная обработка с пропуском ненужных этапов"""
    
    # Шаг 1: Дедупликация (всегда выполняется)
    if remove_duplicates:
        posts = self.deduplication_plugin.remove_duplicates_by_link_hash(posts)
    
    # Шаг 2: Очистка текста (только если нужна фильтрация)
    if keywords:
        posts = self.text_processing_plugin.process_posts_text(posts)
    
    # Шаг 3: Фильтрация (только если есть ключевые слова)
    if keywords:
        posts = self.filter_plugin.filter_posts_by_multiple_keywords(posts, keywords, exact_match)
    
    return posts
```

### **2. Батчевая Обработка (Batch Processing)**
```python
def process_posts_in_batches(self, posts, batch_size=1000):
    """Обработка больших объемов данных батчами"""
    results = []
    
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        processed_batch = self.process_posts(batch)
        results.extend(processed_batch)
    
    return results
```

### **3. Кэширование Результатов (Caching)**
```python
def process_posts_with_cache(self, posts, keywords, exact_match=True):
    """Обработка с кэшированием промежуточных результатов"""
    
    cache_key = self._generate_cache_key(posts, keywords, exact_match)
    
    if cache_key in self.cache:
        return self.cache[cache_key]
    
    result = self.process_posts(posts, keywords, exact_match)
    self.cache[cache_key] = result
    
    return result
```

### **4. Параллельная Обработка (Parallel Processing)**
```python
async def process_posts_parallel(self, posts):
    """Параллельная обработка батчей"""
    batches = self._split_into_batches(posts, 100)
    
    tasks = []
    for batch in batches:
        task = self._process_batch(batch)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return self._merge_results(results)
```

### **5. Раннее Отсечение (Early Termination)**
```python
def process_posts_with_early_termination(self, posts, keywords, exact_match=True):
    """Обработка с ранним отсечением на каждом этапе"""
    
    # Шаг 1: Дедупликация (снижает объем данных)
    unique_posts = self.deduplication_plugin.remove_duplicates_by_link_hash(posts)
    self.log_info(f"После дедупликации: {len(unique_posts)} из {len(posts)}")
    
    # Шаг 2: Очистка текста (только если нужна фильтрация)
    if keywords:
        cleaned_posts = self.text_processing_plugin.process_posts_text(unique_posts)
        self.log_info(f"Очищено {len(cleaned_posts)} текстов")
    else:
        cleaned_posts = unique_posts  # Пропускаем очистку
    
    # Шаг 3: Фильтрация (только если есть ключевые слова)
    if keywords:
        filtered_posts = self.filter_plugin.filter_posts_by_multiple_keywords(
            cleaned_posts, keywords, exact_match
        )
        self.log_info(f"Отфильтровано: {len(filtered_posts)} из {len(cleaned_posts)}")
    else:
        filtered_posts = cleaned_posts  # Пропускаем фильтрацию
    
    return filtered_posts
```

---

## 🔧 **КОНФИГУРАЦИЯ И ИНИЦИАЛИЗАЦИЯ**

### **Порядок инициализации:**
1. **PluginManager** создается в MainInterface
2. **PluginManager** загружает все плагины
3. **PluginManager** устанавливает зависимости между плагинами
4. **PluginManager** инициализирует все плагины
5. GUI получает готовую систему плагинов

### **Установка зависимостей:**
```python
# PostProcessorPlugin получает PluginManager
post_processor.set_plugin_manager(plugin_manager)

# VKSearchPlugin получает TokenManagerPlugin через PluginManager
vk_plugin.set_token_manager(plugin_manager.get_plugin('token_manager'))

# DatabasePlugin подчиняется PluginManager (автоматически)
```

### **Конфигурация оптимизаций:**
```python
# PostProcessorPlugin конфигурация
{
    "enable_lazy_processing": True,
    "batch_size": 1000,
    "enable_caching": True,
    "cache_size": 1000,
    "enable_parallel_processing": True,
    "max_workers": 4,
    "processing_order": ["deduplication", "text_processing", "filtering"],
    "early_termination": True
}
```

---

## 📁 **СТРУКТУРА ПРОЕКТА**

```
src/
├── core/
│   ├── plugin_manager.py          # Центральное ядро
│   ├── config_manager.py          # Управление конфигурацией
│   ├── event_system.py           # Система событий
│   └── logger_utils.py           # Логирование
├── plugins/
│   ├── post_processor/           # Обработка публикаций
│   │   ├── post_processor_plugin.py  # Координатор (с оптимизациями)
│   │   ├── deduplication/
│   │   │   └── deduplication_plugin.py  # Дедупликация (раннее отсечение)
│   │   ├── text_processing/
│   │   │   └── text_processing_plugin.py  # Обработка текста (ленивая)
│   │   └── filter/
│   │       └── filter_plugin.py      # Фильтрация (оптимизированная)
│   ├── database/
│   │   └── database_plugin.py    # Хранилище данных
│   ├── vk_search/
│   │   └── vk_search_plugin.py   # Поиск в ВК
│   ├── token_manager/
│   │   └── token_manager_plugin.py  # Управление токенами
│   └── [другие плагины...]
└── gui/
    ├── main_interface.py         # Главный интерфейс
    ├── vk_parser_interface.py    # Интерфейс парсера
    └── [другие интерфейсы...]
```

---

## 🔗 **ПРИНЦИПЫ ИНТЕГРАЦИИ**

### **1. Единообразие доступа к плагинам:**
```python
# Правильно - через PluginManager
database_plugin = self.plugin_manager.get_plugin('database')

# Неправильно - прямая связь
self.database_plugin = database_plugin
```

### **2. Централизованное управление зависимостями:**
```python
# В PluginManager
def setup_plugin_dependencies(self):
    post_processor = self.get_plugin('post_processor')
    post_processor.set_plugin_manager(self)
```

### **3. Четкое разделение ответственности:**
- **PostProcessorPlugin**: координация обработки + оптимизации
- **DeduplicationPlugin**: только дедупликация + раннее отсечение
- **TextProcessingPlugin**: только обработка текста + ленивая обработка
- **FilterPlugin**: только фильтрация + работа с очищенным текстом
- **DatabasePlugin**: только хранение данных

---

## 🧪 **ТЕСТИРОВАНИЕ**

### **Интеграционные тесты:**
- Тестирование полного потока данных через PluginManager
- Проверка корректности установки зависимостей
- Тестирование обработки ошибок
- **Тестирование оптимизаций**: ленивая обработка, кэширование, батчевая обработка

### **Модульные тесты:**
- Тестирование каждого плагина изолированно
- Mock-объекты для PluginManager
- Тестирование граничных случаев
- **Тестирование производительности**: время выполнения, использование памяти

### **Тесты производительности:**
```python
def test_performance_optimizations():
    """Тест оптимизаций производительности"""
    
    # Тест ленивой обработки
    posts = generate_test_posts(1000)
    
    # Без ключевых слов - пропускаем очистку и фильтрацию
    start_time = time.time()
    result1 = post_processor.process_posts(posts, keywords=None)
    time1 = time.time() - start_time
    
    # С ключевыми словами - полная обработка
    start_time = time.time()
    result2 = post_processor.process_posts(posts, keywords=['тест'])
    time2 = time.time() - start_time
    
    # Время без обработки должно быть меньше
    assert time1 < time2
```

---

## 📊 **МОНИТОРИНГ И ЛОГИРОВАНИЕ**

### **Централизованное логирование:**
- Все плагины используют единую систему логирования
- Логирование через PluginManager
- Структурированные логи для анализа
- **Логирование оптимизаций**: время выполнения каждого этапа, количество обработанных записей

### **Мониторинг производительности:**
- Время выполнения операций
- Использование памяти
- Статистика работы плагинов
- **Метрики оптимизаций**: эффективность кэширования, размер батчей, параллельная обработка

### **Метрики производительности:**
```python
def get_performance_metrics(self):
    """Получение метрик производительности"""
    return {
        "processing_time": self.processing_time,
        "memory_usage": self.memory_usage,
        "cache_hit_rate": self.cache_hit_rate,
        "batch_efficiency": self.batch_efficiency,
        "parallel_processing_speedup": self.parallel_speedup
    }
```

---

## 🚀 **РАЗРАБОТКА И РАСШИРЕНИЕ**

### **Добавление нового плагина:**
1. Создать класс плагина в соответствующей папке
2. Добавить в `src/plugins/__init__.py`
3. Настроить зависимости в `PluginManager`
4. Добавить тесты
5. **Добавить оптимизации**: ленивая обработка, кэширование, батчевая обработка

### **Изменение архитектуры:**
1. Обновить документацию
2. Изменить зависимости в `PluginManager`
3. Обновить все затронутые файлы
4. Провести полное тестирование
5. **Проверить оптимизации**: производительность, использование ресурсов

### **Добавление новых оптимизаций:**
1. Реализовать оптимизацию в соответствующем плагине
2. Добавить конфигурацию
3. Добавить тесты производительности
4. Обновить документацию
5. Провести бенчмарки

---

## ⚠️ **ВАЖНЫЕ ПРИНЦИПЫ**

### **1. Никаких прямых связей между плагинами**
### **2. Все через PluginManager**
### **3. Четкое разделение ответственности**
### **4. Единообразная архитектура**
### **5. Централизованное управление**
### **6. Оптимизация производительности**
### **7. Ленивая обработка**
### **8. Кэширование результатов**

---

## 📈 **ПРЕИМУЩЕСТВА АРХИТЕКТУРЫ**

### **1. Масштабируемость:**
- Легко добавлять новые плагины
- Простая замена компонентов
- Гибкая конфигурация
- **Оптимизации**: батчевая обработка, параллельная обработка

### **2. Поддерживаемость:**
- Четкая структура кода
- Изолированные компоненты
- Простое отладка
- **Оптимизации**: ленивая обработка, кэширование

### **3. Тестируемость:**
- Изолированное тестирование плагинов
- Mock-объекты для зависимостей
- Автоматизированные тесты
- **Тесты производительности**: бенчмарки, профилирование

### **4. Надежность:**
- Централизованная обработка ошибок
- Единообразное логирование
- Предсказуемое поведение
- **Оптимизации**: раннее отсечение, обработка ошибок

### **5. Производительность:**
- Ленивая обработка (пропуск ненужных этапов)
- Кэширование результатов
- Батчевая обработка больших объемов
- Параллельная обработка
- Раннее отсечение дубликатов

---

## 🎯 **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ ОПТИМИЗАЦИЙ**

### **Для 1000 постов:**

#### **Без оптимизаций:**
- Время обработки: ~5-10 секунд
- Использование памяти: ~50-100 МБ
- Все записи обрабатываются полностью

#### **С оптимизациями:**
- Время обработки: ~2-5 секунд (в 2-3 раза быстрее)
- Использование памяти: ~20-50 МБ (в 2-3 раза меньше)
- Ленивая обработка: пропуск ненужных этапов
- Раннее отсечение: удаление дубликатов на первом этапе
- Кэширование: повторные операции мгновенно

---

**Версия:** 2.1 (с оптимизациями)  
**Дата:** 27.07.2025  
**Статус:** Активная разработка с оптимизациями 