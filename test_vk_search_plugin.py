import asyncio
import json
import time
from datetime import datetime
from src.plugins.vk_search.vk_search_plugin import VKSearchPlugin

# Загрузка параметров из автосохранения
with open("data/parser_settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)

vk_token = settings.get("vk_token")
keywords = settings.get("keywords", "").split("\n")
keywords = [k.strip() for k in keywords if k.strip()]
start_date = settings.get("start_date")
end_date = settings.get("end_date")
start_time = settings.get("start_time", "00:00")
end_time = settings.get("end_time", "23:59")
exact_match = settings.get("exact_match", True)

# Преобразование даты и времени в timestamp (по Москве)
def to_vk_timestamp(date_str, time_str, tz_name="Europe/Moscow"):
    import pytz
    dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    tz = pytz.timezone(tz_name)
    return int(tz.localize(dt).timestamp())

start_ts = to_vk_timestamp(start_date, start_time)
end_ts = to_vk_timestamp(end_date, end_time)

async def test_vk_search():
    plugin = VKSearchPlugin()
    plugin.config["access_token"] = vk_token
    plugin.config["api_version"] = "5.131"
    plugin.initialize()  # Инициализация сессии
    await plugin._rate_limit()  # инициализация лимита
    try:
        print(f"Тестовый поиск: {keywords}, {start_date} {start_time} — {end_date} {end_time}, exact_match={exact_match}")
        results = await plugin.search_multiple_queries(keywords, start_ts, end_ts, exact_match=exact_match)
        print("Результаты поиска:", results)
        print(f"Всего постов: {len(results)}")
    except Exception as e:
        print("Ошибка теста VKSearchPlugin:", e)

if __name__ == "__main__":
    asyncio.run(test_vk_search()) 