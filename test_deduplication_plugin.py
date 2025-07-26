#!/usr/bin/env python3
"""
Тест плагина дедупликации на реальных данных
"""

import sys
import os
import json
import pandas as pd
import asyncio

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from plugins.deduplication.deduplication_plugin import DeduplicationPlugin

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

def analyze_duplicates_manual(csv_file):
    """Ручной анализ дубликатов в CSV файле"""
    print(f"\n🔍 РУЧНОЙ АНАЛИЗ ДУБЛИКАТОВ: {csv_file}")
    print("="*60)
    
    try:
        df = pd.read_csv(csv_file)
        print(f"📊 Общая статистика:")
        print(f"   Всего строк: {len(df)}")
        
        # Анализируем дубликаты по разным полям
        print(f"\n📋 Анализ дубликатов:")
        
        # Дубликаты по (owner_id, id)
        df['post_key'] = df['owner_id'].astype(str) + '_' + df['id'].astype(str)
        duplicate_keys = df[df.duplicated(subset=['post_key'], keep=False)]
        print(f"   Дубликаты по (owner_id, id): {len(duplicate_keys)} строк")
        
        # Дубликаты по тексту
        text_duplicates = df[df.duplicated(subset=['text'], keep=False)]
        print(f"   Дубликаты по тексту: {len(text_duplicates)} строк")
        
        # Уникальные посты
        unique_posts = df.drop_duplicates(subset=['post_key'])
        print(f"   Уникальных постов: {len(unique_posts)}")
        
        # Показываем примеры дубликатов
        if len(duplicate_keys) > 0:
            print(f"\n📝 Примеры дубликатов:")
            duplicate_groups = df.groupby('post_key').filter(lambda x: len(x) > 1)
            for i, (key, group) in enumerate(duplicate_groups.groupby('post_key')[:3]):
                print(f"   Группа {i+1} (ключ: {key}): {len(group)} дубликатов")
                for j, row in group.iterrows():
                    text = row['text'][:50] + "..." if len(row['text']) > 50 else row['text']
                    print(f"     {j}: {text}")
        
        return {
            'total': len(df),
            'duplicate_keys': len(duplicate_keys),
            'text_duplicates': len(text_duplicates),
            'unique': len(unique_posts)
        }
        
    except Exception as e:
        print(f"❌ Ошибка анализа {csv_file}: {e}")
        return None

async def test_deduplication_method(csv_file, dedup_plugin, method):
    """Тест конкретного метода дедупликации"""
    print(f"\n🧪 ТЕСТ МЕТОДА: {method.upper()}")
    print("="*40)
    
    # Загружаем посты
    posts = load_csv_as_posts(csv_file)
    if not posts:
        print("❌ Не удалось загрузить посты")
        return None
    
    print(f"📊 Исходные данные:")
    print(f"   Всего постов: {len(posts)}")
    
    # Тестируем дедупликацию
    try:
        if method == "post_id":
            unique_posts = dedup_plugin.remove_duplicates_by_post_id(posts)
        elif method == "text":
            unique_posts = dedup_plugin.remove_duplicates_by_text(posts)
        elif method == "content_hash":
            unique_posts = dedup_plugin.remove_duplicates_by_content_hash(posts)
        else:
            print(f"❌ Неизвестный метод: {method}")
            return None
        
        removed_count = len(posts) - len(unique_posts)
        
        print(f"\n🎯 Результат:")
        print(f"   Исходных постов: {len(posts)}")
        print(f"   Уникальных постов: {len(unique_posts)}")
        print(f"   Удалено дубликатов: {removed_count}")
        print(f"   Процент уникальности: {(len(unique_posts) / len(posts) * 100):.1f}%")
        
        # Показываем примеры уникальных постов
        if unique_posts:
            print(f"\n📝 Примеры уникальных постов:")
            for i, post in enumerate(unique_posts[:3]):
                text = post.get('text', '')[:100]
                owner_id = post.get('owner_id', 0)
                post_id = post.get('id', 0)
                print(f"   {i+1}. [ID: {owner_id}_{post_id}] {text}...")
        
        return {
            'method': method,
            'total': len(posts),
            'unique': len(unique_posts),
            'removed': removed_count,
            'uniqueness_percent': (len(unique_posts) / len(posts) * 100)
        }
        
    except Exception as e:
        print(f"❌ Ошибка дедупликации: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_parallel_deduplication(csv_file, dedup_plugin, method):
    """Тест параллельной дедупликации"""
    print(f"\n🚀 ТЕСТ ПАРАЛЛЕЛЬНОЙ ДЕДУПЛИКАЦИИ: {method.upper()}")
    print("="*50)
    
    # Загружаем посты
    posts = load_csv_as_posts(csv_file)
    if not posts:
        print("❌ Не удалось загрузить посты")
        return None
    
    print(f"📊 Исходные данные:")
    print(f"   Всего постов: {len(posts)}")
    
    # Тестируем параллельную дедупликацию
    try:
        unique_posts = await dedup_plugin.remove_duplicates_parallel(posts, method=method)
        
        removed_count = len(posts) - len(unique_posts)
        
        print(f"\n🎯 Результат:")
        print(f"   Исходных постов: {len(posts)}")
        print(f"   Уникальных постов: {len(unique_posts)}")
        print(f"   Удалено дубликатов: {removed_count}")
        print(f"   Процент уникальности: {(len(unique_posts) / len(posts) * 100):.1f}%")
        
        return {
            'method': f"parallel_{method}",
            'total': len(posts),
            'unique': len(unique_posts),
            'removed': removed_count,
            'uniqueness_percent': (len(unique_posts) / len(posts) * 100)
        }
        
    except Exception as e:
        print(f"❌ Ошибка параллельной дедупликации: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_deduplication_plugin():
    """Основной тест плагина дедупликации"""
    print("🧪 Тест плагина дедупликации")
    
    # Создаем плагин
    dedup_plugin = DeduplicationPlugin()
    dedup_plugin.initialize()
    
    # Список файлов для тестирования
    csv_files = [
        'data/results/search_20250726_045350.csv',
        'data/results/search_20250726_051718.csv'
    ]
    
    all_results = []
    
    for csv_file in csv_files:
        print(f"\n{'='*60}")
        print(f"📋 ТЕСТ ФАЙЛА: {csv_file}")
        print(f"{'='*60}")
        
        # Ручной анализ дубликатов
        manual_stats = analyze_duplicates_manual(csv_file)
        
        # Тестируем все методы дедупликации
        methods = ["post_id", "text", "content_hash"]
        file_results = []
        
        for method in methods:
            result = await test_deduplication_method(csv_file, dedup_plugin, method)
            if result:
                file_results.append(result)
        
        # Тестируем параллельную дедупликацию
        parallel_result = await test_parallel_deduplication(csv_file, dedup_plugin, "post_id")
        if parallel_result:
            file_results.append(parallel_result)
        
        # Сводка по файлу
        if file_results:
            print(f"\n📊 СВОДКА ПО ФАЙЛУ:")
            for result in file_results:
                print(f"   {result['method']}: {result['total']} -> {result['unique']} "
                      f"({result['uniqueness_percent']:.1f}% уникальности)")
        
        all_results.extend(file_results)
    
    # Общая сводка
    print(f"\n{'='*60}")
    print(f"📊 ОБЩАЯ СВОДКА РЕЗУЛЬТАТОВ")
    print(f"{'='*60}")
    
    for result in all_results:
        print(f"📁 {result['method']}:")
        print(f"   Исходных: {result['total']} постов")
        print(f"   Уникальных: {result['unique']} постов")
        print(f"   Удалено: {result['removed']} дубликатов")
        print(f"   Уникальность: {result['uniqueness_percent']:.1f}%")
        print()
    
    # Завершаем работу
    dedup_plugin.shutdown()
    print(f"✅ Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_deduplication_plugin()) 