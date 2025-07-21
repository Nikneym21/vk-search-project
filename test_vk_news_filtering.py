import sys
sys.path.append('/Users/dvofis/Desktop/Проекты/Скрипт таблиц')
import asyncio
from datetime import datetime
import pytz
from typing import List
import os
import csv

# Импортируем AsyncVKSearch из эталонного проекта
from async_vk_integration import AsyncVKSearch

def msk_time_from_timestamp(ts):
    moscow_tz = pytz.timezone('Europe/Moscow')
    return datetime.fromtimestamp(ts, tz=pytz.utc).astimezone(moscow_tz)

def filter_posts_by_time_and_exact(posts: List[dict], query: str, start_time: str, end_time: str):
    """Фильтрует посты по времени (часы:минуты) по Москве и по точному вхождению текста"""
    filtered = []
    for post in posts:
        ts = post.get('timestamp')
        if not isinstance(ts, int):
            continue  # пропускаем посты без timestamp
        dt_msk = msk_time_from_timestamp(ts)
        post_time = dt_msk.strftime('%H:%M')
        # Точное вхождение (без учета регистра)
        if start_time <= post_time <= end_time and query.lower() in post.get('post_text', '').lower():
            filtered.append(post)
    return filtered

def get_default_token():
    token_path = os.path.join('config', 'vk_token.txt')
    if os.path.exists(token_path):
        with open(token_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line
    return ''

async def main():
    default_token = get_default_token()
    default_query = 'Наши бойцы в зоне СВО. Сильные, спокойные, собранные. Делают свою работу'
    token = default_token
    queries = [default_query]
    start_date = '18.07.2025'
    end_date = '19.07.2025'
    start_time = '00:00'
    end_time = '23:59'
    exact_match = True

    # Вычисляем start_timestamp и end_timestamp с учётом времени
    moscow_tz = pytz.timezone('Europe/Moscow')
    start_dt = datetime.strptime(f"{start_date} {start_time}", "%d.%m.%Y %H:%M")
    end_dt = datetime.strptime(f"{end_date} {end_time}", "%d.%m.%Y %H:%M")
    start_ts = int(moscow_tz.localize(start_dt).timestamp())
    end_ts = int(moscow_tz.localize(end_dt).timestamp())

    async with AsyncVKSearch(token, max_concurrent=3) as searcher:
        print(f'\nПолучаем посты по фразе {queries[0]} за период {start_date} {start_time} - {end_date} {end_time}...')
        posts = await searcher.search_multiple_queries(queries, start_ts, end_ts, exact_match)
        print(f'Всего получено: {len(posts)} постов')
        if posts:
            print('Пример поста до фильтрации:')
            print(posts[0])
        # Сохраняем все посты до фильтрации
        with open('all_posts_raw.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=posts[0].keys())
            writer.writeheader()
            writer.writerows(posts)
        # Фильтрация только по точному вхождению
        filtered = [post for post in posts if default_query.lower() in post.get('post_text', '').lower()]
        print(f'\nПосле фильтрации по точному вхождению: {len(filtered)} постов')
        if filtered:
            print('Пример поста после фильтрации:')
            post = filtered[0]
            dt_msk = msk_time_from_timestamp(post["timestamp"])
            print(f"Дата/время по Москве: {dt_msk.strftime('%d.%m.%Y %H:%M')}")
            print(post)
        # Сохраняем отфильтрованные посты
        if filtered:
            with open('filtered_posts.csv', 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=filtered[0].keys())
                writer.writeheader()
                writer.writerows(filtered)

if __name__ == "__main__":
    asyncio.run(main()) 