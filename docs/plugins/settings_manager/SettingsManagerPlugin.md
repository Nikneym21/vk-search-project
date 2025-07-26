# ⚙️ SettingsManagerPlugin

## 📋 **ОПИСАНИЕ**

**SettingsManagerPlugin** - плагин для централизованного управления настройками системы. Обеспечивает сохранение настроек интерфейса, парсера, Google Sheets и автосохранение.

## 🎯 **ОТВЕТСТВЕННОСТЬ**

- Сохранение настроек интерфейса
- Сохранение настроек парсера
- Управление настройками Google Sheets
- Автосохранение и загрузка настроек
- Подчиняется PluginManager

## 🔧 **ОСНОВНЫЕ МЕТОДЫ**

```python
def save_settings(self, settings_type: str, settings: Dict) -> bool:
    """Сохранение настроек"""

def load_settings(self, settings_type: str) -> Dict:
    """Загрузка настроек"""

def auto_save(self) -> None:
    """Автосохранение настроек"""

def get_statistics(self) -> Dict[str, Any]:
    """Получение статистики настроек"""
```

## ⚡ **ПРЕДЛОЖЕНИЯ ПО ОПТИМИЗАЦИИ**

### **1. Умное Автосохранение**
```python
def smart_auto_save(self, settings_type: str, settings: Dict, 
                   force_save=False) -> bool:
    """Умное автосохранение с проверкой изменений"""
    
    # Проверка изменений
    if not force_save and not self._has_changes(settings_type, settings):
        return True  # Нет изменений, пропускаем сохранение
    
    # Создание резервной копии
    backup_created = self._create_backup(settings_type)
    
    try:
        # Сохранение настроек
        success = self.save_settings(settings_type, settings)
        
        if success:
            # Обновление кэша
            self._update_cache(settings_type, settings)
            
            # Очистка старых резервных копий
            self._cleanup_old_backups(settings_type)
            
            self.log_info(f"Настройки {settings_type} автосохранены")
            return True
        else:
            # Восстановление из резервной копии
            if backup_created:
                self._restore_from_backup(settings_type)
            
            return False
            
    except Exception as e:
        self.log_error(f"Ошибка автосохранения {settings_type}: {e}")
        
        # Восстановление из резервной копии
        if backup_created:
            self._restore_from_backup(settings_type)
        
        return False

def _has_changes(self, settings_type: str, new_settings: Dict) -> bool:
    """Проверка наличия изменений в настройках"""
    
    # Получение текущих настроек из кэша
    current_settings = self.settings_cache.get(settings_type, {})
    
    # Сравнение настроек
    return current_settings != new_settings
```

### **2. Кэширование Настроек**
```python
def load_settings_cached(self, settings_type: str, cache_ttl=300) -> Dict:
    """Загрузка настроек с кэшированием"""
    
    # Проверка кэша
    if settings_type in self.settings_cache:
        cache_entry = self.settings_cache[settings_type]
        if time.time() - cache_entry['timestamp'] < cache_ttl:
            return cache_entry['data']
    
    # Загрузка из файла
    settings = self.load_settings(settings_type)
    
    # Кэширование
    self.settings_cache[settings_type] = {
        'data': settings,
        'timestamp': time.time()
    }
    
    return settings

def _update_cache(self, settings_type: str, settings: Dict) -> None:
    """Обновление кэша настроек"""
    
    self.settings_cache[settings_type] = {
        'data': settings,
        'timestamp': time.time()
    }
```

### **3. Валидация Настроек**
```python
def validate_settings(self, settings_type: str, settings: Dict) -> Dict[str, Any]:
    """Валидация настроек с автоматическим исправлением"""
    
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'fixed_settings': settings.copy()
    }
    
    # Схемы валидации для разных типов настроек
    validation_schemas = {
        'interface': self._get_interface_schema(),
        'parser': self._get_parser_schema(),
        'google_sheets': self._get_google_sheets_schema(),
        'window': self._get_window_schema()
    }
    
    schema = validation_schemas.get(settings_type, {})
    
    # Валидация по схеме
    for field, rules in schema.items():
        if field in settings:
            value = settings[field]
            
            # Проверка типа
            if 'type' in rules and not isinstance(value, rules['type']):
                validation_result['errors'].append(f"Неверный тип для {field}")
                validation_result['is_valid'] = False
                
                # Автоматическое исправление
                if 'default' in rules:
                    validation_result['fixed_settings'][field] = rules['default']
            
            # Проверка диапазона
            if 'min' in rules and value < rules['min']:
                validation_result['warnings'].append(f"{field} меньше минимального значения")
                validation_result['fixed_settings'][field] = rules['min']
            
            if 'max' in rules and value > rules['max']:
                validation_result['warnings'].append(f"{field} больше максимального значения")
                validation_result['fixed_settings'][field] = rules['max']
            
            # Проверка обязательности
            if rules.get('required', False) and not value:
                validation_result['errors'].append(f"Поле {field} обязательно")
                validation_result['is_valid'] = False
        else:
            # Отсутствующее обязательное поле
            if rules.get('required', False):
                validation_result['errors'].append(f"Отсутствует обязательное поле {field}")
                validation_result['is_valid'] = False
                
                # Добавление значения по умолчанию
                if 'default' in rules:
                    validation_result['fixed_settings'][field] = rules['default']
    
    return validation_result

def _get_interface_schema(self) -> Dict:
    """Схема валидации настроек интерфейса"""
    
    return {
        'theme': {
            'type': str,
            'required': True,
            'default': 'dark'
        },
        'language': {
            'type': str,
            'required': True,
            'default': 'ru'
        },
        'auto_save_interval': {
            'type': int,
            'min': 30,
            'max': 3600,
            'default': 300
        }
    }
```

### **4. Резервное Копирование**
```python
def _create_backup(self, settings_type: str) -> bool:
    """Создание резервной копии настроек"""
    
    try:
        backup_dir = Path("data/backups/settings")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Имя файла резервной копии
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{settings_type}_{timestamp}.json"
        backup_path = backup_dir / backup_filename
        
        # Копирование текущих настроек
        current_settings = self.load_settings(settings_type)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(current_settings, f, indent=2, ensure_ascii=False)
        
        # Ограничение количества резервных копий
        self._limit_backups(settings_type, max_backups=5)
        
        return True
        
    except Exception as e:
        self.log_error(f"Ошибка создания резервной копии: {e}")
        return False

def _restore_from_backup(self, settings_type: str) -> bool:
    """Восстановление настроек из резервной копии"""
    
    try:
        backup_dir = Path("data/backups/settings")
        
        # Поиск последней резервной копии
        backup_files = list(backup_dir.glob(f"{settings_type}_*.json"))
        
        if not backup_files:
            return False
        
        # Сортировка по времени создания
        latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
        
        # Загрузка резервной копии
        with open(latest_backup, 'r', encoding='utf-8') as f:
            backup_settings = json.load(f)
        
        # Восстановление настроек
        success = self.save_settings(settings_type, backup_settings)
        
        if success:
            self.log_info(f"Настройки {settings_type} восстановлены из резервной копии")
        
        return success
        
    except Exception as e:
        self.log_error(f"Ошибка восстановления из резервной копии: {e}")
        return False
```

### **5. Оптимизированное Сохранение**
```python
def save_settings_optimized(self, settings_type: str, settings: Dict) -> bool:
    """Оптимизированное сохранение настроек"""
    
    try:
        # Подготовка файла
        settings_file = Path(f"data/{settings_type}_settings.json")
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Создание временного файла
        temp_file = settings_file.with_suffix('.tmp')
        
        # Запись во временный файл
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        # Атомарная замена файла
        temp_file.replace(settings_file)
        
        # Обновление кэша
        self._update_cache(settings_type, settings)
        
        # Очистка старых кэшей
        self._cleanup_cache()
        
        return True
        
    except Exception as e:
        self.log_error(f"Ошибка сохранения настроек {settings_type}: {e}")
        return False

def _cleanup_cache(self) -> None:
    """Очистка устаревших записей кэша"""
    
    current_time = time.time()
    cache_ttl = 3600  # 1 час
    
    expired_keys = []
    
    for key, entry in self.settings_cache.items():
        if current_time - entry['timestamp'] > cache_ttl:
            expired_keys.append(key)
    
    for key in expired_keys:
        del self.settings_cache[key]
```

### **6. Мониторинг Производительности**
```python
def performance_monitoring(self) -> Dict[str, Any]:
    """Мониторинг производительности работы с настройками"""
    
    monitoring_data = {
        'total_operations': 0,
        'save_operations': 0,
        'load_operations': 0,
        'cache_hit_rate': 0,
        'backup_operations': 0,
        'validation_errors': 0,
        'average_operation_time': 0
    }
    
    # Статистика операций
    for operation in self.operation_history:
        monitoring_data['total_operations'] += 1
        
        if operation['type'] == 'save':
            monitoring_data['save_operations'] += 1
        elif operation['type'] == 'load':
            monitoring_data['load_operations'] += 1
        elif operation['type'] == 'backup':
            monitoring_data['backup_operations'] += 1
        
        # Время выполнения
        duration = operation.get('duration', 0)
        monitoring_data['average_operation_time'] += duration
        
        # Ошибки валидации
        if operation.get('validation_errors'):
            monitoring_data['validation_errors'] += len(operation['validation_errors'])
    
    # Расчет средних значений
    if monitoring_data['total_operations'] > 0:
        monitoring_data['average_operation_time'] /= monitoring_data['total_operations']
    
    # Статистика кэша
    cache_hits = sum(1 for op in self.operation_history if op.get('cache_hit', False))
    if monitoring_data['load_operations'] > 0:
        monitoring_data['cache_hit_rate'] = (cache_hits / monitoring_data['load_operations']) * 100
    
    return monitoring_data
```

## 📊 **МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ**

### **Ожидаемые результаты оптимизации:**
- **Скорость загрузки**: увеличение в 5-10 раз (кэширование)
- **Автосохранение**: снижение количества операций на 70%
- **Валидация**: автоматическое исправление 90% ошибок
- **Резервное копирование**: надежность 99.9%
- **Оптимизированное сохранение**: атомарные операции без потери данных

## 🔗 **ЗАВИСИМОСТИ**

- **PluginManager**: управление плагином
- **Все плагины**: предоставление настроек
- **MonitoringPlugin**: передача метрик производительности

## 🧪 **ТЕСТИРОВАНИЕ**

```python
def test_settings_performance():
    """Тест производительности работы с настройками"""
    
    # Тест кэшированной загрузки
    start_time = time.time()
    settings1 = settings_manager.load_settings_cached('interface')
    time1 = time.time() - start_time
    
    # Тест обычной загрузки
    start_time = time.time()
    settings2 = settings_manager.load_settings('interface')
    time2 = time.time() - start_time
    
    # Кэшированная загрузка должна быть быстрее
    assert time1 < time2
```

## 📈 **ПЛАН РАЗВИТИЯ**

1. **Реализация умного автосохранения**
2. **Добавление кэширования настроек**
3. **Реализация валидации настроек**
4. **Добавление резервного копирования**
5. **Реализация оптимизированного сохранения**
6. **Добавление мониторинга производительности**

---

**Версия:** 1.0  
**Статус:** В разработке с оптимизациями 