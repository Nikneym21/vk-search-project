# VK Time Utils - Утилиты работы с временем для VK API

## Описание
Модуль для конвертации дат и времени между пользовательским форматом и timestamp для VK API. Поддерживает различные часовые пояса с приоритетом московского времени.

## Основные функции

### `to_vk_timestamp(date_str, time_str, tz_name="Europe/Moscow")`
Преобразует дату и время пользователя в timestamp для VK API.

**Параметры:**
- `date_str` (str): Дата в формате "DD.MM.YYYY" (например, "24.07.2025")
- `time_str` (str): Время в формате "HH:MM" (например, "14:30")
- `tz_name` (str): Часовой пояс, по умолчанию "Europe/Moscow" (UTC+3)

**Возвращает:**
- `int`: Unix timestamp для VK API

**Пример:**
```python
from src.plugins.vk_search.vk_time_utils import to_vk_timestamp

# Московское время (по умолчанию)
timestamp = to_vk_timestamp("24.07.2025", "14:30")
# timestamp = 1753354200

# Другой часовой пояс
timestamp = to_vk_timestamp("24.07.2025", "14:30", "Asia/Vladivostok")
```

### `from_vk_timestamp(ts, tz_name="Europe/Moscow")`
Преобразует timestamp VK API обратно в читаемую дату и время.

**Параметры:**
- `ts` (int): Unix timestamp от VK API
- `tz_name` (str): Часовой пояс, по умолчанию "Europe/Moscow" (UTC+3)

**Возвращает:**
- `tuple`: (date_str, time_str) в формате ("DD.MM.YYYY", "HH:MM")

**Пример:**
```python
from src.plugins.vk_search.vk_time_utils import from_vk_timestamp

date_str, time_str = from_vk_timestamp(1753354200)
# date_str = "24.07.2025", time_str = "14:30"
```

## Поддерживаемые часовые пояса
- **Europe/Moscow** (UTC+3) - по умолчанию, московское время
- **Asia/Vladivostok** (UTC+10) - владивостокское время
- **Europe/London** (UTC+0/+1) - лондонское время
- **America/New_York** (UTC-5/-4) - нью-йоркское время
- И другие часовые пояса pytz

## Интеграция с VKSearchPlugin
Модуль автоматически используется в `VKSearchPlugin` для корректной обработки дат поиска:

```python
# В VKSearchPlugin
from src.plugins.vk_search.vk_time_utils import to_vk_timestamp

# Преобразование пользовательского времени для API
start_ts = to_vk_timestamp("24.07.2025", "00:00")  # Московское время
end_ts = to_vk_timestamp("24.07.2025", "23:59")
```

## Архитектурное соответствие
✅ **Соответствует архитектуре:** Использует московское время как стандарт
✅ **Централизованное управление:** Единая точка конвертации времени
✅ **Гибкость:** Поддержка различных часовых поясов при необходимости
