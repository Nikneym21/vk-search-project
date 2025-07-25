#!/usr/bin/env python3
"""
Пример использования FilterPlugin для локальной фильтрации по ключевым фразам
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к src для импорта плагинов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.plugins.filter.filter_plugin import FilterPlugin


def main():
    """Пример использования FilterPlugin для локальной фильтрации"""
    
    # Инициализация плагина
    filter_plugin = FilterPlugin()
    filter_plugin.initialize()
    
    # Тестовые данные
    test_posts = [
        {
            "text": "Даже в боевых условиях человек остаётся человеком. 🎯 #война",
            "owner_id": 1,
            "id": 100
        },
        {
            "text": "Лис передает всем доброе утро! ☀️ #утро",
            "owner_id": 2,
            "id": 200
        },
        {
            "text": "Привет родной Бурятии от штурмовиков танковой бригады с Южно-Донецкого направления 🇷🇺",
            "owner_id": 3,
            "id": 300
        },
        {
            "text": "Обычный пост без ключевых слов",
            "owner_id": 4,
            "id": 400
        },
        {
            "text": "Даже в боевых условиях человек остаётся человеком. Дубликат",
            "owner_id": 1,
            "id": 100  # Дубликат
        }
    ]
    
    print(f"📊 Исходные данные: {len(test_posts)} постов")
    
    # 1. Фильтрация уникальных постов
    print("\n🔍 1. Фильтрация уникальных постов:")
    unique_posts = filter_plugin.filter_unique_posts(test_posts)
    print(f"   Результат: {len(unique_posts)} уникальных постов")
    
    # 2. Фильтрация по ключевому слову без очистки текста
    print("\n🔍 2. Фильтрация по ключевому слову (без очистки):")
    keyword_filtered = filter_plugin.filter_posts_by_keyword(
        unique_posts, 
        "Даже в боевых условиях", 
        exact_match=True
    )
    print(f"   Результат: {len(keyword_filtered)} постов с ключевым словом")
    
    # 3. Фильтрация с очисткой текста
    print("\n🔍 3. Фильтрация с очисткой текста:")
    cleaned_filtered = filter_plugin.filter_posts_by_keyword_with_text_cleaning(
        unique_posts,
        "Даже в боевых условиях человек остаётся человеком",
        exact_match=True
    )
    print(f"   Результат: {len(cleaned_filtered)} постов после очистки текста")
    
    # 4. Фильтрация по нескольким ключевым словам
    print("\n🔍 4. Фильтрация по нескольким ключевым словам:")
    keywords = ["Даже в боевых условиях", "Лис передает", "Привет родной"]
    multi_filtered = filter_plugin.filter_posts_by_multiple_keywords(
        unique_posts,
        keywords,
        exact_match=True,
        use_text_cleaning=True
    )
    print(f"   Результат: {len(multi_filtered)} постов по {len(keywords)} ключам")
    
    # 5. Комплексная фильтрация
    print("\n🔍 5. Комплексная фильтрация:")
    comprehensive_filtered = filter_plugin.filter_posts_comprehensive(
        posts=test_posts,
        keywords=["Даже в боевых условиях", "Лис передает"],
        exact_match=True,
        use_text_cleaning=True,
        remove_duplicates=True
    )
    print(f"   Результат: {len(comprehensive_filtered)} постов после комплексной фильтрации")
    
    # Выводим детали результатов
    print("\n📋 Детали результатов комплексной фильтрации:")
    for i, post in enumerate(comprehensive_filtered, 1):
        print(f"   {i}. owner_id={post['owner_id']}, id={post['id']}")
        print(f"      Текст: {post['text'][:50]}...")
    
    # 6. Фильтрация без очистки текста
    print("\n🔍 6. Фильтрация без очистки текста:")
    no_cleaning_filtered = filter_plugin.filter_posts_comprehensive(
        posts=test_posts,
        keywords=["Даже в боевых условиях человек остаётся человеком"],
        exact_match=True,
        use_text_cleaning=False,
        remove_duplicates=True
    )
    print(f"   Результат: {len(no_cleaning_filtered)} постов без очистки текста")
    
    # Завершение работы плагина
    filter_plugin.shutdown()
    
    print(f"\n✅ Пример использования FilterPlugin завершен!")
    print(f"📝 Примечание: Фильтрация по дате происходит на уровне API, этот плагин отвечает только за локальную фильтрацию по ключевым фразам.")


if __name__ == "__main__":
    main() 