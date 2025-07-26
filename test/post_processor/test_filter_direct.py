#!/usr/bin/env python3
"""
Тест прямого использования FilterPlugin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.plugins.post_processor.filter.filter_plugin import FilterPlugin
from src.plugins.post_processor.deduplication.deduplication_plugin import DeduplicationPlugin

def test_filter_plugin():
    """Тест FilterPlugin"""
    print("🧪 Тест FilterPlugin")
    
    # Инициализируем плагины
    filter_plugin = FilterPlugin()
    deduplication_plugin = DeduplicationPlugin()
    
    print("✅ FilterPlugin инициализирован успешно")
    print("✅ DeduplicationPlugin инициализирован успешно")
    
    # Создаем тестовые данные
    test_posts = [
        {
            'id': 1,
            'owner_id': -123456,
            'text': 'Тестовый пост 1',
            'date': 1640995200,
            'likes': {'count': 10},
            'comments': {'count': 5},
            'reposts': {'count': 2},
            'views': {'count': 100}
        },
        {
            'id': 2,
            'owner_id': -123456,
            'text': 'Тестовый пост 2',
            'date': 1640995200,
            'likes': {'count': 15},
            'comments': {'count': 8},
            'reposts': {'count': 3},
            'views': {'count': 150}
        },
        {
            'id': 1,
            'owner_id': -123456,
            'text': 'Тестовый пост 1',  # Дубликат
            'date': 1640995200,
            'likes': {'count': 10},
            'comments': {'count': 5},
            'reposts': {'count': 2},
            'views': {'count': 100}
        },
        {
            'id': 3,
            'owner_id': -789012,
            'text': 'Другой пост',
            'date': 1640995200,
            'likes': {'count': 20},
            'comments': {'count': 12},
            'reposts': {'count': 4},
            'views': {'count': 200}
        }
    ]
    
    print(f"📊 Тестовые данные: {len(test_posts)} постов")
    
    # Тест 1: Фильтрация по ключевым словам
    print("\n🔍 Тест 1: Фильтрация по ключевым словам")
    keywords = ['тестовый', 'пост']
    filtered_posts = filter_plugin.filter_posts_by_multiple_keywords(
        test_posts, keywords, exact_match=False
    )
    print(f"Результат: {len(filtered_posts)} отфильтрованных постов")
    
    for i, post in enumerate(filtered_posts):
        print(f"  {i+1}. ID: {post['id']}, Owner: {post['owner_id']}, Text: {post['text'][:50]}...")
    
    # Тест 2: Удаление дубликатов
    print("\n🔍 Тест 2: Удаление дубликатов")
    unique_posts = deduplication_plugin.remove_duplicates_by_link_hash(test_posts)
    print(f"Результат: {len(unique_posts)} уникальных постов")
    
    for i, post in enumerate(unique_posts):
        print(f"  {i+1}. ID: {post['id']}, Owner: {post['owner_id']}, Text: {post['text'][:50]}...")
    
    filter_plugin.shutdown()
    deduplication_plugin.shutdown()
    print("\n✅ Тестирование завершено успешно")

def main():
    """Основная функция"""
    test_filter_plugin()

if __name__ == "__main__":
    main() 