# 📊 MonitoringPlugin

## 📋 **ОПИСАНИЕ**

**MonitoringPlugin** - плагин для мониторинга производительности системы в реальном времени. Отслеживает метрики плагинов, использование ресурсов и генерирует отчеты о производительности.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Мониторинг производительности всех плагинов
- Отслеживание использования ресурсов (CPU, память, диск)
- Генерация отчетов о производительности
- Алерты при превышении лимитов
- Подчиняется PluginManager

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def start_monitoring(self) -> bool:
    """Запуск мониторинга"""

def stop_monitoring(self) -> None:
    """Остановка мониторинга"""

def get_performance_metrics(self) -> Dict[str, Any]:
    """Получение метрик производительности"""

def get_statistics(self) -> Dict[str, Any]:
    """Получение статистики мониторинга"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

### **1. Асинхронный Мониторинг**
```python
async def async_monitoring_loop(self) -> None:
    """Асинхронный цикл мониторинга"""
    
    while self.monitoring_active:
        try:
            # Параллельный сбор метрик
            tasks = [
                self._collect_plugin_metrics(),
                self._collect_system_metrics(),
                self._collect_performance_metrics(),
                self._check_alerts()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обработка результатов
            plugin_metrics, system_metrics, perf_metrics, alerts = results
            
            # Сохранение метрик
            await self._save_metrics(plugin_metrics, system_metrics, perf_metrics)
            
            # Обработка алертов
            if alerts:
                await self._process_alerts(alerts)
            
            # Ожидание следующего цикла
            await asyncio.sleep(self.monitoring_interval)
            
        except Exception as e:
            self.log_error(f"Ошибка в цикле мониторинга: {e}")
            await asyncio.sleep(5)  # Пауза при ошибке

async def _collect_plugin_metrics(self) -> Dict[str, Any]:
    """Сбор метрик плагинов"""
    
    plugin_metrics = {}
    
    for plugin_name, plugin in self.plugin_manager.plugins.items():
        try:
            # Асинхронный сбор метрик плагина
            if hasattr(plugin, 'get_statistics'):
                metrics = await asyncio.wait_for(
                    asyncio.create_task(self._get_plugin_stats(plugin)),
                    timeout=5.0
                )
                plugin_metrics[plugin_name] = metrics
            else:
                plugin_metrics[plugin_name] = {'status': 'no_metrics'}
                
        except asyncio.TimeoutError:
            plugin_metrics[plugin_name] = {'status': 'timeout'}
        except Exception as e:
            plugin_metrics[plugin_name] = {'status': 'error', 'error': str(e)}
    
    return plugin_metrics

async def _get_plugin_stats(self, plugin) -> Dict[str, Any]:
    """Получение статистики плагина"""
    
    # Использование ThreadPoolExecutor для синхронных методов
    loop = asyncio.get_event_loop()
    
    def get_stats_sync():
        return plugin.get_statistics()
    
    return await loop.run_in_executor(None, get_stats_sync)
```

### **2. Умный Сбор Метрик**
```python
def smart_metrics_collection(self) -> Dict[str, Any]:
    """Умный сбор метрик с адаптивным интервалом"""
    
    current_time = time.time()
    
    # Адаптивный интервал сбора
    if self._should_collect_detailed_metrics():
        interval = self.detailed_interval
        metrics_level = 'detailed'
    else:
        interval = self.basic_interval
        metrics_level = 'basic'
    
    # Проверка времени последнего сбора
    if current_time - self.last_collection < interval:
        return self.cached_metrics
    
    # Сбор метрик
    metrics = {
        'timestamp': current_time,
        'level': metrics_level,
        'system': self._collect_system_metrics_basic(),
        'plugins': self._collect_plugin_metrics_basic()
    }
    
    # Детальные метрики при необходимости
    if metrics_level == 'detailed':
        metrics.update({
            'detailed_system': self._collect_system_metrics_detailed(),
            'detailed_plugins': self._collect_plugin_metrics_detailed(),
            'performance': self._collect_performance_metrics()
        })
    
    # Кэширование результатов
    self.cached_metrics = metrics
    self.last_collection = current_time
    
    return metrics

def _should_collect_detailed_metrics(self) -> bool:
    """Определение необходимости детального сбора метрик"""
    
    # Проверка активности системы
    if self._is_system_active():
        return True
    
    # Проверка ошибок
    if self._has_recent_errors():
        return True
    
    # Проверка высокой нагрузки
    if self._is_high_load():
        return True
    
    return False

def _is_system_active(self) -> bool:
    """Проверка активности системы"""
    
    # Проверка последних операций
    recent_operations = self._get_recent_operations()
    
    if len(recent_operations) > 10:  # Много операций
        return True
    
    # Проверка времени последней операции
    if recent_operations:
        last_operation = max(recent_operations, key=lambda x: x['timestamp'])
        if time.time() - last_operation['timestamp'] < 300:  # 5 минут
            return True
    
    return False
```

### **3. Кэширование и Агрегация**
```python
def cached_metrics_collection(self, force_refresh=False) -> Dict[str, Any]:
    """Сбор метрик с кэшированием"""
    
    cache_key = 'system_metrics'
    
    # Проверка кэша
    if not force_refresh and cache_key in self.metrics_cache:
        cache_entry = self.metrics_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < self.cache_ttl:
            return cache_entry['data']
    
    # Сбор метрик
    metrics = self._collect_all_metrics()
    
    # Агрегация метрик
    aggregated_metrics = self._aggregate_metrics(metrics)
    
    # Кэширование
    self.metrics_cache[cache_key] = {
        'data': aggregated_metrics,
        'timestamp': time.time()
    }
    
    return aggregated_metrics

def _aggregate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Агрегация метрик для оптимизации"""
    
    aggregated = {
        'summary': {},
        'trends': {},
        'alerts': []
    }
    
    # Агрегация системных метрик
    if 'system' in metrics:
        system_metrics = metrics['system']
        aggregated['summary']['cpu_usage'] = system_metrics.get('cpu_percent', 0)
        aggregated['summary']['memory_usage'] = system_metrics.get('memory_percent', 0)
        aggregated['summary']['disk_usage'] = system_metrics.get('disk_percent', 0)
    
    # Агрегация метрик плагинов
    if 'plugins' in metrics:
        plugin_metrics = metrics['plugins']
        total_operations = 0
        total_errors = 0
        
        for plugin_name, plugin_data in plugin_metrics.items():
            if isinstance(plugin_data, dict):
                total_operations += plugin_data.get('total_operations', 0)
                total_errors += plugin_data.get('errors', 0)
        
        aggregated['summary']['total_operations'] = total_operations
        aggregated['summary']['total_errors'] = total_errors
        aggregated['summary']['error_rate'] = (total_errors / total_operations * 100 
                                             if total_operations > 0 else 0)
    
    # Анализ трендов
    aggregated['trends'] = self._analyze_trends(metrics)
    
    # Проверка алертов
    aggregated['alerts'] = self._check_alerts(aggregated['summary'])
    
    return aggregated
```

### **4. Умные Алерты**
```python
def smart_alert_system(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Умная система алертов"""
    
    alerts = []
    
    # Проверка системных метрик
    system_alerts = self._check_system_alerts(metrics)
    alerts.extend(system_alerts)
    
    # Проверка метрик плагинов
    plugin_alerts = self._check_plugin_alerts(metrics)
    alerts.extend(plugin_alerts)
    
    # Проверка трендов
    trend_alerts = self._check_trend_alerts(metrics)
    alerts.extend(trend_alerts)
    
    # Дедупликация алертов
    unique_alerts = self._deduplicate_alerts(alerts)
    
    # Приоритизация алертов
    prioritized_alerts = self._prioritize_alerts(unique_alerts)
    
    return prioritized_alerts

def _check_system_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Проверка системных алертов"""
    
    alerts = []
    summary = metrics.get('summary', {})
    
    # Проверка CPU
    cpu_usage = summary.get('cpu_usage', 0)
    if cpu_usage > 90:
        alerts.append({
            'type': 'system',
            'level': 'critical',
            'message': f'Высокое использование CPU: {cpu_usage}%',
            'metric': 'cpu_usage',
            'value': cpu_usage,
            'threshold': 90
        })
    elif cpu_usage > 80:
        alerts.append({
            'type': 'system',
            'level': 'warning',
            'message': f'Повышенное использование CPU: {cpu_usage}%',
            'metric': 'cpu_usage',
            'value': cpu_usage,
            'threshold': 80
        })
    
    # Проверка памяти
    memory_usage = summary.get('memory_usage', 0)
    if memory_usage > 85:
        alerts.append({
            'type': 'system',
            'level': 'critical',
            'message': f'Высокое использование памяти: {memory_usage}%',
            'metric': 'memory_usage',
            'value': memory_usage,
            'threshold': 85
        })
    
    # Проверка диска
    disk_usage = summary.get('disk_usage', 0)
    if disk_usage > 90:
        alerts.append({
            'type': 'system',
            'level': 'critical',
            'message': f'Критическое использование диска: {disk_usage}%',
            'metric': 'disk_usage',
            'value': disk_usage,
            'threshold': 90
        })
    
    return alerts

def _check_plugin_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Проверка алертов плагинов"""
    
    alerts = []
    plugins = metrics.get('plugins', {})
    
    for plugin_name, plugin_data in plugins.items():
        if not isinstance(plugin_data, dict):
            continue
        
        # Проверка ошибок
        errors = plugin_data.get('errors', 0)
        total_operations = plugin_data.get('total_operations', 0)
        
        if total_operations > 0:
            error_rate = (errors / total_operations) * 100
            
            if error_rate > 10:
                alerts.append({
                    'type': 'plugin',
                    'level': 'critical',
                    'message': f'Высокий уровень ошибок в {plugin_name}: {error_rate:.1f}%',
                    'plugin': plugin_name,
                    'metric': 'error_rate',
                    'value': error_rate,
                    'threshold': 10
                })
        
        # Проверка производительности
        avg_response_time = plugin_data.get('average_response_time', 0)
        if avg_response_time > 5.0:  # 5 секунд
            alerts.append({
                'type': 'plugin',
                'level': 'warning',
                'message': f'Медленная работа {plugin_name}: {avg_response_time:.1f}с',
                'plugin': plugin_name,
                'metric': 'response_time',
                'value': avg_response_time,
                'threshold': 5.0
            })
    
    return alerts
```

### **5. Оптимизированное Хранение**
```python
def optimized_metrics_storage(self, metrics: Dict[str, Any]) -> None:
    """Оптимизированное хранение метрик"""
    
    # Сжатие метрик
    compressed_metrics = self._compress_metrics(metrics)
    
    # Ротация файлов метрик
    self._rotate_metrics_files()
    
    # Запись в оптимизированном формате
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = f"data/metrics/metrics_{timestamp}.json.gz"
    
    # Создание директории
    os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
    
    # Запись сжатых метрик
    with gzip.open(metrics_file, 'wt', encoding='utf-8') as f:
        json.dump(compressed_metrics, f, ensure_ascii=False, indent=2)
    
    # Обновление индекса метрик
    self._update_metrics_index(metrics_file, timestamp)

def _compress_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Сжатие метрик для экономии места"""
    
    compressed = {
        'timestamp': metrics.get('timestamp'),
        'summary': metrics.get('summary', {}),
        'alerts': metrics.get('alerts', [])
    }
    
    # Сжатие детальных метрик
    if 'detailed_system' in metrics:
        detailed = metrics['detailed_system']
        compressed['system'] = {
            'cpu': detailed.get('cpu_percent', 0),
            'memory': detailed.get('memory_percent', 0),
            'disk': detailed.get('disk_percent', 0)
        }
    
    # Сжатие метрик плагинов
    if 'plugins' in metrics:
        plugins = metrics['plugins']
        compressed['plugins'] = {}
        
        for plugin_name, plugin_data in plugins.items():
            if isinstance(plugin_data, dict):
                compressed['plugins'][plugin_name] = {
                    'operations': plugin_data.get('total_operations', 0),
                    'errors': plugin_data.get('errors', 0),
                    'response_time': plugin_data.get('average_response_time', 0)
                }
    
    return compressed
```

### **6. Мониторинг Производительности**
```python
def monitoring_performance_metrics(self) -> Dict[str, Any]:
    """Метрики производительности самого мониторинга"""
    
    performance_data = {
        'collection_time': 0,
        'processing_time': 0,
        'storage_time': 0,
        'cache_hit_rate': 0,
        'alert_processing_time': 0,
        'memory_usage': 0,
        'metrics_file_size': 0
    }
    
    # Время сбора метрик
    if self.collection_history:
        avg_collection_time = sum(h['duration'] for h in self.collection_history) / len(self.collection_history)
        performance_data['collection_time'] = avg_collection_time
    
    # Время обработки
    if self.processing_history:
        avg_processing_time = sum(h['duration'] for h in self.processing_history) / len(self.processing_history)
        performance_data['processing_time'] = avg_processing_time
    
    # Статистика кэша
    cache_hits = sum(1 for h in self.collection_history if h.get('cache_hit', False))
    total_collections = len(self.collection_history)
    if total_collections > 0:
        performance_data['cache_hit_rate'] = (cache_hits / total_collections) * 100
    
    # Размер файлов метрик
    metrics_dir = Path("data/metrics")
    if metrics_dir.exists():
        total_size = sum(f.stat().st_size for f in metrics_dir.glob("*.json.gz"))
        performance_data['metrics_file_size'] = total_size
    
    return performance_data
```

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Скорость сбора метрик**: увеличение в 3-5 раз (асинхронный сбор)
- **Использование ресурсов**: снижение на 50% (умный сбор)
- **Кэширование**: 70-80% запросов из кэша
- **Хранение метрик**: сжатие на 60-70%
- **Алерты**: умная фильтрация и приоритизация

## 🔗 **ЗАВИСИМОСТИ**

- **PluginManager**: получение метрик плагинов
- **Все плагины**: сбор метрик производительности
- **LoggerPlugin**: логирование алертов

## 🧪 **ТЕСТИРОВАНИЕ**

```python
def test_monitoring_performance():
    """Тест производительности мониторинга"""
    
    # Тест асинхронного сбора метрик
    start_time = time.time()
    metrics1 = await monitor.async_monitoring_loop()
    time1 = time.time() - start_time
    
    # Тест синхронного сбора метрик
    start_time = time.time()
    metrics2 = monitor.get_performance_metrics()
    time2 = time.time() - start_time
    
    # Асинхронный сбор должен быть быстрее
    assert time1 < time2
```

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация асинхронного мониторинга**
2. **Добавление умного сбора метрик**
3. **Реализация кэширования и агрегации**
4. **Добавление умной системы алертов**
5. **Реализация оптимизированного хранения**
6. **Добавление мониторинга производительности**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 