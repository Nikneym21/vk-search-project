from datetime import datetime

import pytz


def to_vk_timestamp(date_str: str, time_str: str, tz_name: str = "Europe/Moscow") -> int:
    """
    Преобразует дату и время пользователя в timestamp для VK API.
    date_str: '18.07.2025'
    time_str: '00:00'
    tz_name: 'Europe/Moscow' (Московское время UTC+3)
    """
    dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    tz = pytz.timezone(tz_name)
    return int(tz.localize(dt).timestamp())


def from_vk_timestamp(ts: int, tz_name: str = "Europe/Moscow") -> (str, str):
    """
    Преобразует timestamp VK API в строку даты и времени.
    Возвращает (date_str, time_str)
    """
    tz = pytz.timezone(tz_name)
    dt = datetime.fromtimestamp(ts, tz)
    return dt.strftime("%d.%m.%Y"), dt.strftime("%H:%M")
