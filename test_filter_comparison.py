#!/usr/bin/env python3
"""
Тест сравнения фильтрации для каждого файла отдельно
"""

import sys
import os
import json
import pandas as pd
import asyncio
import re

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class SimpleFilterPlugin:
    """Упрощенная версия FilterPlugin для тестирования"""
    
    def __init__(self):
        self.name = "SimpleFilterPlugin"
    
    def _extract_post_text(self, post):
        """Извлекает текст из поста"""
        text = post.get('text', '')
        if not text:
            text = post.get('message', '')
        if not text:
            text = post.get('content', '')
        return text
    
    def _basic_text_clean(self, text):
        """Базовая очистка текста"""
        if not text:
            return ""
        # Удаляем эмодзи и лишние символы
        text = re.sub(r'[^\w\s]', ' ', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower()
    
    def _check_keyword_match(self, text, keyword, exact_match):
        """Проверяет соответствие текста ключевому слову"""
        if not text or not keyword:
            return False
        
        cleaned_text = self._basic_text_clean(text)
        keyword_lower = keyword.lower()
        
        if exact_match:
            # Точное совпадение (включая границы слов)
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            return bool(re.search(pattern, cleaned_text))
        else:
            # Частичное совпадение
            return keyword_lower in cleaned_text
    
    async def filter_posts_comprehensive_parallel(self, posts, keywords, exact_match=True):
        """Параллельная фильтрация постов"""
        if not posts:
            return []
        
        print(f"🚀 Параллельная фильтрация {len(posts)} постов по {len(keywords)} ключам")
        
        # Создаем задачи для параллельной обработки
        tasks = []
        chunk_size = max(1, len(posts) // 10)
        
        for i in range(0, len(posts), chunk_size):
            chunk = posts[i:i + chunk_size]
            task = self._process_chunk_parallel(chunk, keywords, exact_match)
            tasks.append(task)
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks)
        
        # Объединяем результаты
        filtered_posts = []
        for result in results:
            filtered_posts.extend(result)
        
        # Удаляем дубликаты
        unique_posts = self.filter_unique_posts(filtered_posts)
        
        print(f"✅ Параллельная фильтрация завершена: {len(posts)} -> {len(unique_posts)}")
        return unique_posts
    
    async def _process_chunk_parallel(self, chunk, keywords, exact_match):
        """Параллельная обработка чанка постов"""
        filtered_chunk = []
        
        # Создаем задачи для каждого поста в чанке
        post_tasks = []
        for post in chunk:
            task = self._process_single_post_parallel(post, keywords, exact_match)
            post_tasks.append(task)
        
        # Выполняем обработку постов параллельно
        results = await asyncio.gather(*post_tasks, return_exceptions=True)
        
        # Собираем результаты
        for result in results:
            if isinstance(result, dict) and result:
                filtered_chunk.append(result)
            elif isinstance(result, Exception):
                print(f"Ошибка обработки поста: {result}")
        
        return filtered_chunk
    
    async def _process_single_post_parallel(self, post, keywords, exact_match):
        """Параллельная обработка одного поста"""
        try:
            # Получаем текст поста
            text = self._extract_post_text(post)
            if not text:
                return None
            
            # Проверяем соответствие ключевым словам
            for keyword in keywords:
                if self._check_keyword_match(text, keyword, exact_match):
                    return post
            
            return None
            
        except Exception as e:
            print(f"Ошибка обработки поста: {e}")
            return None
    
    def filter_unique_posts(self, posts):
        """Фильтрация уникальных постов по (owner_id, post_id)"""
        if not posts:
            return []
        
        seen = set()
        unique = []
        
        for post in posts:
            owner_id = post.get('owner_id')
            post_id = post.get('id') or post.get('post_id')
            
            if owner_id is not None and post_id is not None:
                key = (owner_id, post_id)
                if key not in seen:
                    seen.add(key)
                    unique.append(post)
        
        print(f"Фильтрация уникальных постов: {len(posts)} -> {len(unique)}")
        return unique

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

async def test_single_file(meta_file, filter_plugin):
    """Тест фильтрации для одного файла"""
    print(f"\n{'='*60}")
    print(f"📋 ТЕСТ ФАЙЛА: {meta_file}")
    print(f"{'='*60}")
    
    # Загружаем метаданные
    meta = load_meta_data(meta_file)
    if not meta:
        print("❌ Не удалось загрузить метаданные")
        return
    
    keywords = meta.get('keywords', [])
    csv_file = meta.get('filepath', '')
    expected_count = meta.get('count', 0)
    exact_match = meta.get('exact_match', False)
    
    print(f"📊 Метаданные:")
    print(f"   Ожидаемый результат: {expected_count} постов")
    print(f"   Ключевых слов: {len(keywords)}")
    print(f"   Exact match: {exact_match}")
    print(f"   CSV файл: {csv_file}")
    
    # Загружаем посты из CSV
    if not csv_file or not os.path.exists(csv_file):
        print("❌ CSV файл не найден")
        return
    
    posts = load_csv_as_posts(csv_file)
    if not posts:
        print("❌ Не удалось загрузить посты")
        return
    
    print(f"\n🔍 Ключевые слова:")
    for i, keyword in enumerate(keywords[:5], 1):
        print(f"   {i}. {keyword}")
    if len(keywords) > 5:
        print(f"   ... и еще {len(keywords) - 5} ключевых слов")
    
    # Тестируем фильтрацию
    print(f"\n🔍 Тест фильтрации:")
    try:
        # Фильтруем с настройками из meta.json
        print(f"   Запуск фильтрации с exact_match={exact_match}...")
        filtered_posts = await filter_plugin.filter_posts_comprehensive_parallel(
            posts, keywords, exact_match=exact_match
        )
        
        actual_count = len(filtered_posts)
        difference = actual_count - expected_count
        
        print(f"\n🎯 РЕЗУЛЬТАТ:")
        print(f"   Ожидалось: {expected_count} постов")
        print(f"   Получено: {actual_count} постов")
        print(f"   Разница: {difference}")
        
        if abs(difference) <= 5:
            print(f"   ✅ Результат близок к ожидаемому!")
        elif difference > 0:
            print(f"   ⚠️ Получено больше постов чем ожидалось")
        else:
            print(f"   ⚠️ Получено меньше постов чем ожидалось")
        
        # Показываем примеры отфильтрованных постов
        if filtered_posts:
            print(f"\n📝 Примеры отфильтрованных постов:")
            for i, post in enumerate(filtered_posts[:3]):
                text = post.get('text', '')[:100]
                owner_id = post.get('owner_id', 0)
                post_id = post.get('id', 0)
                print(f"   {i+1}. [ID: {owner_id}_{post_id}] {text}...")
        
        # Анализируем результаты по ключевым словам
        print(f"\n📊 Анализ по ключевым словам:")
        for keyword in keywords[:3]:  # Показываем первые 3
            keyword_posts = []
            for post in posts:
                text = filter_plugin._extract_post_text(post)
                if filter_plugin._check_keyword_match(text, keyword, exact_match=exact_match):
                    keyword_posts.append(post)
            print(f"   '{keyword}': {len(keyword_posts)} постов")
        
        return {
            'file': meta_file,
            'expected': expected_count,
            'actual': actual_count,
            'difference': difference,
            'keywords_count': len(keywords),
            'posts_count': len(posts)
        }
            
    except Exception as e:
        print(f"❌ Ошибка фильтрации: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_filter_comparison():
    """Тест сравнения фильтрации для каждого файла"""
    print("🧪 Тест сравнения фильтрации по файлам")
    
    # Создаем упрощенный плагин
    filter_plugin = SimpleFilterPlugin()
    
    # Список файлов для тестирования
    meta_files = [
        'data/results/search_20250726_045350.meta.json',
        'data/results/search_20250726_051718.meta.json'
    ]
    
    results = []
    
    # Тестируем каждый файл отдельно
    for meta_file in meta_files:
        result = await test_single_file(meta_file, filter_plugin)
        if result:
            results.append(result)
    
    # Сводка результатов
    print(f"\n{'='*60}")
    print(f"📊 СВОДКА РЕЗУЛЬТАТОВ")
    print(f"{'='*60}")
    
    total_expected = 0
    total_actual = 0
    
    for result in results:
        print(f"📁 {result['file']}:")
        print(f"   Ожидалось: {result['expected']} постов")
        print(f"   Получено: {result['actual']} постов")
        print(f"   Разница: {result['difference']}")
        print(f"   Ключевых слов: {result['keywords_count']}")
        print(f"   Исходных постов: {result['posts_count']}")
        print()
        
        total_expected += result['expected']
        total_actual += result['actual']
    
    total_difference = total_actual - total_expected
    print(f"🎯 ИТОГО:")
    print(f"   Ожидалось: {total_expected} постов")
    print(f"   Получено: {total_actual} постов")
    print(f"   Общая разница: {total_difference}")
    
    if abs(total_difference) <= 10:
        print(f"   ✅ Общий результат близок к ожидаемому!")
    else:
        print(f"   ⚠️ Общий результат отличается от ожидаемого")
    
    print(f"\n✅ Тест завершен")

if __name__ == "__main__":
    asyncio.run(test_filter_comparison()) 