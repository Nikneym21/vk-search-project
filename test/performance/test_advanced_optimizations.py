#!/usr/bin/env python3
"""
Тест продвинутых оптимизаций: параллельная фильтрация, интеллектуальное кэширование, мониторинг
"""

import asyncio
import time
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем напрямую
from src.core.plugin_manager import PluginManager

async def test_parallel_filtering():
    """Тест параллельной фильтрации"""
    print("🚀 Тест параллельной фильтрации")
    print("=" * 50)
    
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Тестовые данные
    keywords = ['новости', 'технологии', 'программирование']
    start_date = '24.07.2025'
    end_date = '24.07.2025'
    
    start_time = time.time()
    
    try:
        results = await pm.coordinate_search_and_filter(
            keywords, start_date, end_date, exact_match=False
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Параллельная фильтрация завершена:")
        print(f"   Время: {execution_time:.2f} сек")
        print(f"   Результатов: {len(results)}")
        print(f"   Скорость: {len(results) / execution_time:.1f} постов/сек")
        
        # Проверяем FilterPlugin
        filter_plugin = pm.get_plugin('filter')
        if filter_plugin:
            print(f"   FilterPlugin загружен: ✅")
        
        pm.shutdown_plugins()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        pm.shutdown_plugins()

async def test_intelligent_caching():
    """Тест интеллектуального кэширования"""
    print("\n🧠 Тест интеллектуального кэширования")
    print("=" * 50)
    
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Тестовые данные
    keywords = ['python', 'разработка']
    start_date = '24.07.2025'
    end_date = '24.07.2025'
    
    try:
        # Первый запрос
        print("📊 Первый запрос (должен быть cache miss)...")
        start_time = time.time()
        results1 = await pm.coordinate_search_and_filter(
            keywords, start_date, end_date, exact_match=False
        )
        time1 = time.time() - start_time
        
        # Второй запрос (должен быть cache hit)
        print("📊 Второй запрос (должен быть cache hit)...")
        start_time = time.time()
        results2 = await pm.coordinate_search_and_filter(
            keywords, start_date, end_date, exact_match=False
        )
        time2 = time.time() - start_time
        
        # Проверяем VKSearchPlugin статистику
        vk_plugin = pm.get_plugin('vk_search')
        if vk_plugin:
            stats = vk_plugin.get_statistics()
            intelligent_cache = stats.get("intelligent_caching", {})
            
            print(f"✅ Интеллектуальное кэширование:")
            print(f"   Cache hits: {intelligent_cache.get('cache_hits', 0)}")
            print(f"   Cache misses: {intelligent_cache.get('cache_misses', 0)}")
            print(f"   Cache hit rate: {intelligent_cache.get('cache_hit_rate', 0):.1%}")
            print(f"   Время первого запроса: {time1:.2f} сек")
            print(f"   Время второго запроса: {time2:.2f} сек")
            print(f"   Ускорение: {time1 / max(time2, 0.1):.1f}x")
            
            # Топ популярных запросов
            top_queries = intelligent_cache.get('top_popular_queries', [])
            if top_queries:
                print(f"   Топ запросов: {top_queries[:3]}")
        
        pm.shutdown_plugins()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        pm.shutdown_plugins()

async def test_monitoring():
    """Тест мониторинга в реальном времени"""
    print("\n📊 Тест мониторинга в реальном времени")
    print("=" * 50)
    
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    try:
        # Получаем MonitoringPlugin
        monitoring_plugin = pm.get_plugin('monitoring')
        if monitoring_plugin:
            print("✅ MonitoringPlugin загружен")
            
            # Ждем немного для сбора метрик
            await asyncio.sleep(10)
            
            # Получаем статистику
            stats = monitoring_plugin.get_statistics()
            print(f"📈 Статистика мониторинга:")
            print(f"   Включен: {stats.get('enabled', False)}")
            print(f"   Алерты: {stats.get('alerts_count', 0)}")
            print(f"   История метрик: {stats.get('history_size', 0)} записей")
            print(f"   Дашборд: {'✅' if stats.get('dashboard_enabled', False) else '❌'}")
            print(f"   Алерты: {'✅' if stats.get('alerts_enabled', False) else '❌'}")
            
            # Получаем данные дашборда
            dashboard = monitoring_plugin.get_dashboard_data()
            metrics = dashboard.get('metrics', {})
            
            print(f"📊 Текущие метрики:")
            print(f"   Время ответа: {metrics.get('response_times', 0):.3f} сек")
            print(f"   Rate limit hits: {metrics.get('rate_limit_hits', 0)}")
            print(f"   Cache hit rate: {metrics.get('cache_hit_rate', 0):.1%}")
            print(f"   Использование памяти: {metrics.get('memory_usage', 0):.1%}")
            print(f"   Активные соединения: {metrics.get('active_connections', 0)}")
            
            # Проверяем статус
            status = dashboard.get('status', 'unknown')
            print(f"🎯 Статус системы: {status}")
            
            # Проверяем алерты
            alerts = dashboard.get('alerts', [])
            if alerts:
                print(f"⚠️ Последние алерты:")
                for alert in alerts[-3:]:
                    print(f"   {alert.get('message', 'Unknown')}")
            else:
                print("✅ Алертов нет")
        
        pm.shutdown_plugins()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        pm.shutdown_plugins()

async def test_integrated_optimizations():
    """Интеграционный тест всех оптимизаций"""
    print("\n🎯 Интеграционный тест всех оптимизаций")
    print("=" * 50)
    
    pm = PluginManager()
    pm.load_plugins()
    pm.initialize_plugins()
    
    # Тестовые данные
    keywords = ['новости', 'технологии', 'программирование', 'python', 'разработка']
    start_date = '24.07.2025'
    end_date = '24.07.2025'
    
    start_time = time.time()
    
    try:
        print("🚀 Запуск интегрированного теста...")
        
        # Выполняем поиск с фильтрацией
        results = await pm.coordinate_search_and_filter(
            keywords, start_date, end_date, exact_match=False
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ Интегрированный тест завершен:")
        print(f"   Общее время: {execution_time:.2f} сек")
        print(f"   Результатов: {len(results)}")
        print(f"   Скорость: {len(results) / execution_time:.1f} постов/сек")
        
        # Проверяем все плагины
        plugins_to_check = ['vk_search', 'filter', 'monitoring']
        for plugin_name in plugins_to_check:
            plugin = pm.get_plugin(plugin_name)
            if plugin:
                print(f"   {plugin_name}: ✅")
            else:
                print(f"   {plugin_name}: ❌")
        
        # Получаем финальную статистику
        vk_plugin = pm.get_plugin('vk_search')
        if vk_plugin:
            stats = vk_plugin.get_statistics()
            intelligent_cache = stats.get("intelligent_caching", {})
            
            print(f"\n📊 Финальная статистика:")
            print(f"   Cache hit rate: {intelligent_cache.get('cache_hit_rate', 0):.1%}")
            print(f"   Популярные запросы: {len(intelligent_cache.get('top_popular_queries', []))}")
            print(f"   Паттерны запросов: {len(intelligent_cache.get('top_query_patterns', []))}")
        
        pm.shutdown_plugins()
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        pm.shutdown_plugins()

if __name__ == "__main__":
    print("🎯 Тест продвинутых оптимизаций")
    print("=" * 60)
    
    # Запускаем все тесты
    asyncio.run(test_parallel_filtering())
    asyncio.run(test_intelligent_caching())
    asyncio.run(test_monitoring())
    asyncio.run(test_integrated_optimizations())
    
    print("\n" + "=" * 60)
    print("✅ Все тесты завершены!") 