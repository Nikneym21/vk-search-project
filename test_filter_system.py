#!/usr/bin/env python3
"""
Тест фильтрации через всю систему плагинов с реальными ключевыми словами
"""

import sys
import os
import json
import pandas as pd
import asyncio

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.plugin_manager import PluginManager

def load_csv_as_posts(csv_file):
    """Загружает CSV файл и конвертирует в формат постов"""
    print(f"📁 Загружаем {csv_file}...")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"   Загружено {len(df)} строк")
        
        # Конвертируем в формат постов (как возвращает VK API)
        posts = []
        for _, row in df.iterrows():
            post = {
                'id': row.get('id', 0),
                'owner_id': row.get('owner_id', 0),
                'text': row.get('text', ''),
                'date': row.get('date', 0),
                'likes': {'count': row.get('likes', 0)},
                'comments': {'count': row.get('comments', 0)},
                'reposts': {'count': row.get('reposts', 0)},
                'views': {'count': row.get('views', 0)}
            }
            posts.append(post)
        
        print(f"   Конвертировано в {len(posts)} постов")
        return posts
        
    except Exception as e:
        print(f"❌ Ошибка загрузки {csv_file}: {e}")
        return []

def load_meta_data(meta_file):
    """Загружает метаданные из meta.json файла"""
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return meta
    except Exception as e:
        print(f"❌ Ошибка загрузки {meta_file}: {e}")
        return None

async def test_filter_system():
    """Тест фильтрации через всю систему"""
    print("🧪 Тест фильтрации через систему плагинов")
    
    # Инициализируем PluginManager
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Проверяем наличие плагинов
    filter_plugin = pm.get_plugin('filter')
    if not filter_plugin:
        print("❌ FilterPlugin не найден")
        return
    
    print("✅ FilterPlugin загружен")
    
    # Загружаем метаданные
    meta_files = [
        'data/results/search_20250726_045350.meta.json',
        'data/results/search_20250726_051718.meta.json'
    ]
    
    all_keywords = []
    all_posts = []
    
    for meta_file in meta_files:
        meta = load_meta_data(meta_file)
        if meta:
            keywords = meta.get('keywords', [])
            csv_file = meta.get('filepath', '')
            expected_count = meta.get('count', 0)
            
            print(f"\n📋 Метаданные {meta_file}:")
            print(f"   Ожидаемый результат: {expected_count} постов")
            print(f"   Ключевых слов: {len(keywords)}")
            print(f"   Exact match: {meta.get('exact_match', False)}")
            
            # Загружаем посты из соответствующего CSV
            if csv_file and os.path.exists(csv_file):
                posts = load_csv_as_posts(csv_file)
                all_posts.extend(posts)
                all_keywords.extend(keywords)
                
                print(f"   Загружено постов: {len(posts)}")
    
    print(f"\n📊 Общие данные:")
    print(f"   Всего постов: {len(all_posts)}")
    print(f"   Всего ключевых слов: {len(all_keywords)}")
    
    # Убираем дубликаты ключевых слов
    unique_keywords = list(set(all_keywords))
    print(f"   Уникальных ключевых слов: {len(unique_keywords)}")
    
    # Показываем ключевые слова
    print(f"\n🔍 Ключевые слова:")
    for i, keyword in enumerate(unique_keywords[:10], 1):
        print(f"   {i}. {keyword}")
    if len(unique_keywords) > 10:
        print(f"   ... и еще {len(unique_keywords) - 10} ключевых слов")
    
    # Тестируем фильтрацию через систему
    print(f"\n🔍 Тест фильтрации через систему:")
    try:
        # Фильтруем с точным совпадением (как в meta.json)
        print("   Запуск параллельной фильтрации с exact_match=True...")
        filtered_posts_exact = await filter_plugin.filter_posts_comprehensive_parallel(
            all_posts, unique_keywords, exact_match=True
        )
        
        print(f"   ✅ Результат (exact_match=True): {len(filtered_posts_exact)} постов")
        
        # Фильтруем с частичным совпадением
        print("   Запуск параллельной фильтрации с exact_match=False...")
        filtered_posts_partial = await filter_plugin.filter_posts_comprehensive_parallel(
            all_posts, unique_keywords, exact_match=False
        )
        
        print(f"   ✅ Результат (exact_match=False): {len(filtered_posts_partial)} постов")
        
        # Показываем примеры отфильтрованных постов
        if filtered_posts_partial:
            print(f"\n📝 Примеры отфильтрованных постов:")
            for i, post in enumerate(filtered_posts_partial[:3]):
                text = post.get('text', '')[:100]
                owner_id = post.get('owner_id', 0)
                post_id = post.get('id', 0)
                print(f"   {i+1}. [ID: {owner_id}_{post_id}] {text}...")
        
        # Сравниваем с ожидаемыми результатами
        expected_total = 825 + 365  # Из meta.json файлов
        actual_exact = len(filtered_posts_exact)
        actual_partial = len(filtered_posts_partial)
        
        print(f"\n🎯 Сравнение с ожидаемыми результатами:")
        print(f"   Ожидалось (из meta.json): {expected_total} постов")
        print(f"   Получено (exact_match=True): {actual_exact} постов")
        print(f"   Получено (exact_match=False): {actual_partial} постов")
        print(f"   Разница (exact): {actual_exact - expected_total}")
        print(f"   Разница (partial): {actual_partial - expected_total}")
        
        # Анализируем результаты по ключевым словам
        print(f"\n📊 Анализ по ключевым словам (первые 5):")
        for keyword in unique_keywords[:5]:
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
    
    # Завершаем работу
    pm.shutdown_plugins()
    print(f"\n✅ Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_filter_system()) 