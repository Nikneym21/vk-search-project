# HotkeysPlugin

## Описание

HotkeysPlugin — специализированный плагин для управления горячими клавишами в tkinter приложениях, с особой поддержкой macOS.

## Возможности

### 🎮 **Поддерживаемые горячие клавиши**

**macOS (⌘):**
- `⌘+C` — Копировать
- `⌘+V` — Вставить
- `⌘+X` — Вырезать
- `⌘+A` — Выделить все
- `⌘+Z` — Отмена (только Text)
- `⌘+Y` — Повтор (только Text)

**Windows/Linux (Ctrl):**
- `Ctrl+C` — Копировать
- `Ctrl+V` — Вставить
- `Ctrl+X` — Вырезать
- `Ctrl+A` — Выделить все
- `Ctrl+Z` — Отмена (только Text)
- `Ctrl+Y` — Повтор (только Text)

### 🔧 **Поддерживаемые виджеты**

- **Entry** — однострочные поля ввода
- **Text** — многострочные текстовые поля

### 🚀 **Особенности**

- ✅ **Автоопределение ОС** — автоматическое использование правильных модификаторов
- ✅ **Умная обработка выделения** — операции применяются к выделенному тексту
- ✅ **Защита от ошибок** — все операции защищены try/catch блоками
- ✅ **Возврат "break"** — предотвращает дублирование стандартной обработки
- ✅ **Массовая регистрация** — поддержка регистрации множества виджетов

## Архитектура

### Основные методы

```python
class HotkeysPlugin(BasePlugin):
    def register_widget(widget, widget_type="auto") -> bool
    def register_multiple_widgets(widgets: List) -> int
    def get_statistics() -> dict
```

### Приоритет загрузки
```python
plugin_priorities = {
    'hotkeys': 2,  # Загружается рано, но после системных плагинов
}
```

## Интеграция

### В PluginManager

```python
# Автоматическая загрузка
PLUGIN_CLASSES = {
    "hotkeys": HotkeysPlugin,
}
```

### В GUI интерфейсах

```python
def _setup_hotkeys(self):
    """Настройка горячих клавиш через HotkeysPlugin"""
    hotkeys_plugin = self.plugin_manager.get_plugin("hotkeys")
    if hotkeys_plugin:
        widgets = [self.entry1, self.text1, self.entry2]
        success_count = hotkeys_plugin.register_multiple_widgets(widgets)
        print(f"🎮 Настроено {success_count} виджетов")
```

## Конфигурация

### Автоматическое определение платформы

```python
# Автоматически определяется при инициализации
self.is_macos = platform.system() == "Darwin"
self.modifier_key = "Command" if self.is_macos else "Control"
```

### Статистика

```python
stats = hotkeys_plugin.get_statistics()
# {
#   "registered_widgets": 5,
#   "platform": "Darwin",
#   "modifier_key": "Command",
#   "is_macos": True
# }
```

## Методы плагина

### `register_widget(widget, widget_type="auto")`

Регистрирует один виджет для поддержки горячих клавиш.

**Параметры:**
- `widget` — виджет tkinter (Entry или Text)
- `widget_type` — тип виджета ("entry", "text", "auto")

**Возвращает:** `bool` — успешность регистрации

### `register_multiple_widgets(widgets)`

Регистрирует несколько виджетов сразу.

**Параметры:**
- `widgets` — список виджетов

**Возвращает:** `int` — количество успешно зарегистрированных виджетов

### `get_statistics()`

Возвращает статистику плагина.

**Возвращает:** `dict` с информацией о зарегистрированных виджетах и платформе

## Использование

### Пример интеграции в интерфейс

```python
class MyInterface:
    def __init__(self, parent_frame, plugin_manager):
        self.plugin_manager = plugin_manager
        self.setup_ui()
        self._setup_hotkeys()

    def setup_ui(self):
        # Создание виджетов
        self.entry1 = ttk.Entry(...)
        self.text1 = tk.Text(...)

    def _setup_hotkeys(self):
        hotkeys_plugin = self.plugin_manager.get_plugin("hotkeys")
        if hotkeys_plugin:
            widgets = [self.entry1, self.text1]
            hotkeys_plugin.register_multiple_widgets(widgets)
```

### Пример регистрации отдельных виджетов

```python
# Регистрация Entry
success = hotkeys_plugin.register_widget(my_entry, "entry")

# Регистрация Text
success = hotkeys_plugin.register_widget(my_text, "text")

# Автоопределение типа
success = hotkeys_plugin.register_widget(widget, "auto")
```

## Решение проблем

### Горячие клавиши не работают

1. **Проверьте загрузку плагина:**
```python
hotkeys_plugin = plugin_manager.get_plugin("hotkeys")
if not hotkeys_plugin:
    print("❌ HotkeysPlugin не загружен")
```

2. **Проверьте регистрацию виджетов:**
```python
stats = hotkeys_plugin.get_statistics()
print(f"Зарегистрировано: {stats['registered_widgets']} виджетов")
```

3. **Проверьте платформу:**
```python
print(f"Платформа: {stats['platform']}")
print(f"Модификатор: {stats['modifier_key']}")
```

### Конфликты с системными горячими клавишами

HotkeysPlugin автоматически отключает стандартные привязки tkinter на macOS, чтобы избежать конфликтов.

### Проблемы с Focus

Убедитесь, что виджет имеет фокус перед использованием горячих клавиш.

## Технические детали

### Специальная обработка macOS

```python
def _setup_macos_widget(self, widget):
    # Отключение стандартных привязок
    widget.unbind_class("Text", "<Command-a>")
    widget.unbind_class("Entry", "<Command-a>")
    # ... другие привязки
```

### Обработка ошибок

Все методы обработки горячих клавиш защищены от ошибок и возвращают "break" для предотвращения дальнейшей обработки события.

### Производительность

- Минимальное влияние на производительность
- Ленивая инициализация
- Эффективная привязка событий

## Журналирование

Плагин логирует все важные события:

```
🎮 Горячие клавиши настроены для Command
✅ Виджет entry зарегистрирован для горячих клавиш
✅ Виджет text зарегистрирован для горячих клавиш
📊 Скопирован текст (25 символов)
📊 Вставлен текст (10 символов)
```

## Заключение

HotkeysPlugin обеспечивает единообразную и надежную поддержку горячих клавиш во всех интерфейсах приложения, с особым вниманием к совместимости с macOS.
