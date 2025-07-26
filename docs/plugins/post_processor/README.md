# 🔄 PostProcessorPlugin

## 📋 **ОПИСАНИЕ**

**PostProcessorPlugin** - центральный координатор обработки публикаций, управляющий цепочкой обработки данных: DeduplicationPlugin → TextProcessingPlugin → FilterPlugin.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Координация работы DeduplicationPlugin → TextProcessingPlugin → FilterPlugin
- Получение данных из DatabasePlugin через PluginManager
- Сохранение обработанных данных в DatabasePlugin через PluginManager
- Управление порядком обработки данных
- Оптимизация производительности обработки

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def process_posts(self, posts: List[Dict], keywords: List[str] = None, 
                 exact_match: bool = True, remove_duplicates: bool = True) -> List[Dict]:
    """Основная обработка постов"""

def process_posts_from_database(self, task_id: int, keywords: List[str] = None,
                              exact_match: bool = True) -> List[Dict]:
    """Обработка постов из базы данных"""

def get_statistics(self) -> Dict[str, Any]:
    """Получение статистики обработки"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

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

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Время обработки**: сокращение в 2-3 раза
- **Использование памяти**: сокращение в 2-3 раза
- **Ленивая обработка**: пропуск ненужных этапов
- **Раннее отсечение**: удаление дубликатов на первом этапе
- **Кэширование**: повторные операции мгновенно

## 🔗 **ЗАВИСИМОСТИ**

- **DeduplicationPlugin**: удаление дубликатов
- **TextProcessingPlugin**: очистка текста
- **FilterPlugin**: фильтрация по ключевым словам
- **DatabasePlugin**: получение и сохранение данных

## 🧪 **ТЕСТИРОВАНИЕ**

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

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация оптимизированных методов**
2. **Добавление метрик производительности**
3. **Интеграция с системой мониторинга**
4. **Оптимизация для больших объемов данных**
5. **Добавление конфигурации оптимизаций**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 