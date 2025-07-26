# 📝 LoggerPlugin

## 📋 **ОПИСАНИЕ**

**LoggerPlugin** - плагин для централизованного логирования системы. Обеспечивает структурированное логирование, ротацию логов, фильтрацию и мониторинг производительности.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Централизованное логирование всех плагинов
- Ротация логов по размеру и времени
- Фильтрация логов по уровням
- Мониторинг производительности логирования
- Подчиняется PluginManager

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def log_info(self, message: str, **kwargs) -> None:
    """Логирование информационных сообщений"""

def log_error(self, message: str, **kwargs) -> None:
    """Логирование ошибок"""

def log_warning(self, message: str, **kwargs) -> None:
    """Логирование предупреждений"""

def get_statistics(self) -> Dict[str, Any]:
    """Получение статистики логирования"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

### **1. Асинхронное Логирование**
```python
async def log_async(self, level: str, message: str, **kwargs) -> None:
    """Асинхронное логирование для улучшения производительности"""
    
    # Создание записи лога
    log_entry = {
        'timestamp': datetime.now(),
        'level': level,
        'message': message,
        'kwargs': kwargs,
        'thread_id': threading.get_ident(),
        'plugin': kwargs.get('plugin', 'unknown')
    }
    
    # Добавление в очередь для асинхронной обработки
    await self.log_queue.put(log_entry)
    
    # Запуск обработки если не запущена
    if not self.processing_task or self.processing_task.done():
        self.processing_task = asyncio.create_task(self._process_log_queue())

async def _process_log_queue(self) -> None:
    """Обработка очереди логов"""
    
    batch_size = 100
    batch = []
    
    while True:
        try:
            # Получение записи из очереди с таймаутом
            log_entry = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)
            batch.append(log_entry)
            
            # Обработка батча
            if len(batch) >= batch_size:
                await self._write_log_batch(batch)
                batch = []
                
        except asyncio.TimeoutError:
            # Обработка оставшихся записей
            if batch:
                await self._write_log_batch(batch)
            break

async def _write_log_batch(self, batch: List[Dict]) -> None:
    """Запись батча логов"""
    
    # Форматирование записей
    formatted_logs = []
    for entry in batch:
        formatted = self._format_log_entry(entry)
        formatted_logs.append(formatted)
    
    # Запись в файл
    log_file = self._get_current_log_file()
    
    async with aiofiles.open(log_file, 'a', encoding='utf-8') as f:
        await f.write('\n'.join(formatted_logs) + '\n')
    
    # Обновление статистики
    self._update_statistics(batch)
```

### **2. Умная Ротация Логов**
```python
def smart_log_rotation(self) -> None:
    """Умная ротация логов на основе размера и времени"""
    
    current_log_file = self._get_current_log_file()
    
    if not os.path.exists(current_log_file):
        return
    
    # Проверка размера файла
    file_size = os.path.getsize(current_log_file)
    max_size = 10 * 1024 * 1024  # 10 MB
    
    # Проверка времени последней ротации
    last_rotation = self.rotation_history.get('last_rotation', 0)
    current_time = time.time()
    rotation_interval = 24 * 3600  # 24 часа
    
    should_rotate = (file_size > max_size or 
                    current_time - last_rotation > rotation_interval)
    
    if should_rotate:
        self._perform_log_rotation()

def _perform_log_rotation(self) -> None:
    """Выполнение ротации логов"""
    
    current_log_file = self._get_current_log_file()
    
    # Создание имени архивированного файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"app_{timestamp}.log"
    archive_path = os.path.join(self.log_dir, "archive", archive_name)
    
    # Создание директории архива
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    
    # Сжатие и перемещение файла
    with open(current_log_file, 'rb') as f_in:
        with gzip.open(f"{archive_path}.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Очистка старого файла
    os.remove(current_log_file)
    
    # Ограничение количества архивных файлов
    self._cleanup_old_logs()
    
    # Обновление истории ротации
    self.rotation_history['last_rotation'] = time.time()
    self.rotation_history['rotations_count'] += 1
    
    self.log_info("Ротация логов выполнена")

def _cleanup_old_logs(self, max_archives=30) -> None:
    """Очистка старых архивных логов"""
    
    archive_dir = os.path.join(self.log_dir, "archive")
    if not os.path.exists(archive_dir):
        return
    
    # Получение списка архивных файлов
    archive_files = glob.glob(os.path.join(archive_dir, "*.gz"))
    
    # Сортировка по времени создания
    archive_files.sort(key=lambda x: os.path.getctime(x))
    
    # Удаление старых файлов
    if len(archive_files) > max_archives:
        files_to_delete = archive_files[:-max_archives]
        for file_path in files_to_delete:
            os.remove(file_path)
```

### **3. Фильтрация и Структурирование**
```python
def structured_logging(self, level: str, message: str, **kwargs) -> None:
    """Структурированное логирование с фильтрацией"""
    
    # Проверка уровня логирования
    if not self._should_log(level):
        return
    
    # Создание структурированной записи
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level.upper(),
        'message': message,
        'plugin': kwargs.get('plugin', 'unknown'),
        'function': kwargs.get('function', 'unknown'),
        'line': kwargs.get('line', 0),
        'thread_id': threading.get_ident(),
        'process_id': os.getpid(),
        'extra_data': {k: v for k, v in kwargs.items() 
                      if k not in ['plugin', 'function', 'line']}
    }
    
    # Фильтрация по правилам
    if self._should_filter(log_entry):
        return
    
    # Форматирование в JSON
    formatted_log = json.dumps(log_entry, ensure_ascii=False, default=str)
    
    # Добавление в очередь
    asyncio.create_task(self.log_async(level, formatted_log, **kwargs))

def _should_log(self, level: str) -> bool:
    """Проверка необходимости логирования"""
    
    level_priority = {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3,
        'CRITICAL': 4
    }
    
    current_priority = level_priority.get(level.upper(), 0)
    min_priority = level_priority.get(self.min_level.upper(), 0)
    
    return current_priority >= min_priority

def _should_filter(self, log_entry: Dict) -> bool:
    """Проверка фильтрации записи"""
    
    # Фильтр по плагину
    if self.plugin_filter and log_entry['plugin'] not in self.plugin_filter:
        return True
    
    # Фильтр по ключевым словам
    if self.keyword_filter:
        message = log_entry['message'].lower()
        for keyword in self.keyword_filter:
            if keyword.lower() in message:
                return True
    
    # Фильтр по регулярным выражениям
    if self.regex_filter:
        message = log_entry['message']
        for pattern in self.regex_filter:
            if re.search(pattern, message):
                return True
    
    return False
```

### **4. Кэширование и Батчевая Запись**
```python
def batched_logging(self, level: str, message: str, **kwargs) -> None:
    """Батчевое логирование для оптимизации"""
    
    # Добавление в батч
    log_entry = {
        'timestamp': datetime.now(),
        'level': level,
        'message': message,
        'kwargs': kwargs
    }
    
    self.log_batch.append(log_entry)
    
    # Проверка размера батча
    if len(self.log_batch) >= self.batch_size:
        self._flush_log_batch()

def _flush_log_batch(self) -> None:
    """Запись батча логов"""
    
    if not self.log_batch:
        return
    
    # Группировка по уровням
    grouped_logs = {}
    for entry in self.log_batch:
        level = entry['level']
        if level not in grouped_logs:
            grouped_logs[level] = []
        grouped_logs[level].append(entry)
    
    # Запись по группам
    for level, entries in grouped_logs.items():
        self._write_level_batch(level, entries)
    
    # Очистка батча
    self.log_batch.clear()

def _write_level_batch(self, level: str, entries: List[Dict]) -> None:
    """Запись батча для определенного уровня"""
    
    # Форматирование записей
    formatted_entries = []
    for entry in entries:
        formatted = self._format_log_entry(entry)
        formatted_entries.append(formatted)
    
    # Запись в файл
    log_file = self._get_level_log_file(level)
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write('\n'.join(formatted_entries) + '\n')
```

### **5. Мониторинг Производительности**
```python
def performance_monitoring(self) -> Dict[str, Any]:
    """Мониторинг производительности логирования"""
    
    monitoring_data = {
        'total_logs': 0,
        'logs_by_level': {},
        'average_log_size': 0,
        'queue_size': 0,
        'batch_efficiency': 0,
        'rotation_count': 0,
        'disk_usage': 0
    }
    
    # Статистика по уровням
    for level, count in self.logs_by_level.items():
        monitoring_data['logs_by_level'][level] = count
        monitoring_data['total_logs'] += count
    
    # Размер очереди
    if hasattr(self, 'log_queue'):
        monitoring_data['queue_size'] = self.log_queue.qsize()
    
    # Эффективность батчевой записи
    if self.batch_writes > 0:
        monitoring_data['batch_efficiency'] = (self.batch_writes / 
                                             (self.batch_writes + self.single_writes)) * 100
    
    # Количество ротаций
    monitoring_data['rotation_count'] = self.rotation_history.get('rotations_count', 0)
    
    # Использование диска
    log_dir_size = self._calculate_log_dir_size()
    monitoring_data['disk_usage'] = log_dir_size
    
    return monitoring_data

def _calculate_log_dir_size(self) -> int:
    """Расчет размера директории логов"""
    
    total_size = 0
    
    for root, dirs, files in os.walk(self.log_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
    
    return total_size
```

### **6. Оптимизация Памяти**
```python
def memory_optimized_logging(self, level: str, message: str, **kwargs) -> None:
    """Логирование с оптимизацией памяти"""
    
    # Ограничение размера сообщения
    if len(message) > self.max_message_size:
        message = message[:self.max_message_size] + "..."
    
    # Ограничение размера дополнительных данных
    if 'extra_data' in kwargs:
        kwargs['extra_data'] = self._truncate_extra_data(kwargs['extra_data'])
    
    # Использование слабых ссылок для больших объектов
    if 'large_object' in kwargs:
        kwargs['large_object'] = weakref.proxy(kwargs['large_object'])
    
    # Логирование с оптимизацией
    self.structured_logging(level, message, **kwargs)

def _truncate_extra_data(self, extra_data: Dict) -> Dict:
    """Обрезка дополнительных данных"""
    
    truncated = {}
    max_value_size = 1000
    
    for key, value in extra_data.items():
        if isinstance(value, str) and len(value) > max_value_size:
            truncated[key] = value[:max_value_size] + "..."
        elif isinstance(value, (dict, list)):
            # Ограничение глубины вложенности
            truncated[key] = self._truncate_nested_data(value, max_depth=3)
        else:
            truncated[key] = value
    
    return truncated
```

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Скорость логирования**: увеличение в 5-10 раз (асинхронное логирование)
- **Использование памяти**: снижение на 60% (оптимизация памяти)
- **Батчевая запись**: снижение операций I/O на 80%
- **Ротация логов**: автоматическая очистка и сжатие
- **Фильтрация**: эффективная фильтрация ненужных записей

## 🔗 **ЗАВИСИМОСТИ**

- **PluginManager**: управление плагином
- **Все плагины**: предоставление логов
- **MonitoringPlugin**: передача метрик производительности

## 🧪 **ТЕСТИРОВАНИЕ**

```python
def test_logging_performance():
    """Тест производительности логирования"""
    
    # Тест асинхронного логирования
    start_time = time.time()
    for i in range(10000):
        logger.log_async('INFO', f'Test message {i}')
    time1 = time.time() - start_time
    
    # Тест синхронного логирования
    start_time = time.time()
    for i in range(10000):
        logger.log_info(f'Test message {i}')
    time2 = time.time() - start_time
    
    # Асинхронное логирование должно быть быстрее
    assert time1 < time2
```

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация асинхронного логирования**
2. **Добавление умной ротации логов**
3. **Реализация структурированного логирования**
4. **Добавление батчевой записи**
5. **Реализация мониторинга производительности**
6. **Добавление оптимизации памяти**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 