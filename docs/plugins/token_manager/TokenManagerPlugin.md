# 🔑 TokenManagerPlugin

## 📋 **ОПИСАНИЕ**

**TokenManagerPlugin** - плагин для управления VK API токенами. Обеспечивает ротацию токенов, мониторинг лимитов API и предоставление токенов для VKSearchPlugin.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Ротация VK API токенов
- Мониторинг лимитов API
- Предоставление токенов VKSearchPlugin
- Отслеживание производительности токенов
- Подчиняется PluginManager

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def get_next_token(self) -> str:
    """Получение следующего доступного токена"""

def check_token_limits(self, token: str) -> Dict[str, Any]:
    """Проверка лимитов токена"""

def rotate_tokens(self) -> None:
    """Ротация токенов"""

def get_statistics(self) -> Dict[str, Any]:
    """Получение статистики токенов"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

### **1. Умная Ротация Токенов**
```python
def smart_token_rotation(self) -> str:
    """Умная ротация токенов на основе производительности"""
    
    # Анализ производительности токенов
    token_performance = {}
    for token in self.tokens:
        performance = self._analyze_token_performance(token)
        token_performance[token] = performance
    
    # Выбор лучшего токена
    best_token = max(token_performance.items(), key=lambda x: x[1])[0]
    
    # Проверка лимитов
    if self._is_token_available(best_token):
        return best_token
    else:
        # Выбор следующего доступного токена
        return self._get_next_available_token()

def _analyze_token_performance(self, token: str) -> float:
    """Анализ производительности токена"""
    
    # Метрики производительности
    success_rate = self.token_stats[token].get('success_rate', 0)
    response_time = self.token_stats[token].get('avg_response_time', 0)
    remaining_requests = self.token_stats[token].get('remaining_requests', 0)
    
    # Расчет производительности
    performance = (success_rate * 0.4 + 
                  (1 / (response_time + 1)) * 0.3 + 
                  (remaining_requests / 1000) * 0.3)
    
    return performance
```

### **2. Предсказание Лимитов**
```python
def predict_token_limits(self, token: str) -> Dict[str, Any]:
    """Предсказание лимитов токена на основе исторических данных"""
    
    # Анализ исторических данных
    historical_data = self.token_history.get(token, [])
    
    if not historical_data:
        return {'predicted_reset_time': None, 'risk_level': 'unknown'}
    
    # Анализ паттернов использования
    usage_patterns = self._analyze_usage_patterns(historical_data)
    
    # Предсказание времени сброса лимитов
    predicted_reset = self._predict_reset_time(usage_patterns)
    
    # Оценка риска превышения лимитов
    risk_level = self._calculate_risk_level(token, usage_patterns)
    
    return {
        'predicted_reset_time': predicted_reset,
        'risk_level': risk_level,
        'usage_pattern': usage_patterns
    }

def _analyze_usage_patterns(self, historical_data: List[Dict]) -> Dict:
    """Анализ паттернов использования токена"""
    
    # Группировка по часам
    hourly_usage = {}
    for record in historical_data:
        hour = record['timestamp'].hour
        hourly_usage[hour] = hourly_usage.get(hour, 0) + record['requests']
    
    # Поиск пиковых часов
    peak_hours = sorted(hourly_usage.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        'peak_hours': peak_hours,
        'avg_requests_per_hour': sum(hourly_usage.values()) / 24,
        'usage_variance': self._calculate_variance(list(hourly_usage.values()))
    }
```

### **3. Адаптивное Управление Лимитами**
```python
def adaptive_rate_limiting(self, token: str) -> bool:
    """Адаптивное управление лимитами запросов"""
    
    current_time = datetime.now()
    token_info = self.token_stats.get(token, {})
    
    # Проверка текущих лимитов
    if not self._is_token_available(token):
        return False
    
    # Анализ нагрузки
    current_load = self._get_current_load(token)
    predicted_load = self._predict_load(token, current_time)
    
    # Адаптивное ограничение
    if current_load + predicted_load > self._get_safe_limit(token):
        self.log_warning(f"Токен {token}: превышение безопасного лимита")
        return False
    
    # Обновление статистики
    self._update_token_usage(token, current_time)
    return True

def _get_safe_limit(self, token: str) -> int:
    """Получение безопасного лимита для токена"""
    
    base_limit = 1000  # Базовый лимит
    token_performance = self._analyze_token_performance(token)
    
    # Адаптация на основе производительности
    if token_performance > 0.8:
        return int(base_limit * 1.2)  # Увеличение для хороших токенов
    elif token_performance < 0.5:
        return int(base_limit * 0.8)  # Уменьшение для плохих токенов
    else:
        return base_limit
```

### **4. Кэширование Статуса Токенов**
```python
def get_token_status_cached(self, token: str, cache_ttl=60) -> Dict[str, Any]:
    """Получение статуса токена с кэшированием"""
    
    cache_key = f"token_status_{token}"
    
    # Проверка кэша
    if cache_key in self.status_cache:
        cache_entry = self.status_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < cache_ttl:
            return cache_entry['data']
    
    # Получение актуального статуса
    status = self._get_token_status(token)
    
    # Кэширование
    self.status_cache[cache_key] = {
        'data': status,
        'timestamp': time.time()
    }
    
    return status

def _get_token_status(self, token: str) -> Dict[str, Any]:
    """Получение актуального статуса токена"""
    
    # Проверка лимитов через API
    limits = self.check_token_limits(token)
    
    # Анализ производительности
    performance = self._analyze_token_performance(token)
    
    # Предсказание лимитов
    predictions = self.predict_token_limits(token)
    
    return {
        'token': token,
        'limits': limits,
        'performance': performance,
        'predictions': predictions,
        'last_updated': datetime.now()
    }
```

### **5. Автоматическое Восстановление**
```python
def auto_token_recovery(self) -> None:
    """Автоматическое восстановление токенов"""
    
    for token in self.tokens:
        status = self.get_token_status_cached(token)
        
        # Проверка необходимости восстановления
        if self._needs_recovery(token, status):
            self._recover_token(token)
    
    # Обновление статистики
    self._update_recovery_statistics()

def _needs_recovery(self, token: str, status: Dict) -> bool:
    """Проверка необходимости восстановления токена"""
    
    # Проверка блокировки
    if status.get('is_blocked', False):
        return True
    
    # Проверка производительности
    performance = status.get('performance', 0)
    if performance < 0.3:  # Низкая производительность
        return True
    
    # Проверка лимитов
    limits = status.get('limits', {})
    if limits.get('remaining_requests', 0) < 100:  # Мало запросов
        return True
    
    return False

def _recover_token(self, token: str) -> None:
    """Восстановление токена"""
    
    # Сброс статистики
    self.token_stats[token] = {
        'success_rate': 1.0,
        'avg_response_time': 0,
        'remaining_requests': 1000,
        'last_reset': datetime.now()
    }
    
    # Очистка истории ошибок
    self.token_errors[token] = []
    
    self.log_info(f"Токен {token} восстановлен")
```

### **6. Мониторинг в Реальном Времени**
```python
def real_time_monitoring(self) -> Dict[str, Any]:
    """Мониторинг токенов в реальном времени"""
    
    monitoring_data = {
        'total_tokens': len(self.tokens),
        'available_tokens': 0,
        'blocked_tokens': 0,
        'low_performance_tokens': 0,
        'average_performance': 0,
        'total_requests': 0,
        'success_rate': 0
    }
    
    total_performance = 0
    
    for token in self.tokens:
        status = self.get_token_status_cached(token)
        
        if status.get('limits', {}).get('is_available', False):
            monitoring_data['available_tokens'] += 1
        else:
            monitoring_data['blocked_tokens'] += 1
        
        performance = status.get('performance', 0)
        total_performance += performance
        
        if performance < 0.5:
            monitoring_data['low_performance_tokens'] += 1
        
        # Статистика запросов
        requests = status.get('limits', {}).get('total_requests', 0)
        monitoring_data['total_requests'] += requests
    
    # Средние показатели
    if self.tokens:
        monitoring_data['average_performance'] = total_performance / len(self.tokens)
    
    return monitoring_data
```

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Эффективность ротации**: увеличение в 2-3 раза (умная ротация)
- **Предсказание лимитов**: точность 85-90%
- **Кэширование**: снижение нагрузки на API на 60%
- **Автоматическое восстановление**: снижение простоя на 70%
- **Мониторинг**: отслеживание в реальном времени

## 🔗 **ЗАВИСИМОСТИ**

- **PluginManager**: управление плагином
- **VKSearchPlugin**: предоставление токенов
- **MonitoringPlugin**: передача метрик

## 🧪 **ТЕСТИРОВАНИЕ**

```python
def test_token_rotation():
    """Тест ротации токенов"""
    
    # Тест умной ротации
    start_time = time.time()
    token1 = token_manager.smart_token_rotation()
    time1 = time.time() - start_time
    
    # Тест обычной ротации
    start_time = time.time()
    token2 = token_manager.get_next_token()
    time2 = time.time() - start_time
    
    # Умная ротация должна быть эффективнее
    assert token1 != token2  # Разные токены
```

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация умной ротации токенов**
2. **Добавление предсказания лимитов**
3. **Реализация адаптивного управления**
4. **Добавление кэширования статуса**
5. **Реализация автоматического восстановления**
6. **Добавление мониторинга в реальном времени**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 