#!/usr/bin/env python3
"""
Тест интеграции плагинов через PluginManager
"""

import sys
import os
from datetime import datetime

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_plugin_manager_integration():
    """Тест интеграции плагинов через PluginManager"""
    try:
        from src.core.plugin_manager import PluginManager
        
        print("🚀 ТЕСТ ИНТЕГРАЦИИ ПЛАГИНОВ")
        print("=" * 60)
        
        # Создаем PluginManager
        plugin_manager = PluginManager()
        
        # Загружаем плагины
        print("📦 Загрузка плагинов...")
        plugin_manager.load_plugins()
        
        # Инициализируем плагины
        print("🔧 Инициализация плагинов...")
        plugin_manager.initialize_plugins()
        
        # Проверяем статус плагинов
        print("\n📊 Статус плагинов:")
        plugin_status = plugin_manager.get_plugin_status()
        for plugin_name, status in plugin_status.items():
            print(f"   {plugin_name}: {status}")
        
        # Проверяем зависимости
        print("\n🔗 Проверка зависимостей:")
        dependencies = plugin_manager.validate_plugin_dependencies()
        for plugin_name, deps in dependencies.items():
            for dep in deps:
                print(f"   {plugin_name}: {dep}")
        
        # Получаем основные плагины
        database_plugin = plugin_manager.get_plugin('database')
        filter_plugin = plugin_manager.get_plugin('filter')
        vk_search_plugin = plugin_manager.get_plugin('vk_search')
        token_manager = plugin_manager.get_plugin('token_manager')
        
        print(f"\n✅ Получены плагины:")
        print(f"   Database: {'✅' if database_plugin else '❌'}")
        print(f"   Filter: {'✅' if filter_plugin else '❌'}")
        print(f"   VKSearch: {'✅' if vk_search_plugin else '❌'}")
        print(f"   TokenManager: {'✅' if token_manager else '❌'}")
        
        # Тест работы с базой данных
        if database_plugin:
            print("\n🗄️ Тест базы данных:")
            
            # Создаем тестовую задачу
            task_id = database_plugin.create_task(
                task_name="Тест интеграции плагинов",
                keywords=["тест", "интеграция"],
                start_date="26.07.2025",
                end_date="26.07.2025"
            )
            print(f"   Создана задача: {task_id}")
            
            # Создаем тестовые посты
            test_posts = []
            for i in range(5):
                post = {
                    'id': i,
                    'owner_id': -123456,
                    'text': f'Тестовый пост {i} для проверки интеграции плагинов',
                    'date': 1640995200 + i * 3600,
                    'likes': {'count': 10 + i},
                    'comments': {'count': 5 + i},
                    'reposts': {'count': 2 + i},
                    'views': {'count': 100 + i * 10},
                    'keywords_matched': ['тест', 'интеграция']
                }
                test_posts.append(post)
            
            # Сохраняем посты
            saved_count = database_plugin.save_posts(task_id, test_posts)
            print(f"   Сохранено постов: {saved_count}")
            
            # Получаем статистику
            stats = database_plugin.get_task_statistics(task_id)
            print(f"   Статистика: {stats['total_posts']} постов, {stats['total_likes']} лайков")
            
            # Тест фильтрации
            if filter_plugin:
                print("\n🔍 Тест фильтрации:")
                
                # Получаем посты из БД
                posts = database_plugin.get_task_posts(task_id)
                print(f"   Получено постов из БД: {len(posts)}")
                
                # Фильтруем по ключевым словам
                if hasattr(filter_plugin, 'filter_posts_by_keywords_fast'):
                    filtered_posts = filter_plugin.filter_posts_by_keywords_fast(
                        posts, ["тест"], exact_match=False
                    )
                    print(f"   Отфильтровано постов: {len(filtered_posts)}")
                else:
                    print("   ⚠️ Метод фильтрации не найден")
            
            # Тест экспорта
            print("\n💾 Тест экспорта:")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"data/results/test_integration_{timestamp}.csv"
            
            if database_plugin.export_task_to_csv(task_id, csv_path):
                print(f"   ✅ Экспорт успешен: {csv_path}")
            else:
                print("   ❌ Ошибка экспорта")
        
        # Тест координации поиска
        if vk_search_plugin and token_manager:
            print("\n🔎 Тест координации поиска:")
            
            # Проверяем доступность токенов
            tokens = token_manager.list_vk_tokens()
            print(f"   Доступно токенов: {len(tokens)}")
            
            if tokens:
                print("   ✅ Токены доступны для поиска")
            else:
                print("   ⚠️ Токены недоступны")
        
        # Завершаем работу
        print("\n🔄 Завершение работы плагинов...")
        plugin_manager.shutdown_plugins()
        
        print("\n✅ Тест интеграции плагинов завершен успешно")
        
        return {
            'database_plugin': database_plugin is not None,
            'filter_plugin': filter_plugin is not None,
            'vk_search_plugin': vk_search_plugin is not None,
            'token_manager': token_manager is not None,
            'total_plugins': len(plugin_status),
            'task_id': task_id if database_plugin else None
        }
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_gui_integration():
    """Тест интеграции с GUI"""
    try:
        print("\n🖥️ ТЕСТ ИНТЕГРАЦИИ С GUI")
        print("=" * 60)
        
        # Импортируем GUI компоненты
        from src.gui.main_interface import MainInterface
        import tkinter as tk
        
        # Создаем тестовое окно
        root = tk.Tk()
        root.withdraw()  # Скрываем окно
        
        # Создаем главный интерфейс
        app = MainInterface(root)
        
        # Проверяем доступность плагинов
        print("📊 Проверка плагинов в GUI:")
        print(f"   Database: {'✅' if app.database_plugin else '❌'}")
        print(f"   Filter: {'✅' if app.filter_plugin else '❌'}")
        print(f"   VKSearch: {'✅' if app.vk_search_plugin else '❌'}")
        print(f"   TokenManager: {'✅' if app.token_manager else '❌'}")
        
        # Проверяем интерфейсы
        print("\n🖼️ Проверка интерфейсов:")
        print(f"   VK Interface: {'✅' if hasattr(app, 'vk_interface') else '❌'}")
        print(f"   Link Interface: {'✅' if hasattr(app, 'link_interface') else '❌'}")
        print(f"   DB Interface: {'✅' if hasattr(app, 'db_interface') else '❌'}")
        
        # Закрываем окно
        root.destroy()
        
        print("✅ Тест GUI интеграции завершен успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании GUI: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция"""
    print("🚀 ТЕСТ ИНТЕГРАЦИИ ПЛАГИНОВ ЧЕРЕЗ PLUGINMANAGER")
    print("=" * 80)
    
    # Тест PluginManager
    results = test_plugin_manager_integration()
    
    if results:
        print(f"\n📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   Database Plugin: {'✅' if results['database_plugin'] else '❌'}")
        print(f"   Filter Plugin: {'✅' if results['filter_plugin'] else '❌'}")
        print(f"   VKSearch Plugin: {'✅' if results['vk_search_plugin'] else '❌'}")
        print(f"   TokenManager Plugin: {'✅' if results['token_manager'] else '❌'}")
        print(f"   Всего плагинов: {results['total_plugins']}")
        if results['task_id']:
            print(f"   Тестовая задача: {results['task_id']}")
    
    # Тест GUI интеграции
    gui_success = test_gui_integration()
    
    print("\n" + "=" * 80)
    if results and gui_success:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    
    print("=" * 80)

if __name__ == "__main__":
    main() 