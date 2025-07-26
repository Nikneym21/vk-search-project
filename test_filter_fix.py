#!/usr/bin/env python3
"""
Тест исправления FilterPlugin
"""

import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from plugins.filter.filter_plugin import FilterPlugin

def test_filter_plugin():
    """Тест FilterPlugin"""
    print("🧪 Тест FilterPlugin")
    
    # Создаем плагин
    filter_plugin = FilterPlugin()
    filter_plugin.initialize()
    
    # Тестовые данные
    test_posts = [
        {
            'id': 1,
            'owner_id': 123,
            'text': 'Это тестовый пост с ключевым словом',
            'date': 1640995200
        },
        {
            'id': 2,
            'owner_id': 456,
            'text': 'Другой пост без ключевых слов',
            'date': 1640995200
        },
        {
            'id': 3,
            'owner_id': 789,
            'text': 'Еще один пост с ключевым словом',
            'date': 1640995200
        }
    ]
    
    test_keywords = ['ключевым']
    
    print(f"📊 Тестовые данные:")
    print(f"   Постов: {len(test_posts)}")
    print(f"   Ключевых слов: {len(test_keywords)}")
    
    # Тестируем извлечение текста
    print(f"\n🔍 Тест извлечения текста:")
    for i, post in enumerate(test_posts):
        text = filter_plugin._extract_post_text(post)
        print(f"   {i+1}. {text}")
    
    # Тестируем проверку ключевых слов
    print(f"\n🔍 Тест проверки ключевых слов:")
    for keyword in test_keywords:
        for i, post in enumerate(test_posts):
            text = filter_plugin._extract_post_text(post)
            match = filter_plugin._check_keyword_match(text, keyword, exact_match=False)
            print(f"   Пост {i+1}, ключ '{keyword}': {match}")
    
    # Тестируем фильтрацию
    print(f"\n🔍 Тест фильтрации:")
    try:
        import asyncio
        
        async def test_async():
            filtered = await filter_plugin.filter_posts_comprehensive_parallel(
                test_posts, test_keywords, exact_match=False
            )
            return filtered
        
        filtered = asyncio.run(test_async())
        
        print(f"✅ Результат фильтрации:")
        print(f"   Исходных постов: {len(test_posts)}")
        print(f"   Отфильтрованных постов: {len(filtered)}")
        
        for i, post in enumerate(filtered):
            print(f"   {i+1}. {post.get('text', '')[:50]}...")
            
    except Exception as e:
        print(f"❌ Ошибка фильтрации: {e}")
        import traceback
        traceback.print_exc()
    
    filter_plugin.shutdown()
    print(f"\n✅ Тест завершен")

if __name__ == "__main__":
    test_filter_plugin() 