#!/usr/bin/env python3
"""
Тест фильтрации с реальными сырыми данными
"""

import sys
import os
import json
import pandas as pd
import asyncio

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from plugins.filter.filter_plugin import FilterPlugin

def load_csv_as_posts(csv_file):
    """Загружает CSV файл и конвертирует в формат постов"""
    print(f"📁 Загружаем {csv_file}...")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"   Загружено {len(df)} строк")
        
        # Конвертируем в формат постов
        posts = []
        for _, row in df.iterrows():
            post = {
                'id': row.get('id', 0),
                'owner_id': row.get('owner_id', 0),
                'text': row.get('text', ''),
                'date': row.get('date', 0),
                'likes': row.get('likes', 0),
                'comments': row.get('comments', 0),
                'reposts': row.get('reposts', 0),
                'views': row.get('views', 0)
            }
            posts.append(post)
        
        print(f"   Конвертировано в {len(posts)} постов")
        return posts
        
    except Exception as e:
        print(f"❌ Ошибка загрузки {csv_file}: {e}")
        return []

async def test_filter_with_real_data():
    """Тест фильтрации с реальными данными"""
    print("🧪 Тест фильтрации с реальными данными")
    
    # Создаем плагин
    filter_plugin = FilterPlugin()
    filter_plugin.initialize()
    
    # Загружаем данные из CSV файлов
    csv_files = [
        'search_20250726_045350.csv',
        'search_20250726_051718.csv'
    ]
    
    all_posts = []
    for csv_file in csv_files:
        posts = load_csv_as_posts(csv_file)
        all_posts.extend(posts)
    
    print(f"\n📊 Общие данные:")
    print(f"   Всего постов: {len(all_posts)}")
    
    # Тестовые ключевые слова (те же, что использовались в парсинге)
    test_keywords = [
        'Лис передает всем доброе утро',
        'Привет родной Бурятии от штурмовиков танковой бригады с Южно-Донецкого направления',
        'Даже в боевых условиях человек остаётся человеком.',
        'Враг не пройдет',
        'Слава Украине',
        'Героям слава'
    ]
    
    print(f"   Ключевых слов: {len(test_keywords)}")
    for i, keyword in enumerate(test_keywords, 1):
        print(f"   {i}. {keyword}")
    
    # Тестируем фильтрацию
    print(f"\n🔍 Тест фильтрации:")
    try:
        # Фильтруем с точным совпадением
        print("   Тест 1: Точное совпадение (exact_match=True)")
        filtered_exact = await filter_plugin.filter_posts_comprehensive_parallel(
            all_posts, test_keywords, exact_match=True
        )
        print(f"   Результат: {len(filtered_exact)} постов")
        
        # Фильтруем с частичным совпадением
        print("   Тест 2: Частичное совпадение (exact_match=False)")
        filtered_partial = await filter_plugin.filter_posts_comprehensive_parallel(
            all_posts, test_keywords, exact_match=False
        )
        print(f"   Результат: {len(filtered_partial)} постов")
        
        # Показываем примеры отфильтрованных постов
        if filtered_partial:
            print(f"\n📝 Примеры отфильтрованных постов:")
            for i, post in enumerate(filtered_partial[:5]):
                text = post.get('text', '')[:100]
                print(f"   {i+1}. {text}...")
        
        # Анализируем результаты по ключевым словам
        print(f"\n📊 Анализ по ключевым словам:")
        for keyword in test_keywords:
            keyword_posts = []
            for post in all_posts:
                text = filter_plugin._extract_post_text(post)
                if filter_plugin._check_keyword_match(text, keyword, exact_match=False):
                    keyword_posts.append(post)
            print(f"   '{keyword}': {len(keyword_posts)} постов")
            
    except Exception as e:
        print(f"❌ Ошибка фильтрации: {e}")
        import traceback
        traceback.print_exc()
    
    filter_plugin.shutdown()
    print(f"\n✅ Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_filter_with_real_data()) 