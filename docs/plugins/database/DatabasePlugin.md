# 🗄️ DatabasePlugin

## 📋 **ОПИСАНИЕ**

**DatabasePlugin** - расширенное хранилище данных системы с интегрированной статистикой. Управляет SQLite базой данных, экспортом данных и подсчетом статистики.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Управление SQLite базой данных
- Сохранение и извлечение задач парсинга
- Сохранение и извлечение публикаций
- Экспорт данных в CSV/JSON форматы
- **Интегрированная статистика**: подсчет лайков, комментариев, репостов, просмотров, SI
- Управление резервными копиями
- Подчиняется PluginManager

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def create_task(self, task_name: str, keywords: List[str], start_date: str = None,
                end_date: str = None, exact_match: bool = True, minus_words: List[str] = None) -> int:
    """Создание новой задачи парсинга"""

def save_posts(self, task_id: int, posts: List[Dict]) -> int:
    """Сохранение постов в базу данных"""

def get_task_statistics(self, task_id: int) -> Dict:
    """Получение статистики задачи"""

def export_task_to_csv(self, task_id: int, output_path: str) -> bool:
    """Экспорт задачи в CSV"""

def calculate_posts_statistics(self, posts: List[Dict]) -> Dict:
    """Подсчет статистики для списка постов (интегрировано из StatsPlugin)"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

### **1. Индексирование Базы Данных**
```python
def optimize_database_performance(self):
    """Оптимизация производительности БД"""
    
    cursor = self.connection.cursor()
    
    # Создание индексов для ускорения запросов
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_task_id ON posts(task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_link_hash ON posts(link_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_text_hash ON posts(text_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created_date ON posts(created_date)')
    
    # Анализ и оптимизация таблиц
    cursor.execute('ANALYZE')
    
    self.connection.commit()
    self.log_info("База данных оптимизирована")
```

### **2. Батчевая Запись (Batch Insert)**
```python
def save_posts_batch(self, task_id: int, posts: List[Dict], batch_size=1000) -> int:
    """Батчевое сохранение постов для улучшения производительности"""
    
    cursor = self.connection.cursor()
    total_saved = 0
    
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        
        # Подготовка данных для батчевой вставки
        batch_data = []
        for post in batch:
            batch_data.append((
                task_id,
                post.get('vk_id'),
                post.get('title', ''),
                post.get('content', ''),
                post.get('author_id'),
                post.get('author_name', ''),
                post.get('likes', 0),
                post.get('comments', 0),
                post.get('reposts', 0),
                post.get('views', 0),
                post.get('link', ''),
                self._calculate_link_hash(post.get('link', '')),
                self._calculate_text_hash(post.get('content', '')),
                post.get('created_date')
            ))
        
        # Батчевая вставка
        cursor.executemany('''
            INSERT INTO posts (task_id, vk_id, title, content, author_id, author_name,
                             likes, comments, reposts, views, link, link_hash, text_hash, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data)
        
        total_saved += len(batch)
        self.log_info(f"Сохранено {total_saved} постов из {len(posts)}")
    
    self.connection.commit()
    self._update_task_statistics(task_id)
    
    return total_saved
```

### **3. Кэширование Статистики**
```python
def get_task_statistics_cached(self, task_id: int, force_refresh=False) -> Dict:
    """Получение статистики задачи с кэшированием"""
    
    cache_key = f"task_stats_{task_id}"
    
    if not force_refresh and cache_key in self.stats_cache:
        return self.stats_cache[cache_key]
    
    # Получение статистики из БД
    cursor = self.connection.cursor()
    cursor.execute('''
        SELECT total_posts, total_likes, total_comments, total_reposts, total_views, total_SI
        FROM tasks WHERE id = ?
    ''', (task_id,))
    
    result = cursor.fetchone()
    if result:
        stats = {
            'total_posts': result[0],
            'total_likes': result[1],
            'total_comments': result[2],
            'total_reposts': result[3],
            'total_views': result[4],
            'total_SI': result[5]
        }
        
        # Кэширование результата
        self.stats_cache[cache_key] = stats
        return stats
    
    return {}
```

### **4. Асинхронная Обработка**
```python
async def save_posts_async(self, task_id: int, posts: List[Dict]) -> int:
    """Асинхронное сохранение постов"""
    
    # Разделение на батчи для параллельной обработки
    batches = [posts[i:i + 1000] for i in range(0, len(posts), 1000)]
    
    tasks = []
    for batch in batches:
        task = self._save_batch_async(task_id, batch)
        tasks.append(task)
    
    # Параллельное выполнение
    results = await asyncio.gather(*tasks)
    
    total_saved = sum(results)
    self._update_task_statistics(task_id)
    
    return total_saved

async def _save_batch_async(self, task_id: int, batch: List[Dict]) -> int:
    """Асинхронное сохранение батча"""
    # Реализация асинхронного сохранения
    return len(batch)
```

### **5. Сжатие Данных**
```python
def compress_database(self):
    """Сжатие базы данных для экономии места"""
    
    cursor = self.connection.cursor()
    
    # Включение WAL режима для лучшей производительности
    cursor.execute('PRAGMA journal_mode=WAL')
    
    # Оптимизация размера БД
    cursor.execute('VACUUM')
    
    # Сжатие индексов
    cursor.execute('REINDEX')
    
    self.connection.commit()
    self.log_info("База данных сжата и оптимизирована")
```

### **6. Умная Очистка**
```python
def smart_cleanup(self, days_to_keep=30):
    """Умная очистка старых данных"""
    
    cursor = self.connection.cursor()
    
    # Удаление старых задач и постов
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    cursor.execute('''
        DELETE FROM posts WHERE task_id IN (
            SELECT id FROM tasks WHERE created_at < ?
        )
    ''', (cutoff_date,))
    
    cursor.execute('DELETE FROM tasks WHERE created_at < ?', (cutoff_date,))
    
    # Сжатие БД после очистки
    cursor.execute('VACUUM')
    
    self.connection.commit()
    self.log_info(f"Очищены данные старше {days_to_keep} дней")
```

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Скорость записи**: увеличение в 3-5 раз (батчевая запись)
- **Скорость чтения**: увеличение в 2-3 раза (индексы)
- **Размер БД**: сокращение на 20-30% (сжатие)
- **Кэширование**: мгновенный доступ к статистике
- **Асинхронность**: параллельная обработка больших объемов

## 🔗 **ЗАВИСИМОСТИ**

- **PluginManager**: управление плагином
- **PostProcessorPlugin**: получение обработанных данных
- **VKSearchPlugin**: сохранение результатов поиска

## 🧪 **ТЕСТИРОВАНИЕ**

```python
def test_database_performance():
    """Тест производительности базы данных"""
    
    # Тест батчевой записи
    posts = generate_test_posts(10000)
    
    start_time = time.time()
    result1 = database_plugin.save_posts_batch(task_id, posts)
    time1 = time.time() - start_time
    
    # Тест обычной записи
    start_time = time.time()
    result2 = database_plugin.save_posts(task_id, posts)
    time2 = time.time() - start_time
    
    # Батчевая запись должна быть быстрее
    assert time1 < time2
```

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация батчевой записи**
2. **Добавление индексов для оптимизации**
3. **Реализация кэширования статистики**
4. **Добавление асинхронной обработки**
5. **Реализация сжатия данных**
6. **Интеграция с системой мониторинга**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 