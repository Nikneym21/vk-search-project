#!/usr/bin/env python3
"""
Тест системы базы данных
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.plugins.database.database_plugin import DatabasePlugin

def test_database_system():
    """Тест системы базы данных"""
    print("🧪 Тест системы базы данных")
    
    # Инициализируем плагин
    db_plugin = DatabasePlugin()
    db_plugin.initialize()
    
    print("✅ DatabasePlugin инициализирован успешно")
    
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
    for i in range(10):  # Уменьшаем количество для теста
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
    posts = db_plugin.get_task_posts(task1_id, limit=5)
    print(f"Получено {len(posts)} постов (первые 5)")
    
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
    
    # Тест 6: Обновление статуса
    print("\n🔄 Тест 6: Обновление статуса задачи")
    db_plugin.update_task_status(task1_id, "completed")
    print(f"Статус задачи {task1_id} обновлен на 'completed'")
    
    db_plugin.shutdown()
    print("\n✅ Тестирование системы базы данных завершено успешно")
    
    return {
        'task1_id': task1_id,
        'task2_id': task2_id,
        'saved_posts': saved_count,
        'total_tasks': len(tasks)
    }

def main():
    """Основная функция"""
    test_database_system()

if __name__ == "__main__":
    main() 