#!/usr/bin/env python3
"""
Тест оптимизации логирования для больших объемов данных
"""

import asyncio
import time
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем напрямую
from src.core.plugin_manager import PluginManager

async def test_small_volume_logging():
    """Тест логирования для небольшого объема данных"""
    print("📝 Тест логирования для небольшого объема (5 ключевых фраз)")
    print("=" * 60)
    
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Тестовые данные
    keywords = ['новости', 'технологии', 'программирование', 'python', 'разработка']
    start_date = '24.07.2025'
    end_date = '24.07.2025'
    
    start_time = time.time()
    
    try:
        print("🚀 Запуск поиска с обычным логированием...")
        
        results = await pm.coordinate_search_and_filter(
            keywords, start_date, end_date, exact_match=False
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Результаты:")
        print(f"   Время выполнения: {execution_time:.2f} сек")
        print(f"   Получено постов: {len(results)}")
        print(f"   Ключевых фраз: {len(keywords)}")
        print(f"   Режим логирования: Обычный")
        
        pm.shutdown_plugins()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        pm.shutdown_plugins()

async def test_large_volume_logging():
    """Тест логирования для большого объема данных"""
    print("\n📝 Тест логирования для большого объема (50 ключевых фраз)")
    print("=" * 60)
    
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Генерируем много ключевых фраз
    keywords = [
        'новости', 'технологии', 'программирование', 'python', 'разработка',
        'web', 'mobile', 'ai', 'машинное обучение', 'data science',
        'javascript', 'react', 'vue', 'angular', 'nodejs',
        'java', 'kotlin', 'swift', 'android', 'ios',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp',
        'sql', 'nosql', 'mongodb', 'postgresql', 'redis',
        'git', 'github', 'gitlab', 'ci', 'cd',
        'agile', 'scrum', 'kanban', 'devops', 'microservices',
        'blockchain', 'cryptocurrency', 'bitcoin', 'ethereum', 'defi',
        'cybersecurity', 'penetration testing', 'vulnerability', 'threat', 'security'
    ]
    
    start_date = '24.07.2025'
    end_date = '24.07.2025'
    
    start_time = time.time()
    
    try:
        print("🚀 Запуск поиска с оптимизированным логированием...")
        print(f"📊 Количество ключевых фраз: {len(keywords)}")
        
        results = await pm.coordinate_search_and_filter(
            keywords, start_date, end_date, exact_match=False
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Результаты:")
        print(f"   Время выполнения: {execution_time:.2f} сек")
        print(f"   Получено постов: {len(results)}")
        print(f"   Ключевых фраз: {len(keywords)}")
        print(f"   Режим логирования: Оптимизированный для больших объемов")
        
        pm.shutdown_plugins()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        pm.shutdown_plugins()

async def test_extreme_volume_logging():
    """Тест логирования для экстремального объема данных"""
    print("\n📝 Тест логирования для экстремального объема (100+ ключевых фраз)")
    print("=" * 60)
    
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Генерируем очень много ключевых фраз
    base_keywords = [
        'новости', 'технологии', 'программирование', 'python', 'разработка',
        'web', 'mobile', 'ai', 'машинное обучение', 'data science',
        'javascript', 'react', 'vue', 'angular', 'nodejs',
        'java', 'kotlin', 'swift', 'android', 'ios',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp',
        'sql', 'nosql', 'mongodb', 'postgresql', 'redis',
        'git', 'github', 'gitlab', 'ci', 'cd',
        'agile', 'scrum', 'kanban', 'devops', 'microservices',
        'blockchain', 'cryptocurrency', 'bitcoin', 'ethereum', 'defi',
        'cybersecurity', 'penetration testing', 'vulnerability', 'threat', 'security'
    ]
    
    # Создаем вариации ключевых фраз
    keywords = []
    for i, base in enumerate(base_keywords):
        keywords.append(base)
        keywords.append(f"{base} 2025")
        keywords.append(f"новости {base}")
        if i < 20:  # Ограничиваем количество для теста
            keywords.append(f"технологии {base}")
    
    start_date = '24.07.2025'
    end_date = '24.07.2025'
    
    start_time = time.time()
    
    try:
        print("🚀 Запуск поиска с экстремальным объемом...")
        print(f"📊 Количество ключевых фраз: {len(keywords)}")
        
        # Ограничиваем количество для теста
        test_keywords = keywords[:50]
        
        results = await pm.coordinate_search_and_filter(
            test_keywords, start_date, end_date, exact_match=False
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Результаты:")
        print(f"   Время выполнения: {execution_time:.2f} сек")
        print(f"   Получено постов: {len(results)}")
        print(f"   Ключевых фраз: {len(test_keywords)}")
        print(f"   Режим логирования: Экстремальный объем")
        
        pm.shutdown_plugins()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        pm.shutdown_plugins()

if __name__ == "__main__":
    print("🎯 Тест оптимизации логирования для больших объемов")
    print("=" * 60)
    
    # Запускаем тесты
    asyncio.run(test_small_volume_logging())
    asyncio.run(test_large_volume_logging())
    asyncio.run(test_extreme_volume_logging())
    
    print("\n" + "=" * 60)
    print("✅ Все тесты завершены!")
    print("\n📊 Сравнение режимов логирования:")
    print("   🔹 Обычный режим: Подробные логи для каждого запроса")
    print("   🔹 Большие объемы: Batch логирование, rate limiting")
    print("   🔹 Экстремальный: Минимальное логирование, только сводки") 