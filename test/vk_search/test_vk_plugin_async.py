import asyncio
from src.plugins.vk_search.vk_search_plugin import VKSearchPlugin
import os
import csv
from src.plugins.vk_search.vk_time_utils import to_vk_timestamp, from_vk_timestamp

def get_default_token():
    token_path = os.path.join('config', 'vk_token.txt')
    if os.path.exists(token_path):
        with open(token_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line
    return ''

async def test_vk_plugin():
    plugin = VKSearchPlugin()
    plugin.config["access_token"] = get_default_token()
    plugin.initialize()
    queries = ["Наши бойцы в зоне СВО. Сильные, спокойные, собранные. Делают свою работу"]
    # Пример: 18.07.2025 00:00 - 19.07.2025 23:59 (Moscow)
    start_date = "18.07.2025"
    start_time = "00:00"
    end_date = "19.07.2025"
    end_time = "23:59"
    start_ts = to_vk_timestamp(start_date, start_time)
    end_ts = to_vk_timestamp(end_date, end_time)
    results = await plugin.search_multiple_queries(
        queries, start_ts, end_ts, exact_match=True, minus_words=None
    )
    print(f"Уникальных постов: {len(results)}")
    if results:
        print("Пример поста:", results[0])
        # Пример обратного преобразования
        date_str, time_str = from_vk_timestamp(results[0]["timestamp"])
        print(f"Дата: {date_str}, Время: {time_str}")
        # Экспорт в CSV
        with open('vk_plugin_unique_posts.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print("Экспортировано в vk_plugin_unique_posts.csv")

if __name__ == "__main__":
    asyncio.run(test_vk_plugin()) 