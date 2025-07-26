#!/usr/bin/env python3
"""
Тест анализа текста постов
"""

import sys
import os
import json
import pandas as pd
import re

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
                'date': row.get('date', 0)
            }
            posts.append(post)
        
        print(f"   Конвертировано в {len(posts)} постов")
        return posts
        
    except Exception as e:
        print(f"❌ Ошибка загрузки {csv_file}: {e}")
        return []

def basic_text_clean(text):
    """Базовая очистка текста"""
    if not text:
        return ""
    # Удаляем эмодзи и лишние символы
    text = re.sub(r'[^\w\s]', ' ', text)
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def check_keyword_match(text, keyword, exact_match):
    """Проверяет соответствие текста ключевому слову"""
    if not text or not keyword:
        return False
    
    cleaned_text = basic_text_clean(text)
    keyword_lower = keyword.lower()
    
    if exact_match:
        # Точное совпадение (включая границы слов)
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        return bool(re.search(pattern, cleaned_text))
    else:
        # Частичное совпадение
        return keyword_lower in cleaned_text

def analyze_text_samples(csv_file, keywords, exact_match=True):
    """Анализирует образцы текста"""
    print(f"\n🔍 АНАЛИЗ ТЕКСТА: {csv_file}")
    print("="*60)
    
    posts = load_csv_as_posts(csv_file)
    if not posts:
        return
    
    print(f"\n📊 Статистика:")
    print(f"   Всего постов: {len(posts)}")
    print(f"   Ключевых слов: {len(keywords)}")
    print(f"   Exact match: {exact_match}")
    
    # Анализируем первые 5 постов
    print(f"\n📝 Образцы текста (первые 5 постов):")
    for i, post in enumerate(posts[:5]):
        text = post.get('text', '')
        owner_id = post.get('owner_id', 0)
        post_id = post.get('id', 0)
        
        print(f"\n   Пост {i+1} [ID: {owner_id}_{post_id}]:")
        print(f"   Оригинальный текст: {text[:200]}...")
        
        cleaned = basic_text_clean(text)
        print(f"   Очищенный текст: {cleaned[:200]}...")
        
        # Проверяем ключевые слова
        matches = []
        for keyword in keywords[:3]:  # Проверяем первые 3 ключа
            if check_keyword_match(text, keyword, exact_match):
                matches.append(keyword)
        
        if matches:
            print(f"   ✅ Найдены совпадения: {matches}")
        else:
            print(f"   ❌ Совпадений не найдено")
    
    # Подсчитываем общие результаты
    print(f"\n📊 Общие результаты:")
    total_matches = 0
    keyword_stats = {}
    
    for keyword in keywords:
        keyword_matches = 0
        for post in posts:
            if check_keyword_match(post.get('text', ''), keyword, exact_match):
                keyword_matches += 1
                total_matches += 1
        
        if keyword_matches > 0:
            keyword_stats[keyword] = keyword_matches
    
    print(f"   Всего совпадений: {total_matches}")
    print(f"   Ключевых слов с совпадениями: {len(keyword_stats)}")
    
    if keyword_stats:
        print(f"\n📋 Ключевые слова с совпадениями:")
        for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   '{keyword}': {count} постов")

def main():
    """Основная функция"""
    print("🧪 Тест анализа текста")
    
    # Тестируем второй файл (где есть результаты)
    csv_file = 'data/results/search_20250726_051718.csv'
    meta_file = 'data/results/search_20250726_051718.meta.json'
    
    # Загружаем ключевые слова
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        keywords = meta.get('keywords', [])
        exact_match = meta.get('exact_match', True)
    except Exception as e:
        print(f"❌ Ошибка загрузки {meta_file}: {e}")
        return
    
    print(f"📋 Ключевые слова из {meta_file}:")
    for i, keyword in enumerate(keywords, 1):
        print(f"   {i}. {keyword}")
    
    # Анализируем текст
    analyze_text_samples(csv_file, keywords, exact_match)

if __name__ == "__main__":
    main() 