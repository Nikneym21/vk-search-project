#!/usr/bin/env python3
"""
Тест строгой фильтрации VK API результатов
"""

import asyncio
import sys
import os

# Добавляем путь к src для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from plugins.vk_search.vk_search_plugin import VKSearchPlugin

def test_strict_filtering():
    """Тестирует строгую фильтрацию"""
    plugin = VKSearchPlugin()

    # Тестовые данные - реальные примеры из последнего поиска
    test_posts = [
        {
            'text': 'Эпоха пунических войн. Подстрекаемые Клавдием мамертинцы захватили в плен командующего местным карфагенским гарнизоном...',
            'link': 'https://vk.com/wall-216074633_3068'
        },
        {
            'text': '#Новости. Все, кто находились на борту Ан-24, разбившегося под Тындой, погибли...',
            'link': 'https://vk.com/wall-123456_001'
        },
        {
            'text': 'Нас не сломить. Ни пеплом, ни разрухой. А мягкий мишка — напоминание, что победа нужна ради будущего.',
            'link': 'https://vk.com/wall-789012_003'
        },
        {
            'text': 'Памяти павших, во имя живых!!! Миф или реальность Чеченской войны? Легендарный снайпер Володя-Якут...',
            'link': 'https://vk.com/wall-345678_004'
        },
        {
            'text': 'Добро всегда найдёт себе место — даже на передовой. Солдаты помогают мирным жителям.',
            'link': 'https://vk.com/wall-567890_005'
        }
    ]

    # Тестовые ключевые слова
    keywords = [
        "Нас не сломить. Ни пеплом, ни разрухой.",
        "Добро всегда найдёт себе место — даже на передовой.",
        "Лис передает всем доброе утро"
    ]

    print("🔍 Тестирование строгой фильтрации...")
    print(f"Исходное количество постов: {len(test_posts)}")
    print(f"Ключевые слова: {keywords}")
    print()

    # Тестируем строгую фильтрацию
    filtered_posts = plugin._strict_local_filter(test_posts, keywords, exact_match=True)

    print(f"После строгой фильтрации: {len(filtered_posts)} постов")
    print()

    for i, post in enumerate(filtered_posts, 1):
        print(f"Пост {i}:")
        print(f"  Текст: {post['text'][:100]}...")
        print(f"  Совпадения: {post.get('keywords_matched', [])}")
        print()

    # Проверка ожидаемых результатов
    expected_count = 2  # Должны пройти посты 3 и 5
    if len(filtered_posts) == expected_count:
        print("✅ Тест ПРОЙДЕН: фильтрация работает корректно")
    else:
        print(f"❌ Тест ПРОВАЛЕН: ожидалось {expected_count}, получено {len(filtered_posts)}")

    return filtered_posts

if __name__ == "__main__":
    test_strict_filtering()
