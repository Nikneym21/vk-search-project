#!/usr/bin/env python3
"""
Тест системы базы данных для результатов парсинга
"""

import sys
import os
from datetime import datetime

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database_system():
    """Тест системы базы данных"""
    try:
        from src.plugins.database.database_manager_plugin import DatabaseManagerPlugin
        
        # Инициализируем плагин
        db_plugin = DatabaseManagerPlugin()
        if not db_plugin.initialize():
            print("❌ Ошибка инициализации плагина базы данных")
            return None
        
        print("✅ Плагин базы данных инициализирован успешно")
        
        # Тест 1: Создание задач
        print("\n🔧 Тест 1: Создание задач")
        
        task1_id = db_plugin.create_task(
            task_name="Тестовая задача 1",
            keywords=["тестовый", "пост", "ключевые слова"],
            start_date="25.07.2025",
            end_date="25.07.2025",
            exact_match=True,
            minus_words=["спам", "реклама"]
        )
        
        task2_id = db_plugin.create_task(
            task_name="Тестовая задача 2",
            keywords=["второй", "тест"],
            start_date="26.07.2025",
            end_date="26.07.2025",
            exact_match=False
        )
        
        print(f"Созданы задачи: {task1_id}, {task2_id}")
        
        # Тест 2: Создание тестовых постов
        print("\n📝 Тест 2: Создание тестовых постов")
        
        test_posts = []
        for i in range(100):
            post = {
                'id': i,
                'owner_id': -123456,
                'text': f'Тестовый пост номер {i} с ключевыми словами тестовый пост',
                'date': 1640995200 + i * 3600,
                'likes': {'count': 10 + i % 50},
                'comments': {'count': 5 + i % 20},
                'reposts': {'count': 2 + i % 10},
                'views': {'count': 100 + i % 200},
                'keywords_matched': ['тестовый', 'пост']
            }
            test_posts.append(post)
        
        # Добавляем дубликаты
        for i in range(10):
            duplicate_post = {
                'id': 100 + i,
                'owner_id': -123456,
                'text': f'Тестовый пост номер {i} с ключевыми словами тестовый пост',  # Дубликат
                'date': 1640995200 + i * 3600,
                'likes': {'count': 10 + i % 50},
                'comments': {'count': 5 + i % 20},
                'reposts': {'count': 2 + i % 10},
                'views': {'count': 100 + i % 200},
                'keywords_matched': ['тестовый', 'пост']
            }
            test_posts.append(duplicate_post)
        
        # Сохраняем посты в БД
        saved_count = db_plugin.save_posts(task1_id, test_posts)
        print(f"Сохранено {saved_count} постов для задачи {task1_id}")
        
        # Тест 3: Получение задач
        print("\n📋 Тест 3: Получение списка задач")
        tasks = db_plugin.get_tasks()
        print(f"Найдено задач: {len(tasks)}")
        
        for task in tasks:
            print(f"  Задача {task['id']}: {task['task_name']} (статус: {task['status']})")
            print(f"    Постов: {task['total_posts']}, Лайков: {task['total_likes']}, SI: {task['total_SI']}")
        
        # Тест 4: Получение постов
        print("\n📄 Тест 4: Получение постов задачи")
        posts = db_plugin.get_task_posts(task1_id, limit=10)
        print(f"Получено {len(posts)} постов (первые 10)")
        
        for i, post in enumerate(posts[:3]):
            print(f"  Пост {i+1}: {post['text'][:50]}...")
            print(f"    Лайки: {post['likes']}, Комментарии: {post['comments']}")
        
        # Тест 5: Статистика
        print("\n📊 Тест 5: Статистика задачи")
        stats = db_plugin.get_task_statistics(task1_id)
        if stats:
            print(f"Задача: {stats['task_name']}")
            print(f"Статус: {stats['status']}")
            print(f"Постов: {stats['total_posts']}")
            print(f"Лайков: {stats['total_likes']}")
            print(f"Комментариев: {stats['total_comments']}")
            print(f"Репостов: {stats['total_reposts']}")
            print(f"Просмотров: {stats['total_views']}")
            print(f"Общий SI: {stats['total_SI']}")
        
        # Тест 6: Поиск дубликатов
        print("\n🔍 Тест 6: Поиск дубликатов")
        duplicates = db_plugin.find_duplicates(task1_id)
        print(f"Найдено групп дубликатов: {len(duplicates)}")
        
        for i, dup_group in enumerate(duplicates[:3]):
            print(f"  Группа {i+1}: {len(dup_group)} дубликатов")
            for j, post in enumerate(dup_group[:2]):
                print(f"    {j+1}. {post['text'][:50]}...")
        
        # Тест 7: Экспорт в CSV
        print("\n💾 Тест 7: Экспорт в CSV")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"data/results/test_export_{timestamp}.csv"
        
        if db_plugin.export_task_to_csv(task1_id, csv_path):
            print(f"✅ Экспорт успешен: {csv_path}")
            
            # Проверяем размер файла
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                print(f"Размер файла: {file_size / 1024:.2f} KB")
        else:
            print("❌ Ошибка экспорта")
        
        # Тест 8: Обновление статуса
        print("\n🔄 Тест 8: Обновление статуса задачи")
        db_plugin.update_task_status(task1_id, "completed")
        print(f"Статус задачи {task1_id} обновлен на 'completed'")
        
        db_plugin.shutdown()
        print("\n✅ Тестирование системы базы данных завершено успешно")
        
        return {
            'task1_id': task1_id,
            'task2_id': task2_id,
            'saved_posts': saved_count,
            'total_tasks': len(tasks),
            'duplicates_count': len(duplicates),
            'csv_path': csv_path if os.path.exists(csv_path) else None
        }
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_database_info():
    """Показ информации о базе данных"""
    print("\n" + "=" * 60)
    print("📊 ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    db_path = "data/parser_results.db"
    
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        print(f"📁 База данных: {db_path}")
        print(f"📏 Размер: {file_size / 1024:.2f} KB")
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Информация о таблицах
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📋 Таблиц: {len(tables)}")
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} записей")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка чтения БД: {e}")
    else:
        print("❌ База данных не найдена")

def main():
    """Главная функция"""
    print("🚀 ТЕСТ СИСТЕМЫ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    # Тест системы
    results = test_database_system()
    
    if results:
        print(f"\n📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   Задача 1: {results['task1_id']}")
        print(f"   Задача 2: {results['task2_id']}")
        print(f"   Сохранено постов: {results['saved_posts']}")
        print(f"   Всего задач: {results['total_tasks']}")
        print(f"   Групп дубликатов: {results['duplicates_count']}")
        if results['csv_path']:
            print(f"   CSV файл: {results['csv_path']}")
    
    # Информация о БД
    show_database_info()
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    main() 