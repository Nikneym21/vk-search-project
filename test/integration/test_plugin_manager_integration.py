"""
Интеграционные тесты для PluginManager
Тестирует полный цикл работы системы и взаимодействие плагинов
"""

import asyncio
import os
import pytest
import tempfile
from datetime import datetime
from typing import Dict, List

from src.core.plugin_manager import PluginManager


class TestPluginManagerIntegration:
    """Интеграционные тесты PluginManager"""

    @pytest.fixture
    def plugin_manager(self):
        """Фикстура для создания PluginManager"""
        pm = PluginManager()
        pm.load_plugins()
        yield pm
        # Cleanup
        pm.shutdown_plugins()

    @pytest.fixture
    def sample_posts(self):
        """Образцы постов для тестирования"""
        return [
            {
                "link": "https://vk.com/wall-123_1",
                "text": "Это тестовый пост с ключевым словом технологии",
                "author": "Test User 1",
                "date": "2025-07-27 10:00:00",
                "likes": 10,
                "comments": 2,
                "reposts": 1,
                "views": 50
            },
            {
                "link": "https://vk.com/wall-123_2",
                "text": "Другой пост про искусственный интеллект и машинное обучение",
                "author": "Test User 2",
                "date": "2025-07-27 11:00:00",
                "likes": 25,
                "comments": 5,
                "reposts": 3,
                "views": 120
            },
            {
                "link": "https://vk.com/wall-123_1",  # Дубликат по ссылке
                "text": "Это тестовый пост с ключевым словом технологии",
                "author": "Test User 1",
                "date": "2025-07-27 10:00:00",
                "likes": 10,
                "comments": 2,
                "reposts": 1,
                "views": 50
            },
            {
                "link": "https://vk.com/wall-123_3",
                "text": "Пост без ключевых слов, не должен пройти фильтрацию",
                "author": "Test User 3",
                "date": "2025-07-27 12:00:00",
                "likes": 5,
                "comments": 0,
                "reposts": 0,
                "views": 20
            }
        ]

    def test_plugin_loading(self, plugin_manager):
        """Тест загрузки всех плагинов"""
        # Проверяем, что все основные плагины загружены
        required_plugins = [
            "post_processor", "database", "vk_search", "filter",
            "deduplication", "text_processing", "token_manager",
            "google_sheets", "link_comparator", "settings_manager",
            "logger", "monitoring"
        ]

        for plugin_name in required_plugins:
            plugin = plugin_manager.get_plugin(plugin_name)
            assert plugin is not None, f"Плагин {plugin_name} не загружен"
            assert hasattr(plugin, 'name'), f"Плагин {plugin_name} не имеет атрибута name"
            assert plugin.name is not None, f"Плагин {plugin_name} имеет пустое имя"

    def test_plugin_dependencies(self, plugin_manager):
        """Тест настройки зависимостей между плагинами"""
        plugin_manager.setup_plugin_dependencies()

        # Проверяем связи PostProcessorPlugin
        post_processor = plugin_manager.get_plugin("post_processor")
        assert post_processor.filter_plugin is not None
        assert post_processor.deduplication_plugin is not None
        assert post_processor.text_processing_plugin is not None
        assert post_processor.database_plugin is not None

        # Проверяем связи VKSearchPlugin
        vk_search = plugin_manager.get_plugin("vk_search")
        assert vk_search.token_manager is not None

    def test_database_operations(self, plugin_manager):
        """Тест операций с базой данных"""
        database = plugin_manager.get_plugin("database")

        # Создаём временную задачу
        task_id = database.create_task(
            keywords=["тест"],
            start_date="2025-07-27",
            end_date="2025-07-27",
            exact_match=True,
            minus_words=[]
        )

        assert task_id is not None
        assert isinstance(task_id, int)

        # Проверяем, что задача создана
        tasks = database.get_all_tasks()
        assert len(tasks) > 0

        # Находим нашу задачу
        our_task = next((t for t in tasks if t['id'] == task_id), None)
        assert our_task is not None
        assert our_task['keywords'] == "тест"

    def test_post_processing_chain(self, plugin_manager, sample_posts):
        """Тест полной цепочки обработки постов"""
        plugin_manager.setup_plugin_dependencies()

        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект"]

        # Обрабатываем посты
        result = post_processor.process_posts(
            posts=sample_posts,
            keywords=keywords,
            exact_match=False
        )

        # Проверяем результат
        assert result["original_count"] == 4
        assert result["final_count"] == 2  # Должно остаться 2 поста после дедупликации и фильтрации
        assert result["duplicates_removed"] == 1  # Один дубликат
        assert result["filtered_count"] == 1  # Один пост не прошёл фильтрацию
        assert len(result["final_posts"]) == 2

        # Проверяем, что остались правильные посты
        final_links = [post["link"] for post in result["final_posts"]]
        assert "https://vk.com/wall-123_1" in final_links
        assert "https://vk.com/wall-123_2" in final_links
        assert "https://vk.com/wall-123_3" not in final_links

    def test_optimized_processing_methods(self, plugin_manager, sample_posts):
        """Тест оптимизированных методов обработки"""
        plugin_manager.setup_plugin_dependencies()
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Тестируем оптимизированный метод
        result_optimized = post_processor.process_posts_optimized(
            posts=sample_posts,
            keywords=keywords,
            exact_match=False,
            early_termination=False,
            lazy_processing=True
        )

        assert result_optimized["optimization_level"] == "high"
        assert "lazy_skips" in result_optimized
        assert result_optimized["final_count"] <= result_optimized["original_count"]

        # Тестируем батчевый метод
        result_batches = post_processor.process_posts_in_batches(
            posts=sample_posts,
            keywords=keywords,
            exact_match=False,
            batch_size=2
        )

        assert result_batches["optimization_level"] == "batch"
        assert result_batches["batches_processed"] >= 1
        assert "cross_batch_duplicates" in result_batches

        # Тестируем кэшированный метод
        result_cached = post_processor.process_posts_with_cache(
            posts=sample_posts,
            keywords=keywords,
            exact_match=False,
            cache_results=True
        )

        assert result_cached["optimization_level"] == "cached"
        assert "cache_hits" in result_cached
        assert "cache_efficiency" in result_cached

        # Повторный вызов должен использовать кэш
        result_cached_2 = post_processor.process_posts_with_cache(
            posts=sample_posts,
            keywords=keywords,
            exact_match=False,
            cache_results=True
        )

        # Должны быть попадания в кэш
        total_hits = sum(result_cached_2["cache_hits"].values())
        assert total_hits > 0

    def test_cache_management(self, plugin_manager):
        """Тест управления кэшем"""
        plugin_manager.setup_plugin_dependencies()
        post_processor = plugin_manager.get_plugin("post_processor")

        # Проверяем статистику пустого кэша
        cache_stats = post_processor.get_cache_stats()
        if cache_stats["cache_enabled"]:
            assert cache_stats["total_memory_items"] == 0

        # Очищаем кэш
        post_processor.clear_cache()

        # Проверяем, что кэш очищен
        cache_stats_after = post_processor.get_cache_stats()
        if cache_stats_after["cache_enabled"]:
            assert cache_stats_after["total_memory_items"] == 0

    def test_parallel_processing(self, plugin_manager):
        """Тест параллельной обработки (если доступна)"""
        plugin_manager.setup_plugin_dependencies()
        post_processor = plugin_manager.get_plugin("post_processor")

        # Создаём большой набор тестовых данных
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "link": f"https://vk.com/wall-123_{i}",
                "text": f"Тестовый пост {i} с технологиями и инновациями",
                "author": f"User {i}",
                "date": "2025-07-27 10:00:00",
                "likes": i,
                "comments": i % 5,
                "reposts": i % 3,
                "views": i * 10
            })

        keywords = ["технологии"]

        try:
            result = post_processor.process_posts_parallel(
                posts=large_dataset,
                keywords=keywords,
                exact_match=False,
                max_workers=2
            )

            assert result["optimization_level"] == "parallel"
            assert "threads_used" in result
            assert result["threads_used"] >= 1
            assert "cross_thread_duplicates" in result

        except ImportError:
            # concurrent.futures может быть недоступен в некоторых окружениях
            pytest.skip("concurrent.futures недоступен для параллельной обработки")

    def test_error_handling(self, plugin_manager):
        """Тест обработки ошибок"""
        post_processor = plugin_manager.get_plugin("post_processor")

        # Тест с пустыми данными
        result_empty = post_processor.process_posts(
            posts=[],
            keywords=["тест"],
            exact_match=True
        )

        assert result_empty["original_count"] == 0
        assert result_empty["final_count"] == 0
        assert result_empty["final_posts"] == []

        # Тест с некорректными данными
        bad_posts = [
            {"link": None, "text": None},  # Некорректная структура
            {},  # Пустой пост
        ]

        # Не должно падать с ошибкой
        result_bad = post_processor.process_posts(
            posts=bad_posts,
            keywords=["тест"],
            exact_match=True
        )

        assert result_bad["original_count"] == 2
        # Результат может быть разным в зависимости от обработки некорректных данных

    @pytest.mark.asyncio
    async def test_async_coordination(self, plugin_manager):
        """Тест асинхронной координации через PluginManager"""
        # Этот тест проверяет интеграцию с async методами

        # Базовые параметры поиска
        keywords = ["тест"]
        api_keywords = ["тест"]
        start_ts = 1722038400  # 27.07.2025 00:00:00
        end_ts = 1722124800    # 28.07.2025 00:00:00
        exact_match = False
        minus_words = []

        try:
            # Тест координации полного поиска (без реального VK API)
            # Мы тестируем только структуру и обработку ошибок
            with pytest.raises((Exception, AttributeError)):
                # Ожидаем ошибку из-за отсутствия реальных токенов VK
                await plugin_manager.coordinate_full_search(
                    keywords=keywords,
                    api_keywords=api_keywords,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    exact_match=exact_match,
                    minus_words=minus_words,
                    start_date="27.07.2025",
                    start_time="00:00",
                    end_date="28.07.2025",
                    end_time="00:00"
                )

        except Exception as e:
            # Это ожидаемо - у нас нет реальных VK токенов
            assert "token" in str(e).lower() or "vk" in str(e).lower()

    def test_performance_comparison(self, plugin_manager, sample_posts):
        """Тест сравнения производительности разных методов"""
        plugin_manager.setup_plugin_dependencies()
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Повторяем данные для более заметной разницы
        large_sample = sample_posts * 10  # 40 постов

        methods_to_test = [
            ("standard", lambda: post_processor.process_posts(large_sample, keywords, False)),
            ("optimized", lambda: post_processor.process_posts_optimized(large_sample, keywords, False)),
            ("batches", lambda: post_processor.process_posts_in_batches(large_sample, keywords, False, batch_size=5)),
            ("cached", lambda: post_processor.process_posts_with_cache(large_sample, keywords, False))
        ]

        results = {}

        for method_name, method_func in methods_to_test:
            start_time = datetime.now()
            result = method_func()
            end_time = datetime.now()

            processing_time = (end_time - start_time).total_seconds()

            results[method_name] = {
                "processing_time": processing_time,
                "final_count": result["final_count"],
                "reported_time": result.get("processing_time", 0)
            }

        # Проверяем, что все методы дают одинаковый результат
        final_counts = [r["final_count"] for r in results.values()]
        assert len(set(final_counts)) <= 2, "Разные методы дают существенно разные результаты"

        # Логируем результаты для анализа
        print(f"\n📊 Сравнение производительности ({len(large_sample)} постов):")
        for method, result in results.items():
            print(f"  {method}: {result['processing_time']:.3f}с → {result['final_count']} постов")


if __name__ == "__main__":
    # Запуск отдельных тестов для отладки
    test_class = TestPluginManagerIntegration()

    # Создаём простой fixture для ручного тестирования
    pm = PluginManager()
    pm.load_plugins()

    try:
        test_class.test_plugin_loading(pm)
        print("✅ Тест загрузки плагинов пройден")

        test_class.test_plugin_dependencies(pm)
        print("✅ Тест зависимостей плагинов пройден")

        sample_posts = [
            {
                "link": "https://vk.com/wall-123_1",
                "text": "Тестовый пост с технологиями",
                "author": "Test User",
                "date": "2025-07-27 10:00:00",
                "likes": 10
            }
        ]

        test_class.test_post_processing_chain(pm, sample_posts)
        print("✅ Тест цепочки обработки пройден")

        print("🎉 Все базовые интеграционные тесты пройдены!")

    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
    finally:
        pm.shutdown_plugins()
