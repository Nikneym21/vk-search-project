#!/usr/bin/env python3
"""
Скрипт для прямого тестирования плагина фильтрации
Проверяет уникальность постов по тексту и ссылкам
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_filter_plugin():
    """Тестирование плагина фильтрации"""
    try:
        from src.plugins.filter.filter_plugin import FilterPlugin
        
        # Инициализируем плагин
        filter_plugin = FilterPlugin()
        filter_plugin.initialize()
        
        print("✅ FilterPlugin инициализирован успешно")
        
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
        
        # Тест 1: Фильтрация уникальных постов
        print("\n🔍 Тест 1: Фильтрация уникальных постов")
        unique_posts = filter_plugin.filter_unique_posts(test_posts)
        print(f"Результат: {len(unique_posts)} уникальных постов")
        
        for i, post in enumerate(unique_posts):
            print(f"  {i+1}. ID: {post['id']}, Owner: {post['owner_id']}, Text: {post['text'][:50]}...")
        
        # Тест 2: Комплексная фильтрация
        print("\n🔍 Тест 2: Комплексная фильтрация")
        keywords = ['тестовый', 'пост']
        filtered_posts = filter_plugin.filter_posts_comprehensive(
            posts=test_posts,
            keywords=keywords,
            exact_match=False,
            use_text_cleaning=True,
            remove_duplicates=True
        )
        print(f"Результат: {len(filtered_posts)} отфильтрованных постов")
        
        for i, post in enumerate(filtered_posts):
            print(f"  {i+1}. ID: {post['id']}, Owner: {post['owner_id']}, Text: {post['text'][:50]}...")
        
        # Тест 3: Анализ дубликатов
        print("\n🔍 Тест 3: Анализ дубликатов")
        duplicates = filter_plugin.find_duplicates(test_posts)
        print(f"Найдено дубликатов: {len(duplicates)}")
        
        for dup in duplicates:
            print(f"  Дубликат: {dup}")
        
        filter_plugin.shutdown()
        print("\n✅ Тестирование завершено успешно")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

def test_with_real_data():
    """Тестирование с реальными данными из последнего результата"""
    try:
        from src.plugins.filter.filter_plugin import FilterPlugin
        
        # Загружаем последний результат
        results_dir = "data/results"
        csv_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print("❌ Нет CSV файлов в data/results")
            return
        
        # Берем самый новый файл
        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(results_dir, x)))
        filepath = os.path.join(results_dir, latest_file)
        
        print(f"📁 Анализируем файл: {latest_file}")
        
        # Загружаем данные
        df = pd.read_csv(filepath)
        print(f"📊 Загружено {len(df)} записей")
        
        # Конвертируем в формат для фильтра
        posts = []
        for _, row in df.iterrows():
            post = {
                'id': hash(row.get('link', '')),
                'owner_id': 0,
                'text': row.get('text', ''),
                'date': 0,
                'likes': {'count': row.get('likes', 0)},
                'comments': {'count': row.get('comments', 0)},
                'reposts': {'count': row.get('reposts', 0)},
                'views': {'count': row.get('views', 0)}
            }
            posts.append(post)
        
        # Инициализируем плагин
        filter_plugin = FilterPlugin()
        filter_plugin.initialize()
        
        print(f"🔍 Анализируем {len(posts)} постов на уникальность")
        
        # Проверяем уникальность
        unique_posts = filter_plugin.filter_unique_posts(posts)
        print(f"✅ Уникальных постов: {len(unique_posts)}")
        print(f"📉 Дубликатов удалено: {len(posts) - len(unique_posts)}")
        
        # Анализируем дубликаты
        duplicates = filter_plugin.find_duplicates(posts)
        print(f"🔍 Найдено групп дубликатов: {len(duplicates)}")
        
        # Показываем примеры дубликатов
        for i, dup_group in enumerate(duplicates[:5]):  # Показываем первые 5 групп
            print(f"\n  Группа дубликатов {i+1}:")
            for dup in dup_group:
                text = dup.get('text', '')[:100]
                print(f"    - {text}...")
        
        filter_plugin.shutdown()
        
    except Exception as e:
        print(f"❌ Ошибка при анализе реальных данных: {e}")
        import traceback
        traceback.print_exc()

def analyze_links_uniqueness():
    """Анализ уникальности по ссылкам"""
    try:
        results_dir = "data/results"
        csv_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print("❌ Нет CSV файлов в data/results")
            return
        
        # Берем самый новый файл
        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(results_dir, x)))
        filepath = os.path.join(results_dir, latest_file)
        
        print(f"🔗 Анализируем уникальность ссылок в файле: {latest_file}")
        
        # Загружаем данные
        df = pd.read_csv(filepath)
        print(f"📊 Всего записей: {len(df)}")
        
        # Проверяем уникальность ссылок
        unique_links = df['link'].nunique()
        print(f"🔗 Уникальных ссылок: {unique_links}")
        print(f"📉 Дубликатов ссылок: {len(df) - unique_links}")
        
        # Проверяем уникальность текстов
        unique_texts = df['text'].nunique()
        print(f"📝 Уникальных текстов: {unique_texts}")
        print(f"📉 Дубликатов текстов: {len(df) - unique_texts}")
        
        # Показываем примеры дубликатов
        print("\n🔍 Примеры дубликатов ссылок:")
        link_counts = df['link'].value_counts()
        duplicates = link_counts[link_counts > 1]
        
        for link, count in duplicates.head(5).items():
            print(f"  Ссылка: {link}")
            print(f"  Количество: {count}")
            # Показываем тексты для этой ссылки
            texts = df[df['link'] == link]['text'].tolist()
            for i, text in enumerate(texts[:3]):  # Показываем первые 3 текста
                print(f"    {i+1}. {text[:100]}...")
            print()
        
        print("\n🔍 Примеры дубликатов текстов:")
        text_counts = df['text'].value_counts()
        text_duplicates = text_counts[text_counts > 1]
        
        for text, count in text_duplicates.head(3).items():
            print(f"  Текст: {text[:100]}...")
            print(f"  Количество: {count}")
            # Показываем ссылки для этого текста
            links = df[df['text'] == text]['link'].tolist()
            for i, link in enumerate(links[:3]):  # Показываем первые 3 ссылки
                print(f"    {i+1}. {link}")
            print()
        
    except Exception as e:
        print(f"❌ Ошибка при анализе ссылок: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция"""
    print("🚀 Запуск тестирования плагина фильтрации")
    print("=" * 50)
    
    # Тест 1: Базовое тестирование плагина
    test_filter_plugin()
    
    print("\n" + "=" * 50)
    
    # Тест 2: Анализ реальных данных
    test_with_real_data()
    
    print("\n" + "=" * 50)
    
    # Тест 3: Анализ уникальности ссылок
    analyze_links_uniqueness()

if __name__ == "__main__":
    main() 