#!/usr/bin/env python3
"""
Тест анализа дубликатов в CSV файлах
"""

import sys
import os
import json
import pandas as pd
from collections import Counter

def analyze_duplicates(csv_file):
    """Анализирует дубликаты в CSV файле"""
    print(f"\n🔍 АНАЛИЗ ДУБЛИКАТОВ: {csv_file}")
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

def test_filter_without_dedup(csv_file, keywords, exact_match=True):
    """Тест фильтрации без удаления дубликатов"""
    print(f"\n🧪 ТЕСТ ФИЛЬТРАЦИИ БЕЗ УДАЛЕНИЯ ДУБЛИКАТОВ")
    print("="*60)
    
    try:
        df = pd.read_csv(csv_file)
        posts = []
        
        for _, row in df.iterrows():
            post = {
                'id': row.get('id', 0),
                'owner_id': row.get('owner_id', 0),
                'text': row.get('text', ''),
                'date': row.get('date', 0)
            }
            posts.append(post)
        
        print(f"📊 Исходные данные:")
        print(f"   Всего постов: {len(posts)}")
        print(f"   Ключевых слов: {len(keywords)}")
        
        # Простая фильтрация без удаления дубликатов
        filtered_posts = []
        keyword_matches = {}
        
        for post in posts:
            text = post.get('text', '')
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    filtered_posts.append(post)
                    keyword_matches[keyword] = keyword_matches.get(keyword, 0) + 1
                    break  # Один пост может соответствовать только одному ключевому слову
        
        print(f"\n🎯 Результаты:")
        print(f"   Отфильтрованных постов: {len(filtered_posts)}")
        print(f"   Уникальных постов: {len(set((p['owner_id'], p['id']) for p in filtered_posts))}")
        
        if keyword_matches:
            print(f"\n📋 Совпадения по ключевым словам:")
            for keyword, count in sorted(keyword_matches.items(), key=lambda x: x[1], reverse=True):
                print(f"   '{keyword}': {count} постов")
        
        return len(filtered_posts)
        
    except Exception as e:
        print(f"❌ Ошибка фильтрации: {e}")
        return 0

def main():
    """Основная функция"""
    print("🧪 Тест анализа дубликатов")
    
    # Анализируем оба файла
    csv_files = [
        'data/results/search_20250726_045350.csv',
        'data/results/search_20250726_051718.csv'
    ]
    
    meta_files = [
        'data/results/search_20250726_045350.meta.json',
        'data/results/search_20250726_051718.meta.json'
    ]
    
    for csv_file, meta_file in zip(csv_files, meta_files):
        # Анализируем дубликаты
        dup_stats = analyze_duplicates(csv_file)
        
        # Загружаем ключевые слова
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            keywords = meta.get('keywords', [])
            expected_count = meta.get('count', 0)
        except Exception as e:
            print(f"❌ Ошибка загрузки {meta_file}: {e}")
            continue
        
        print(f"\n📋 Ожидаемый результат: {expected_count} постов")
        
        # Тестируем фильтрацию без удаления дубликатов
        actual_count = test_filter_without_dedup(csv_file, keywords)
        
        print(f"\n🎯 Сравнение:")
        print(f"   Ожидалось: {expected_count}")
        print(f"   Получено: {actual_count}")
        print(f"   Разница: {actual_count - expected_count}")
        
        if dup_stats:
            print(f"   Уникальных постов: {dup_stats['unique']}")
            print(f"   Дубликатов: {dup_stats['duplicate_keys']}")

if __name__ == "__main__":
    main() 