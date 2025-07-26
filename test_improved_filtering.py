#!/usr/bin/env python3
"""
Тест улучшенной строгой фильтрации VKSearchPlugin
Проверяем соответствие результатов эталонным данным
"""

import asyncio
import sys
import os

# Добавляем корневую директорию в path
sys.path.insert(0, os.path.abspath('.'))

from src.plugins.vk_search.vk_search_plugin import VKSearchPlugin


async def test_improved_filtering():
    """Тестируем улучшенную фильтрацию с реальными данными"""

    print("🧪 Тест улучшенной строгой фильтрации VKSearchPlugin")
    print("=" * 60)

    # Создаем плагин
    vk_search_plugin = VKSearchPlugin()

    # Тестовые данные по образцу эталона
    posts = [
        # Должны ПРОЙТИ фильтрацию (из эталона)
        {
            "text": "Лис передает всем доброе утро",
            "link": "https://vk.com/wall-25943575_1158294"
        },
        {
            "text": "Лис передает всем доброе утро",
            "link": "https://vk.com/wall-125866183_516874"
        },
        {
            "text": "Даже в боевых условиях человек остаётся человеком.\nДобро всегда найдёт себе место — даже на передовой.",
            "link": "https://vk.com/wall299788145_3101"
        },
        {
            "text": "Нас не сломить. Ни пеплом, ни разрухой.\nА мягкий мишка — напоминание, что победа нужна ради будущего.",
            "link": "https://vk.com/wall-123456789_1234"
        },

        # Должны НЕ ПРОЙТИ фильтрацию (нерелевантные)
        {
            "text": "Эпоха пунических войн и другая история без наших ключевых слов",
            "link": "https://vk.com/wall-216074633_3068"
        },
        {
            "text": "Какой-то пост про новости без наших фраз",
            "link": "https://vk.com/wall-987654321_5678"
        }
    ]

    # Ключевые слова из нашего поиска
    keywords = [
        "Лис передает всем доброе утро",
        "Даже в боевых условиях человек остаётся человеком.",
        "Добро всегда найдёт себе место — даже на передовой.",
        "Нас не сломить. Ни пеплом, ни разрухой.",
        "А мягкий мишка — напоминание, что победа нужна ради будущего."
    ]

    print(f"📊 Исходные данные:")
    print(f"   Постов: {len(posts)}")
    print(f"   Ключевых слов: {len(keywords)}")
    print()

    # Тестируем фильтрацию
    filtered_posts = vk_search_plugin._strict_local_filter(posts, keywords, exact_match=True)

    print(f"📈 Результаты фильтрации:")
    print(f"   Исходно: {len(posts)} постов")
    print(f"   Отфильтровано: {len(filtered_posts)} постов")
    print()

    # Проверяем результаты
    print("✅ Прошедшие фильтрацию посты:")
    for i, post in enumerate(filtered_posts, 1):
        print(f"   {i}. {post['text'][:50]}...")
        print(f"      Совпадения: {post.get('keywords_matched', [])}")
        print()

    # Ожидаемые результаты
    expected_count = 4  # Должны пройти первые 4 поста

    if len(filtered_posts) == expected_count:
        print("🎉 ТЕСТ ПРОЙДЕН!")
        print(f"   Ожидалось: {expected_count} постов")
        print(f"   Получено: {len(filtered_posts)} постов")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН!")
        print(f"   Ожидалось: {expected_count} постов")
        print(f"   Получено: {len(filtered_posts)} постов")

    return len(filtered_posts) == expected_count


if __name__ == "__main__":
    result = asyncio.run(test_improved_filtering())
    print(f"\n🏁 Результат теста: {'ПРОЙДЕН' if result else 'НЕ ПРОЙДЕН'}")
