# 🔍 VKSearchPlugin

## 📋 **ОПИСАНИЕ**

**VKSearchPlugin** - плагин для поиска публикаций в ВКонтакте через VK API. Выполняет поисковые запросы, обрабатывает результаты и управляет токенами через TokenManagerPlugin.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Выполнение поисковых запросов к VK API
- Обработка результатов поиска
- Управление токенами через TokenManagerPlugin
- Обработка ошибок и лимитов API
- Подчиняется PluginManager

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def mass_search_with_tokens(self, keyword_token_pairs: List[Tuple[str, str]], 
                          start_date: str, end_date: str, exact_match: bool = True,
                          minus_words: List[str] = None) -> List[Dict]:
    """Массовый поиск с использованием токенов"""

def search_with_single_token(self, keyword: str, token: str, start_date: str,
                           end_date: str, exact_match: bool = True) -> List[Dict]:
    """Поиск с одним токеном"""

def get_statistics(self) -> Dict[str, Any]:
    """Получение статистики поиска"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

### **1. Параллельная Обработка Запросов**
```python
async def mass_search_parallel(self, keyword_token_pairs: List[Tuple[str, str]], 
                             start_date: str, end_date: str, exact_match: bool = True,
                             minus_words: List[str] = None, max_concurrent=5) -> List[Dict]:
    """Параллельный массовый поиск с ограничением одновременных запросов"""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def search_with_semaphore(keyword: str, token: str):
        async with semaphore:
            return await self._search_async(keyword, token, start_date, end_date, exact_match, minus_words)
    
    tasks = []
    for keyword, token in keyword_token_pairs:
        task = search_with_semaphore(keyword, token)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Объединение результатов
    all_posts = []
    for result in results:
        if isinstance(result, list):
            all_posts.extend(result)
        else:
            self.log_error(f"Ошибка поиска: {result}")
    
    return all_posts
```

### **2. Умное Кэширование Результатов**
```python
def search_with_cache(self, keyword: str, token: str, start_date: str, end_date: str,
                     exact_match: bool = True, cache_ttl=3600) -> List[Dict]:
    """Поиск с кэшированием результатов"""
    
    cache_key = self._generate_cache_key(keyword, token, start_date, end_date, exact_match)
    
    # Проверка кэша
    if cache_key in self.search_cache:
        cache_entry = self.search_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < cache_ttl:
            self.log_info(f"Результат найден в кэше для ключа: {keyword}")
            return cache_entry['data']
    
    # Выполнение поиска
    result = self.search_with_single_token(keyword, token, start_date, end_date, exact_match)
    
    # Сохранение в кэш
    self.search_cache[cache_key] = {
        'data': result,
        'timestamp': time.time()
    }
    
    return result
```

### **3. Адаптивная Ротация Токенов**
```python
def adaptive_token_rotation(self, keyword_token_pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Адаптивная ротация токенов на основе их производительности"""
    
    # Анализ производительности токенов
    token_performance = {}
    for token in set(token for _, token in keyword_token_pairs):
        performance = self._analyze_token_performance(token)
        token_performance[token] = performance
    
    # Сортировка токенов по производительности
    sorted_tokens = sorted(token_performance.items(), key=lambda x: x[1], reverse=True)
    
    # Перераспределение ключевых слов
    optimized_pairs = []
    token_index = 0
    
    for keyword, _ in keyword_token_pairs:
        if token_index >= len(sorted_tokens):
            token_index = 0
        
        optimized_pairs.append((keyword, sorted_tokens[token_index][0]))
        token_index += 1
    
    return optimized_pairs
```

### **4. Батчевая Обработка Результатов**
```python
def process_results_in_batches(self, raw_results: List[Dict], batch_size=100) -> List[Dict]:
    """Батчевая обработка результатов поиска"""
    
    processed_results = []
    
    for i in range(0, len(raw_results), batch_size):
        batch = raw_results[i:i + batch_size]
        
        # Параллельная обработка батча
        processed_batch = self._process_batch_parallel(batch)
        processed_results.extend(processed_batch)
        
        self.log_info(f"Обработано {len(processed_results)} из {len(raw_results)} результатов")
    
    return processed_results

def _process_batch_parallel(self, batch: List[Dict]) -> List[Dict]:
    """Параллельная обработка батча результатов"""
    
    def process_single_result(result: Dict) -> Dict:
        # Очистка и нормализация данных
        processed = {
            'vk_id': result.get('id'),
            'title': result.get('title', ''),
            'content': self._clean_content(result.get('text', '')),
            'author_id': result.get('owner_id'),
            'author_name': result.get('owner_name', ''),
            'likes': result.get('likes', {}).get('count', 0),
            'comments': result.get('comments', {}).get('count', 0),
            'reposts': result.get('reposts', {}).get('count', 0),
            'views': result.get('views', {}).get('count', 0),
            'link': f"https://vk.com/wall{result.get('owner_id')}_{result.get('id')}",
            'created_date': result.get('date')
        }
        return processed
    
    # Параллельная обработка
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        processed_batch = list(executor.map(process_single_result, batch))
    
    return processed_batch
```

### **5. Умная Обработка Ошибок**
```python
def smart_error_handling(self, keyword: str, token: str, max_retries=3):
    """Умная обработка ошибок с автоматическими повторами"""
    
    for attempt in range(max_retries):
        try:
            result = self._make_api_request(keyword, token)
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            
            if error_type == 'RateLimitError':
                # Ожидание при превышении лимитов
                wait_time = self._calculate_wait_time(attempt)
                self.log_warning(f"Превышен лимит API, ожидание {wait_time} секунд")
                time.sleep(wait_time)
                
            elif error_type == 'TokenExpiredError':
                # Замена токена
                new_token = self.token_manager.get_next_token()
                self.log_info(f"Токен истек, заменен на новый")
                token = new_token
                
            elif error_type == 'NetworkError':
                # Повтор при сетевых ошибках
                wait_time = 2 ** attempt
                self.log_warning(f"Сетевая ошибка, повтор через {wait_time} секунд")
                time.sleep(wait_time)
                
            else:
                # Неизвестная ошибка
                self.log_error(f"Неизвестная ошибка: {e}")
                break
    
    return []
```

### **6. Оптимизация Запросов**
```python
def optimize_search_queries(self, keywords: List[str]) -> List[str]:
    """Оптимизация поисковых запросов"""
    
    optimized_keywords = []
    
    for keyword in keywords:
        # Удаление лишних пробелов
        cleaned = ' '.join(keyword.split())
        
        # Добавление кавычек для точного поиска
        if ' ' in cleaned:
            optimized = f'"{cleaned}"'
        else:
            optimized = cleaned
        
        # Исключение слишком коротких запросов
        if len(cleaned) >= 3:
            optimized_keywords.append(optimized)
    
    return optimized_keywords
```

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Скорость поиска**: увеличение в 3-5 раз (параллельная обработка)
- **Эффективность токенов**: увеличение в 2-3 раза (адаптивная ротация)
- **Кэширование**: 70-80% повторных запросов из кэша
- **Обработка ошибок**: снижение количества неудачных запросов на 50%
- **Батчевая обработка**: ускорение обработки больших объемов в 2-3 раза

## 🔗 **ЗАВИСИМОСТИ**

- **PluginManager**: управление плагином
- **TokenManagerPlugin**: получение и управление токенами
- **DatabasePlugin**: сохранение результатов поиска

## 🧪 **ТЕСТИРОВАНИЕ**

```python
def test_search_performance():
    """Тест производительности поиска"""
    
    keywords = ['тест', 'новости', 'технологии']
    tokens = ['token1', 'token2', 'token3']
    
    # Тест параллельного поиска
    start_time = time.time()
    result1 = vk_plugin.mass_search_parallel(keyword_token_pairs, start_date, end_date)
    time1 = time.time() - start_time
    
    # Тест последовательного поиска
    start_time = time.time()
    result2 = vk_plugin.mass_search_with_tokens(keyword_token_pairs, start_date, end_date)
    time2 = time.time() - start_time
    
    # Параллельный поиск должен быть быстрее
    assert time1 < time2
```

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация параллельной обработки запросов**
2. **Добавление кэширования результатов**
3. **Реализация адаптивной ротации токенов**
4. **Добавление батчевой обработки результатов**
5. **Улучшение обработки ошибок**
6. **Оптимизация поисковых запросов**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 