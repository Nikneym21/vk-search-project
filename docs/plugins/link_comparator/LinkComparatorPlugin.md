# 🔗 LinkComparatorPlugin

## 📋 **ОПИСАНИЕ**

**LinkComparatorPlugin** - плагин для сравнения ссылок между таблицами. Извлекает ссылки из текста, сравнивает их между таблицами и генерирует отчеты о различиях.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Загрузка таблиц для сравнения
- Извлечение ссылок из текста
- Сравнение ссылок между таблицами
- Генерация отчетов о различиях
- Подчиняется PluginManager

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def load_tables(self, table1_path: str, table2_path: str) -> bool:
    """Загрузка таблиц для сравнения"""

def extract_links(self, text: str) -> List[str]:
    """Извлечение ссылок из текста"""

def compare_links(self, links1: List[str], links2: List[str]) -> Dict[str, Any]:
    """Сравнение ссылок между таблицами"""

def get_statistics(self) -> Dict[str, Any]:
    """Получение статистики сравнения"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

### **1. Параллельная Обработка Таблиц**
```python
async def compare_tables_parallel(self, table1_path: str, table2_path: str) -> Dict[str, Any]:
    """Параллельное сравнение таблиц для улучшения производительности"""
    
    # Параллельная загрузка таблиц
    tasks = [
        self._load_table_async(table1_path),
        self._load_table_async(table2_path)
    ]
    
    table1_data, table2_data = await asyncio.gather(*tasks)
    
    # Параллельное извлечение ссылок
    tasks = [
        self._extract_links_parallel(table1_data),
        self._extract_links_parallel(table2_data)
    ]
    
    links1, links2 = await asyncio.gather(*tasks)
    
    # Сравнение ссылок
    comparison_result = self.compare_links(links1, links2)
    
    return comparison_result

async def _load_table_async(self, table_path: str) -> List[Dict]:
    """Асинхронная загрузка таблицы"""
    
    loop = asyncio.get_event_loop()
    
    def load_sync():
        return self._load_table_sync(table_path)
    
    return await loop.run_in_executor(None, load_sync)

async def _extract_links_parallel(self, data: List[Dict]) -> List[str]:
    """Параллельное извлечение ссылок"""
    
    # Разделение данных на батчи
    batch_size = 100
    batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
    
    tasks = []
    for batch in batches:
        task = self._extract_links_batch(batch)
        tasks.append(task)
    
    # Параллельное выполнение
    batch_results = await asyncio.gather(*tasks)
    
    # Объединение результатов
    all_links = []
    for batch_links in batch_results:
        all_links.extend(batch_links)
    
    return all_links
```

### **2. Умное Извлечение Ссылок**
```python
def smart_link_extraction(self, text: str) -> List[str]:
    """Умное извлечение ссылок с оптимизацией"""
    
    # Кэширование результатов
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_key = f"links_{text_hash}"
    
    if cache_key in self.link_cache:
        return self.link_cache[cache_key]
    
    # Регулярные выражения для разных типов ссылок
    link_patterns = [
        r'https?://[^\s<>"]+',  # HTTP/HTTPS ссылки
        r'vk\.com/[^\s<>"]+',   # VK ссылки
        r'www\.[^\s<>"]+',      # WWW ссылки
        r't\.me/[^\s<>"]+',     # Telegram ссылки
        r'instagram\.com/[^\s<>"]+',  # Instagram ссылки
    ]
    
    extracted_links = []
    
    for pattern in link_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        extracted_links.extend(matches)
    
    # Нормализация ссылок
    normalized_links = []
    for link in extracted_links:
        normalized = self._normalize_link(link)
        if normalized and normalized not in normalized_links:
            normalized_links.append(normalized)
    
    # Кэширование результата
    self.link_cache[cache_key] = normalized_links
    
    return normalized_links

def _normalize_link(self, link: str) -> str:
    """Нормализация ссылки"""
    
    # Удаление лишних символов
    link = link.strip()
    
    # Добавление протокола если отсутствует
    if not link.startswith(('http://', 'https://')):
        link = 'https://' + link
    
    # Удаление параметров отслеживания
    link = re.sub(r'[?&](utm_|ref=|source=)[^&]*', '', link)
    
    # Удаление якоря
    link = re.sub(r'#.*$', '', link)
    
    return link
```

### **3. Оптимизированное Сравнение**
```python
def optimized_link_comparison(self, links1: List[str], links2: List[str]) -> Dict[str, Any]:
    """Оптимизированное сравнение ссылок"""
    
    # Создание множеств для быстрого поиска
    set1 = set(links1)
    set2 = set(links2)
    
    # Быстрые операции с множествами
    common_links = set1 & set2
    unique_to_table1 = set1 - set2
    unique_to_table2 = set2 - set1
    
    # Детальное сравнение для общих ссылок
    detailed_comparison = {}
    for link in common_links:
        # Поиск контекста ссылок
        context1 = self._find_link_context(link, links1)
        context2 = self._find_link_context(link, links2)
        
        detailed_comparison[link] = {
            'table1_context': context1,
            'table2_context': context2,
            'context_different': context1 != context2
        }
    
    return {
        'common_links': list(common_links),
        'unique_to_table1': list(unique_to_table1),
        'unique_to_table2': list(unique_to_table2),
        'detailed_comparison': detailed_comparison,
        'statistics': {
            'total_table1': len(set1),
            'total_table2': len(set2),
            'common_count': len(common_links),
            'unique_table1_count': len(unique_to_table1),
            'unique_table2_count': len(unique_to_table2)
        }
    }

def _find_link_context(self, link: str, all_links: List[str]) -> Dict[str, Any]:
    """Поиск контекста ссылки"""
    
    # Поиск индексов вхождения
    indices = [i for i, l in enumerate(all_links) if l == link]
    
    return {
        'occurrence_count': len(indices),
        'first_occurrence': indices[0] if indices else None,
        'last_occurrence': indices[-1] if indices else None
    }
```

### **4. Кэширование Результатов**
```python
def compare_with_cache(self, table1_path: str, table2_path: str, 
                      force_refresh=False) -> Dict[str, Any]:
    """Сравнение с кэшированием результатов"""
    
    # Генерация ключа кэша
    cache_key = self._generate_cache_key(table1_path, table2_path)
    
    # Проверка кэша
    if not force_refresh and cache_key in self.comparison_cache:
        cache_entry = self.comparison_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < 3600:  # 1 час
            self.log_info("Результат сравнения найден в кэше")
            return cache_entry['data']
    
    # Выполнение сравнения
    result = self.compare_tables(table1_path, table2_path)
    
    # Кэширование результата
    self.comparison_cache[cache_key] = {
        'data': result,
        'timestamp': time.time()
    }
    
    return result

def _generate_cache_key(self, table1_path: str, table2_path: str) -> str:
    """Генерация ключа кэша"""
    
    # Использование хеша путей и времени модификации файлов
    stat1 = os.stat(table1_path)
    stat2 = os.stat(table2_path)
    
    key_data = f"{table1_path}_{stat1.st_mtime}_{table2_path}_{stat2.st_mtime}"
    return hashlib.md5(key_data.encode()).hexdigest()
```

### **5. Инкрементальное Сравнение**
```python
def incremental_comparison(self, table1_path: str, table2_path: str,
                          previous_result: Dict[str, Any] = None) -> Dict[str, Any]:
    """Инкрементальное сравнение для больших таблиц"""
    
    if not previous_result:
        # Полное сравнение при первом запуске
        return self.compare_tables(table1_path, table2_path)
    
    # Загрузка только новых данных
    new_data1 = self._get_new_data(table1_path, previous_result.get('table1_last_modified'))
    new_data2 = self._get_new_data(table2_path, previous_result.get('table2_last_modified'))
    
    if not new_data1 and not new_data2:
        # Нет изменений
        return previous_result
    
    # Извлечение ссылок только из новых данных
    new_links1 = self.extract_links_from_data(new_data1)
    new_links2 = self.extract_links_from_data(new_data2)
    
    # Обновление результата
    updated_result = self._update_comparison_result(
        previous_result, new_links1, new_links2
    )
    
    return updated_result

def _get_new_data(self, table_path: str, last_modified: float) -> List[Dict]:
    """Получение новых данных с момента последнего сравнения"""
    
    current_modified = os.path.getmtime(table_path)
    
    if last_modified and current_modified <= last_modified:
        return []  # Нет изменений
    
    # Загрузка только новых записей (упрощенная логика)
    return self._load_table_sync(table_path)
```

### **6. Мониторинг Производительности**
```python
def performance_monitoring(self) -> Dict[str, Any]:
    """Мониторинг производительности сравнения"""
    
    monitoring_data = {
        'total_comparisons': 0,
        'average_comparison_time': 0,
        'cache_hit_rate': 0,
        'parallel_processing_usage': 0,
        'memory_usage': 0,
        'link_extraction_efficiency': 0
    }
    
    # Статистика сравнений
    for comparison in self.comparison_history:
        monitoring_data['total_comparisons'] += 1
        monitoring_data['average_comparison_time'] += comparison.get('duration', 0)
    
    # Расчет средних значений
    if monitoring_data['total_comparisons'] > 0:
        monitoring_data['average_comparison_time'] /= monitoring_data['total_comparisons']
    
    # Статистика кэша
    cache_hits = len(self.comparison_cache)
    cache_misses = len(self.comparison_history) - cache_hits
    if cache_hits + cache_misses > 0:
        monitoring_data['cache_hit_rate'] = (cache_hits / (cache_hits + cache_misses)) * 100
    
    # Использование параллельной обработки
    parallel_count = sum(1 for c in self.comparison_history if c.get('parallel', False))
    if monitoring_data['total_comparisons'] > 0:
        monitoring_data['parallel_processing_usage'] = (parallel_count / 
                                                      monitoring_data['total_comparisons']) * 100
    
    return monitoring_data
```

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Скорость сравнения**: увеличение в 3-5 раз (параллельная обработка)
- **Кэширование**: 80-90% повторных сравнений из кэша
- **Извлечение ссылок**: ускорение в 2-3 раза (умное извлечение)
- **Инкрементальное сравнение**: снижение времени на 70% для больших таблиц
- **Память**: оптимизация использования памяти на 40%

## 🔗 **ЗАВИСИМОСТИ**

- **PluginManager**: управление плагином
- **DatabasePlugin**: получение данных для сравнения
- **MonitoringPlugin**: передача метрик производительности

## 🧪 **ТЕСТИРОВАНИЕ**

```python
def test_comparison_performance():
    """Тест производительности сравнения"""
    
    # Генерация тестовых данных
    table1_data = generate_test_table(10000)
    table2_data = generate_test_table(10000)
    
    # Тест параллельного сравнения
    start_time = time.time()
    result1 = comparator.compare_tables_parallel(table1_path, table2_path)
    time1 = time.time() - start_time
    
    # Тест последовательного сравнения
    start_time = time.time()
    result2 = comparator.compare_tables(table1_path, table2_path)
    time2 = time.time() - start_time
    
    # Параллельное сравнение должно быть быстрее
    assert time1 < time2
```

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация параллельной обработки таблиц**
2. **Добавление умного извлечения ссылок**
3. **Реализация оптимизированного сравнения**
4. **Добавление кэширования результатов**
5. **Реализация инкрементального сравнения**
6. **Добавление мониторинга производительности**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 