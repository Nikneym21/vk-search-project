#!/usr/bin/env python3
"""
Тест централизованной обработки публикаций через PostProcessorPlugin
"""

import sys
import os
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.plugin_manager import PluginManager


def test_post_processor_integration():
    """Тест интеграции PostProcessorPlugin"""
    print("🧪 Тест интеграции PostProcessorPlugin")
    print("=" * 50)
    
    try:
        # Создаем PluginManager
        plugin_manager = PluginManager()
        
        # Загружаем плагины
        plugin_manager.load_plugins()
        
        # Инициализируем плагины
        plugin_manager.initialize_plugins()
        
        # Получаем PostProcessorPlugin
        post_processor = plugin_manager.get_plugin('post_processor')
        
        if not post_processor:
            print("❌ PostProcessorPlugin не найден")
            return False
        
        print("✅ PostProcessorPlugin загружен")
        
        # Проверяем подключение к другим плагинам
        filter_plugin = plugin_manager.get_plugin('filter')
        deduplication_plugin = plugin_manager.get_plugin('deduplication')
        database_plugin = plugin_manager.get_plugin('database')
        
        print(f"📊 Статус подключений:")
        print(f"   FilterPlugin: {'✅' if filter_plugin else '❌'}")
        print(f"   DeduplicationPlugin: {'✅' if deduplication_plugin else '❌'}")
        print(f"   DatabasePlugin: {'✅' if database_plugin else '❌'}")
        
        # Получаем статистику
        stats = post_processor.get_statistics()
        print(f"📈 Статистика PostProcessorPlugin: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


def test_post_processing():
    """Тест обработки публикаций"""
    print("\n🧪 Тест обработки публикаций")
    print("=" * 50)
    
    try:
        # Создаем PluginManager
        plugin_manager = PluginManager()
        plugin_manager.load_plugins()
        plugin_manager.initialize_plugins()
        
        # Получаем PostProcessorPlugin
        post_processor = plugin_manager.get_plugin('post_processor')
        
        if not post_processor:
            print("❌ PostProcessorPlugin не найден")
            return False
        
        # Создаем тестовые данные
        test_posts = [
            {
                "id": 1,
                "owner_id": 123,
                "text": "Python программирование новости",
                "link": "https://vk.com/wall123_1",
                "date": 1640995200
            },
            {
                "id": 2,
                "owner_id": 456,
                "text": "JavaScript разработка веб",
                "link": "https://vk.com/wall456_2",
                "date": 1640995200
            },
            {
                "id": 3,
                "owner_id": 123,
                "text": "Python программирование новости",  # Дубликат по тексту
                "link": "https://vk.com/wall123_3",  # Разная ссылка
                "date": 1640995200
            },
            {
                "id": 4,
                "owner_id": 789,
                "text": "Python программирование новости",
                "link": "https://vk.com/wall123_1",  # Дубликат по ссылке
                "date": 1640995200
            },
            {
                "id": 5,
                "owner_id": 999,
                "text": "Java разработка приложений",
                "link": "https://vk.com/wall999_5",
                "date": 1640995200
            }
        ]
        
        print(f"📝 Тестовые данные: {len(test_posts)} публикаций")
        
        # Тест 1: Только удаление дубликатов
        print("\n🔍 Тест 1: Только удаление дубликатов")
        result1 = post_processor.process_posts(
            posts=test_posts,
            keywords=None,
            remove_duplicates=True,
            processing_order=["deduplication"]
        )
        
        print(f"   Исходно: {result1['original_count']}")
        print(f"   Дубликатов удалено: {result1['duplicates_removed']}")
        print(f"   Результат: {result1['final_count']}")
        print(f"   Время обработки: {result1['processing_time']:.3f}с")
        
        # Тест 2: Только фильтрация
        print("\n🔍 Тест 2: Только фильтрация по ключевым словам")
        result2 = post_processor.process_posts(
            posts=test_posts,
            keywords=["Python", "программирование"],
            exact_match=False,
            remove_duplicates=False,
            processing_order=["filtering"]
        )
        
        print(f"   Исходно: {result2['original_count']}")
        print(f"   Отфильтровано: {result2['filtered_count']}")
        print(f"   Результат: {result2['final_count']}")
        print(f"   Время обработки: {result2['processing_time']:.3f}с")
        
        # Тест 3: Комплексная обработка
        print("\n🔍 Тест 3: Комплексная обработка (дубликаты + фильтрация)")
        result3 = post_processor.process_posts(
            posts=test_posts,
            keywords=["Python", "программирование"],
            exact_match=False,
            remove_duplicates=True,
            processing_order=["deduplication", "filtering"]
        )
        
        print(f"   Исходно: {result3['original_count']}")
        print(f"   Дубликатов удалено: {result3['duplicates_removed']}")
        print(f"   Отфильтровано: {result3['filtered_count']}")
        print(f"   Результат: {result3['final_count']}")
        print(f"   Время обработки: {result3['processing_time']:.3f}с")
        
        # Тест 4: Обратный порядок обработки
        print("\n🔍 Тест 4: Обратный порядок (фильтрация + дубликаты)")
        result4 = post_processor.process_posts(
            posts=test_posts,
            keywords=["Python", "программирование"],
            exact_match=False,
            remove_duplicates=True,
            processing_order=["filtering", "deduplication"]
        )
        
        print(f"   Исходно: {result4['original_count']}")
        print(f"   Отфильтровано: {result4['filtered_count']}")
        print(f"   Дубликатов удалено: {result4['duplicates_removed']}")
        print(f"   Результат: {result4['final_count']}")
        print(f"   Время обработки: {result4['processing_time']:.3f}с")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обработки: {e}")
        return False


def main():
    """Главная функция тестирования"""
    print("🚀 Тестирование PostProcessorPlugin")
    print("=" * 60)
    
    # Тест интеграции
    integration_success = test_post_processor_integration()
    
    # Тест обработки
    processing_success = test_post_processing()
    
    # Итоговый результат
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print(f"   Интеграция: {'✅ УСПЕХ' if integration_success else '❌ ОШИБКА'}")
    print(f"   Обработка: {'✅ УСПЕХ' if processing_success else '❌ ОШИБКА'}")
    
    if integration_success and processing_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("PostProcessorPlugin готов к использованию")
    else:
        print("\n⚠️ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ")


if __name__ == "__main__":
    main() 