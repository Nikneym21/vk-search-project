#!/usr/bin/env python3
"""
Тест полного пайплайна: API поиск → строгая фильтрация → экспорт CSV
"""

import asyncio
import sys
import os
from datetime import datetime
import time

# Добавляем путь к src для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_full_pipeline():
    """Тестирует полный пайплайн поиска"""
    print("🔄 Инициализация тестового пайплайна...")

    from core.plugin_manager import PluginManager

    # Создаем менеджер плагинов
    plugin_manager = PluginManager()
    plugin_manager.load_plugins()  # Убираем await

    print(f"✅ Загружено {len(plugin_manager.plugins)} плагинов")

    # Тестовые параметры поиска
    test_keywords = [
        "Нас не сломить. Ни пеплом, ни разрухой.",
        "Добро всегда найдёт себе место — даже на передовой."
    ]

    # Даты для поиска (последние посты)
    start_date = "24.07.2025"
    start_time = "00:00"
    end_date = "25.07.2025"
    end_time = "23:59"

    print(f"🔍 Поиск по ключевым словам: {test_keywords}")
    print(f"📅 Период: {start_date} {start_time} - {end_date} {end_time}")
    print()

    # Тест 1: Поиск БЕЗ строгой локальной фильтрации
    print("=== ТЕСТ 1: Поиск БЕЗ строгой фильтрации ===")

    start_time = time.time()

    result1 = await plugin_manager.coordinate_full_search(
        keywords=test_keywords,
        api_keywords=test_keywords,
        start_ts=int(datetime(2025, 7, 24, 0, 0).timestamp()),
        end_ts=int(datetime(2025, 7, 25, 23, 59).timestamp()),
        exact_match=True,
        minus_words=[],
        start_date=start_date,
        start_time="00:00",
        end_date=end_date,
        end_time="23:59",
        disable_local_filtering=True  # Отключаем локальную фильтрацию
    )

    elapsed1 = time.time() - start_time

    print(f"⏱️  Время выполнения: {elapsed1:.1f}с")
    print(f"📊 Результат БЕЗ фильтрации: {result1.get('posts_count', 0)} постов")
    print(f"📁 Файл: {result1.get('filepath', 'не создан')}")
    print()

    # Тест 2: Поиск С строгой локальной фильтрацией
    print("=== ТЕСТ 2: Поиск С строгой фильтрацией ===")

    start_time = time.time()

    result2 = await plugin_manager.coordinate_full_search(
        keywords=test_keywords,
        api_keywords=test_keywords,
        start_ts=int(datetime(2025, 7, 24, 0, 0).timestamp()),
        end_ts=int(datetime(2025, 7, 25, 23, 59).timestamp()),
        exact_match=True,
        minus_words=[],
        start_date=start_date,
        start_time="00:00",
        end_date=end_date,
        end_time="23:59",
        disable_local_filtering=False  # Включаем локальную фильтрацию
    )

    elapsed2 = time.time() - start_time

    print(f"⏱️  Время выполнения: {elapsed2:.1f}с")
    print(f"📊 Результат С фильтрацией: {result2.get('posts_count', 0)} постов")
    print(f"📁 Файл: {result2.get('filepath', 'не создан')}")
    print()

    # Анализ результатов
    print("=== АНАЛИЗ РЕЗУЛЬТАТОВ ===")

    posts_without_filter = result1.get('posts_count', 0)
    posts_with_filter = result2.get('posts_count', 0)

    if posts_without_filter > posts_with_filter:
        filtered_out = posts_without_filter - posts_with_filter
        filter_efficiency = (filtered_out / posts_without_filter) * 100 if posts_without_filter > 0 else 0

        print(f"✅ Строгая фильтрация РАБОТАЕТ!")
        print(f"📉 Отфильтровано {filtered_out} нерелевантных постов ({filter_efficiency:.1f}%)")
    elif posts_without_filter == posts_with_filter:
        print("⚠️  Фильтрация не изменила количество постов (возможно, все посты релевантны)")
    else:
        print("❌ Странная ситуация: с фильтрацией постов больше чем без неё")

    print()

    # Проверка CSV файлов
    print("=== ПРОВЕРКА CSV ФАЙЛОВ ===")

    for i, result in enumerate([result1, result2], 1):
        filepath = result.get('filepath')
        if filepath and os.path.exists(filepath):
            print(f"📄 Тест {i} - файл создан: {filepath}")

            # Читаем первые несколько строк
            try:
                import pandas as pd
                df = pd.read_csv(filepath)
                print(f"   Строк в CSV: {len(df)}")
                print(f"   Колонки: {list(df.columns)}")

                # Проверяем поле keywords_matched
                if 'keywords_matched' in df.columns:
                    non_empty_keywords = df[df['keywords_matched'].notna() & (df['keywords_matched'] != '')].shape[0]
                    print(f"   Посты с keywords_matched: {non_empty_keywords}")

                    # Показываем пример
                    sample = df[df['keywords_matched'].notna() & (df['keywords_matched'] != '')]['keywords_matched'].head(3)
                    if not sample.empty:
                        print(f"   Примеры keywords_matched:")
                        for idx, keywords in sample.items():
                            print(f"     - {keywords}")

            except Exception as e:
                print(f"   ❌ Ошибка чтения CSV: {e}")
        else:
            print(f"📄 Тест {i} - файл НЕ создан")

    print()
    print("🏁 Тестирование завершено!")

    # Завершаем плагины
    plugin_manager.shutdown_plugins()  # Убираем await

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
