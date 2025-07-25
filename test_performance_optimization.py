#!/usr/bin/env python3
"""
Тест производительности оптимизированного VKSearchPlugin
"""

import asyncio
import time
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем напрямую
from src.core.plugin_manager import PluginManager

async def test_performance():
    """Тест производительности оптимизированного парсинга"""
    print("🚀 Тест производительности оптимизированного VKSearchPlugin")
    print("=" * 60)
    
    # Инициализируем PluginManager
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Тестовые данные
    keywords = ['новости', 'технологии', 'программирование', 'python', 'разработка']
    start_date = '24.07.2025'
    end_date = '24.07.2025'
    
    print(f"📊 Параметры теста:")
    print(f"   Ключевые слова: {keywords}")
    print(f"   Период: {start_date} - {end_date}")
    print(f"   Количество запросов: {len(keywords)}")
    print()
    
    # Засекаем время
    start_time = time.time()
    
    try:
        # Выполняем поиск
        results = await pm.coordinate_search_and_filter(
            keywords, start_date, end_date, exact_match=False
        )
        
        # Вычисляем время выполнения
        execution_time = time.time() - start_time
        
        print(f"✅ Результаты теста:")
        print(f"   Время выполнения: {execution_time:.2f} секунд")
        print(f"   Получено постов: {len(results)}")
        print(f"   Скорость: {len(results) / execution_time:.1f} постов/сек")
        
        # Получаем статистику VKSearchPlugin
        vk_plugin = pm.get_plugin('vk_search')
        if vk_plugin:
            stats = vk_plugin.get_statistics()
            print(f"\n📈 Статистика VKSearchPlugin:")
            print(f"   Запросов к API: {stats['requests_made']}")
            print(f"   Rate limit hits: {stats['performance_metrics']['rate_limit_hits']}")
            print(f"   Среднее время ответа: {stats['performance_metrics']['average_response_time']:.3f} сек")
            print(f"   Размер кэша: {stats['performance_metrics']['cache_size']}")
            print(f"   Запросов в секунду: {stats['performance_metrics']['requests_per_second']:.1f}")
            print(f"   Использование токенов: {stats['performance_metrics']['token_usage']}")
        
        # Получаем статистику FilterPlugin
        filter_plugin = pm.get_plugin('filter')
        if filter_plugin:
            print(f"\n🔍 Статистика FilterPlugin:")
            print(f"   Обработано постов: {len(results)}")
        
        print(f"\n🎯 Оценка производительности:")
        if execution_time < 30:
            print("   ⚡ Отлично! Быстрая работа")
        elif execution_time < 60:
            print("   ✅ Хорошо! Приемлемая скорость")
        else:
            print("   ⚠️  Медленно! Требует оптимизации")
            
        if len(results) > 100:
            print("   📈 Высокая результативность")
        elif len(results) > 50:
            print("   ✅ Средняя результативность")
        else:
            print("   ⚠️  Низкая результативность")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        execution_time = time.time() - start_time
        print(f"   Время до ошибки: {execution_time:.2f} секунд")
    
    finally:
        # Завершаем работу
        pm.shutdown_plugins()

async def test_comparison():
    """Сравнение производительности до и после оптимизации"""
    print("\n" + "=" * 60)
    print("📊 Сравнение производительности")
    print("=" * 60)
    
    # Тестовые данные для сравнения
    test_cases = [
        {
            "name": "Мало запросов",
            "keywords": ["тест"],
            "expected_time": 10
        },
        {
            "name": "Среднее количество",
            "keywords": ["новости", "технологии", "программирование"],
            "expected_time": 20
        },
        {
            "name": "Много запросов",
            "keywords": ["новости", "технологии", "программирование", "python", "разработка", "web", "mobile"],
            "expected_time": 40
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}:")
        print(f"   Запросов: {len(test_case['keywords'])}")
        
        start_time = time.time()
        
        try:
            pm = PluginManager()
            pm.load_plugins()
            pm.initialize_plugins()
            
            results = await pm.coordinate_search_and_filter(
                test_case['keywords'], '24.07.2025', '24.07.2025', exact_match=False
            )
            
            execution_time = time.time() - start_time
            efficiency = len(results) / execution_time if execution_time > 0 else 0
            
            print(f"   ⏱️  Время: {execution_time:.2f} сек")
            print(f"   📊 Результатов: {len(results)}")
            print(f"   🚀 Эффективность: {efficiency:.1f} постов/сек")
            
            if execution_time < test_case['expected_time']:
                print(f"   ✅ Быстрее ожидаемого ({test_case['expected_time']} сек)")
            else:
                print(f"   ⚠️  Медленнее ожидаемого ({test_case['expected_time']} сек)")
                
            pm.shutdown_plugins()
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🎯 Тест производительности оптимизированного VKSearchPlugin")
    print("=" * 60)
    
    # Запускаем тесты
    asyncio.run(test_performance())
    asyncio.run(test_comparison())
    
    print("\n" + "=" * 60)
    print("✅ Тест завершен!") 