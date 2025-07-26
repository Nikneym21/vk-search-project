#!/usr/bin/env python3
"""
Тест оптимизированной системы фильтрации
Демонстрирует работу с легкими и полными форматами данных
"""

import sys
import os
import json
import gzip
from datetime import datetime

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_optimized_filter():
    """Тест оптимизированного плагина фильтрации"""
    try:
        from src.plugins.filter.optimized_filter_plugin import OptimizedFilterPlugin
        
        # Инициализируем плагин
        filter_plugin = OptimizedFilterPlugin()
        filter_plugin.initialize()
        
        print("✅ OptimizedFilterPlugin инициализирован успешно")
        
        # Создаем тестовые данные (имитация большого объема)
        test_posts = []
        for i in range(1000):
            post = {
                'id': i,
                'owner_id': -123456,
                'text': f'Тестовый пост номер {i} с ключевыми словами',
                'date': 1640995200 + i,
                'likes': {'count': 10 + i % 50},
                'comments': {'count': 5 + i % 20},
                'reposts': {'count': 2 + i % 10},
                'views': {'count': 100 + i % 200}
            }
            test_posts.append(post)
        
        # Добавляем дубликаты
        for i in range(100):
            duplicate_post = {
                'id': 1000 + i,
                'owner_id': -123456,
                'text': f'Тестовый пост номер {i} с ключевыми словами',  # Дубликат
                'date': 1640995200 + i,
                'likes': {'count': 10 + i % 50},
                'comments': {'count': 5 + i % 20},
                'reposts': {'count': 2 + i % 10},
                'views': {'count': 100 + i % 200}
            }
            test_posts.append(duplicate_post)
        
        print(f"📊 Создано {len(test_posts)} тестовых постов (включая дубликаты)")
        
        # Тест 1: Быстрая фильтрация уникальных постов
        print("\n🔍 Тест 1: Быстрая фильтрация уникальных постов")
        unique_posts = filter_plugin.filter_unique_posts_fast(test_posts)
        print(f"Результат: {len(unique_posts)} уникальных постов")
        print(f"📉 Удалено дубликатов: {len(test_posts) - len(unique_posts)}")
        
        # Тест 2: Фильтрация по ключевым словам
        print("\n🔍 Тест 2: Фильтрация по ключевым словам")
        keywords = ['ключевыми', 'словами', 'тестовый']
        filtered_posts = filter_plugin.filter_posts_by_keywords_fast(unique_posts, keywords, exact_match=False)
        print(f"Результат: {len(filtered_posts)} отфильтрованных постов")
        
        # Тест 3: Сохранение в легком формате
        print("\n💾 Тест 3: Сохранение в легком формате")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lightweight_file = filter_plugin.save_lightweight_results(filtered_posts, f"test_lightweight_{timestamp}")
        print(f"Сохранено в: {lightweight_file}")
        
        # Проверяем размер файла
        file_size = os.path.getsize(lightweight_file)
        print(f"Размер файла: {file_size / 1024:.2f} KB")
        
        # Тест 4: Экспорт в полный CSV
        print("\n📊 Тест 4: Экспорт в полный CSV")
        output_csv = f"data/results/test_full_{timestamp}.csv"
        csv_file = filter_plugin.export_to_full_csv(lightweight_file, output_csv)
        if csv_file:
            csv_size = os.path.getsize(csv_file)
            print(f"CSV файл: {csv_file}")
            print(f"Размер CSV: {csv_size / 1024:.2f} KB")
        
        # Тест 5: Статистика
        print("\n📈 Тест 5: Статистика")
        stats = filter_plugin.get_statistics(filtered_posts)
        print(f"Всего постов: {stats['total_posts']}")
        print(f"Всего лайков: {stats['total_likes']}")
        print(f"Всего комментариев: {stats['total_comments']}")
        print(f"Всего репостов: {stats['total_reposts']}")
        print(f"Всего просмотров: {stats['total_views']}")
        print(f"Общий SI: {stats['total_SI']}")
        
        # Тест 6: Поиск дубликатов
        print("\n🔍 Тест 6: Поиск дубликатов")
        duplicates = filter_plugin.find_duplicates(test_posts)
        print(f"Найдено групп дубликатов: {len(duplicates)}")
        
        # Показываем примеры дубликатов
        for i, dup_group in enumerate(duplicates[:3]):
            print(f"\n  Группа дубликатов {i+1} ({len(dup_group)} постов):")
            for dup in dup_group[:2]:  # Показываем первые 2
                text = dup.get('text', '')[:50]
                print(f"    - {text}...")
        
        filter_plugin.shutdown()
        print("\n✅ Тестирование оптимизированной системы завершено успешно")
        
        return {
            'lightweight_file': lightweight_file,
            'csv_file': csv_file,
            'stats': stats,
            'duplicates_count': len(duplicates)
        }
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_formats():
    """Сравнение размеров файлов разных форматов"""
    print("\n" + "=" * 60)
    print("📊 СРАВНЕНИЕ ФОРМАТОВ ФАЙЛОВ")
    print("=" * 60)
    
    results_dir = "data/results"
    if not os.path.exists(results_dir):
        print("❌ Папка data/results не найдена")
        return
    
    # Находим файлы для сравнения
    files = os.listdir(results_dir)
    csv_files = [f for f in files if f.endswith('.csv')]
    json_files = [f for f in files if f.endswith('.json.gz')]
    
    print(f"📁 Найдено файлов:")
    print(f"   CSV файлов: {len(csv_files)}")
    print(f"   JSON.GZ файлов: {len(json_files)}")
    
    # Показываем размеры последних файлов
    if csv_files:
        latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(results_dir, x)))
        csv_path = os.path.join(results_dir, latest_csv)
        csv_size = os.path.getsize(csv_path)
        print(f"\n📄 Последний CSV файл: {latest_csv}")
        print(f"   Размер: {csv_size / 1024:.2f} KB")
        
        # Показываем количество строк
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            print(f"   Строк: {len(df)}")
            print(f"   Колонок: {len(df.columns)}")
        except Exception as e:
            print(f"   Ошибка чтения CSV: {e}")
    
    if json_files:
        latest_json = max(json_files, key=lambda x: os.path.getctime(os.path.join(results_dir, x)))
        json_path = os.path.join(results_dir, latest_json)
        json_size = os.path.getsize(json_path)
        print(f"\n📄 Последний JSON.GZ файл: {latest_json}")
        print(f"   Размер: {json_size / 1024:.2f} KB")
        
        # Показываем количество записей
        try:
            with gzip.open(json_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   Записей: {len(data)}")
        except Exception as e:
            print(f"   Ошибка чтения JSON: {e}")

def main():
    """Главная функция"""
    print("🚀 ТЕСТ ОПТИМИЗИРОВАННОЙ СИСТЕМЫ ФИЛЬТРАЦИИ")
    print("=" * 60)
    
    # Тест оптимизированного плагина
    results = test_optimized_filter()
    
    if results:
        print(f"\n📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   Легкий файл: {results['lightweight_file']}")
        print(f"   CSV файл: {results['csv_file']}")
        print(f"   Статистика: {results['stats']['total_posts']} постов")
        print(f"   Групп дубликатов: {results['duplicates_count']}")
    
    # Сравнение форматов
    compare_formats()
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    main() 