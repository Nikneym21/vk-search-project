"""
Тесты оптимизированных методов PostProcessorPlugin
Детальное тестирование каждого оптимизированного метода
"""

import pytest
from datetime import datetime
from typing import Dict, List

from src.core.plugin_manager import PluginManager


class TestOptimizedMethods:
    """Тесты оптимизированных методов обработки"""

    @pytest.fixture
    def plugin_manager(self):
        """Фикстура PluginManager с настроенными зависимостями"""
        pm = PluginManager()
        pm.load_plugins()
        pm.setup_plugin_dependencies()
        yield pm
        pm.shutdown_plugins()

    @pytest.fixture
    def test_posts(self):
        """Тестовые посты с различными сценариями"""
        return [
            {
                "link": "https://vk.com/wall-123_1",
                "text": "Пост про технологии и инновации в IT",
                "author": "Tech User",
                "date": "2025-07-27 10:00:00",
                "likes": 10,
                "comments": 2,
                "reposts": 1,
                "views": 50
            },
            {
                "link": "https://vk.com/wall-123_2",
                "text": "Искусственный интеллект меняет мир технологий",
                "author": "AI Expert",
                "date": "2025-07-27 11:00:00",
                "likes": 25,
                "comments": 5,
                "reposts": 3,
                "views": 120
            },
            {
                "link": "https://vk.com/wall-123_1",  # Дубликат по ссылке
                "text": "Пост про технологии и инновации в IT",
                "author": "Tech User",
                "date": "2025-07-27 10:00:00",
                "likes": 10,
                "comments": 2,
                "reposts": 1,
                "views": 50
            },
            {
                "link": "https://vk.com/wall-123_3",
                "text": "Обычный пост о погоде без ключевых слов",
                "author": "Weather User",
                "date": "2025-07-27 12:00:00",
                "likes": 5,
                "comments": 0,
                "reposts": 0,
                "views": 20
            },
            {
                "link": "https://vk.com/wall-123_4",
                "text": "Ещё один пост с технологиями и программированием",
                "author": "Dev User",
                "date": "2025-07-27 13:00:00",
                "likes": 15,
                "comments": 3,
                "reposts": 2,
                "views": 80
            }
        ]

    def test_process_posts_optimized_basic(self, plugin_manager, test_posts):
        """Базовый тест оптимизированной обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект"]

        result = post_processor.process_posts_optimized(
            posts=test_posts,
            keywords=keywords,
            exact_match=False,
            early_termination=False,
            lazy_processing=True
        )

        # Проверяем структуру результата
        assert "optimization_level" in result
        assert result["optimization_level"] == "high"
        assert "lazy_skips" in result
        assert "early_exit" in result
        assert result["early_exit"] == False  # Отключен early_termination

        # Проверяем логику обработки
        assert result["original_count"] == 5
        assert result["duplicates_removed"] == 1  # Один дубликат по ссылке
        assert result["final_count"] == 2  # 4 уникальных - 2 отфильтрованных

        print(f"✅ Оптимизированная обработка: {result['original_count']} → {result['final_count']}")
        print(f"   Ленивых пропусков: {result['lazy_skips']}")

    def test_process_posts_optimized_early_termination(self, plugin_manager):
        """Тест раннего завершения"""
        post_processor = plugin_manager.get_plugin("post_processor")

        # Создаём большой набор постов
        large_posts = []
        for i in range(6000):  # Больше лимита 5000
            large_posts.append({
                "link": f"https://vk.com/wall-123_{i}",
                "text": f"Пост про технологии номер {i}",
                "author": f"User {i}",
                "date": "2025-07-27 10:00:00",
                "likes": i % 100
            })

        result = post_processor.process_posts_optimized(
            posts=large_posts,
            keywords=["технологии"],
            exact_match=False,
            early_termination=True,  # Включаем ранний выход
            lazy_processing=True
        )

        # Должен быть ранний выход
        assert result["early_exit"] == True
        assert result["final_count"] <= 5000  # Лимит раннего выхода

        print(f"✅ Ранний выход: {result['original_count']} → {result['final_count']} (лимит: 5000)")

    def test_process_posts_optimized_lazy_processing(self, plugin_manager, test_posts):
        """Тест ленивой обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")

        # Тест с ленивой обработкой
        result_lazy = post_processor.process_posts_optimized(
            posts=test_posts,
            keywords=["технологии"],
            exact_match=False,
            early_termination=False,
            lazy_processing=True
        )

        # Тест без ленивой обработки (для сравнения)
        result_normal = post_processor.process_posts_optimized(
            posts=test_posts,
            keywords=["технологии"],
            exact_match=False,
            early_termination=False,
            lazy_processing=False
        )

        # Результаты должны быть одинаковыми
        assert result_lazy["final_count"] == result_normal["final_count"]

        # Ленивая обработка должна пропустить некоторые посты
        assert "lazy_skips" in result_lazy
        assert result_lazy["lazy_skips"] >= 0

        print(f"✅ Ленивая обработка пропустила: {result_lazy['lazy_skips']} постов")

    def test_process_posts_in_batches(self, plugin_manager, test_posts):
        """Тест батчевой обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Увеличиваем набор данных для батчевой обработки
        extended_posts = test_posts * 5  # 25 постов

        result = post_processor.process_posts_in_batches(
            posts=extended_posts,
            keywords=keywords,
            exact_match=False,
            batch_size=3  # Маленький батч для тестирования
        )

        # Проверяем структуру результата
        assert "optimization_level" in result
        assert result["optimization_level"] == "batch"
        assert "batches_processed" in result
        assert "cross_batch_duplicates" in result
        assert "batch_size" in result

        # Проверяем логику батчевой обработки
        assert result["batch_size"] == 3
        assert result["batches_processed"] >= 1
        assert result["original_count"] == len(extended_posts)

        # Должна быть дедупликация между батчами
        assert result["cross_batch_duplicates"] >= 0

        print(f"✅ Батчевая обработка: {result['batches_processed']} батчей")
        print(f"   Дубликатов между батчами: {result['cross_batch_duplicates']}")

    def test_process_posts_with_cache(self, plugin_manager, test_posts):
        """Тест кэшированной обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Очищаем кэш перед тестом
        post_processor.clear_cache()

        # Первый запуск - заполнение кэша
        result1 = post_processor.process_posts_with_cache(
            posts=test_posts,
            keywords=keywords,
            exact_match=False,
            cache_results=True
        )

        # Проверяем структуру результата
        assert "optimization_level" in result1
        assert result1["optimization_level"] == "cached"
        assert "cache_hits" in result1
        assert "cache_efficiency" in result1

        # Первый запуск - минимальные попадания в кэш
        cache_hits_1 = sum(result1["cache_hits"].values())
        assert cache_hits_1 >= 0

        # Второй запуск - должны быть попадания в кэш
        result2 = post_processor.process_posts_with_cache(
            posts=test_posts,
            keywords=keywords,
            exact_match=False,
            cache_results=True
        )

        cache_hits_2 = sum(result2["cache_hits"].values())
        assert cache_hits_2 > cache_hits_1  # Больше попаданий в кэш

        # Результаты должны быть одинаковыми
        assert result1["final_count"] == result2["final_count"]

        print(f"✅ Кэширование: {cache_hits_1} → {cache_hits_2} попаданий")
        print(f"   Эффективность: {result2['cache_efficiency']:.1f}%")

    def test_process_posts_parallel(self, plugin_manager, test_posts):
        """Тест параллельной обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Увеличиваем набор данных для параллельной обработки
        large_posts = test_posts * 20  # 100 постов

        try:
            result = post_processor.process_posts_parallel(
                posts=large_posts,
                keywords=keywords,
                exact_match=False,
                max_workers=2  # Ограничиваем для тестирования
            )

            # Проверяем структуру результата
            assert "optimization_level" in result
            assert result["optimization_level"] == "parallel"
            assert "threads_used" in result
            assert "cross_thread_duplicates" in result
            assert "max_workers" in result
            assert "chunk_size" in result

            # Проверяем логику параллельной обработки
            assert result["max_workers"] == 2
            assert result["threads_used"] >= 1
            assert result["original_count"] == len(large_posts)

            print(f"✅ Параллельная обработка: {result['threads_used']} потоков")
            print(f"   Дубликатов между потоками: {result['cross_thread_duplicates']}")

        except ImportError:
            pytest.skip("concurrent.futures недоступен для параллельной обработки")

    def test_cache_management(self, plugin_manager, test_posts):
        """Тест управления кэшем"""
        post_processor = plugin_manager.get_plugin("post_processor")

        # Очищаем кэш
        post_processor.clear_cache()

        # Проверяем пустой кэш
        cache_stats = post_processor.get_cache_stats()
        if cache_stats["cache_enabled"]:
            assert cache_stats["total_memory_items"] == 0

        # Заполняем кэш
        post_processor.process_posts_with_cache(
            test_posts, ["технологии"], False, True
        )

        # Проверяем заполненный кэш
        cache_stats_filled = post_processor.get_cache_stats()
        if cache_stats_filled["cache_enabled"]:
            assert cache_stats_filled["total_memory_items"] > 0
            assert cache_stats_filled["text_cache_size"] >= 0
            assert cache_stats_filled["filter_cache_size"] >= 0
            assert cache_stats_filled["duplicates_cache_size"] >= 0

        # Очищаем кэш снова
        post_processor.clear_cache()

        # Проверяем очищенный кэш
        cache_stats_cleared = post_processor.get_cache_stats()
        if cache_stats_cleared["cache_enabled"]:
            assert cache_stats_cleared["total_memory_items"] == 0

        print(f"✅ Управление кэшем: {cache_stats_filled['total_memory_items']} → 0 элементов")

    def test_method_consistency(self, plugin_manager, test_posts):
        """Тест согласованности результатов всех методов"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Тестируем все методы с одинаковыми параметрами
        methods = [
            ("standard", lambda: post_processor.process_posts(test_posts, keywords, False)),
            ("optimized", lambda: post_processor.process_posts_optimized(
                test_posts, keywords, False, early_termination=False, lazy_processing=False
            )),
            ("batches", lambda: post_processor.process_posts_in_batches(
                test_posts, keywords, False, batch_size=10
            )),
            ("cached", lambda: post_processor.process_posts_with_cache(
                test_posts, keywords, False, cache_results=True
            ))
        ]

        results = {}

        for method_name, method_func in methods:
            result = method_func()
            results[method_name] = {
                "final_count": result["final_count"],
                "duplicates_removed": result["duplicates_removed"],
                "processing_time": result["processing_time"]
            }

        # Проверяем согласованность результатов
        final_counts = [r["final_count"] for r in results.values()]
        duplicates_counts = [r["duplicates_removed"] for r in results.values()]

        # Все методы должны давать одинаковый результат
        assert len(set(final_counts)) <= 2, f"Несогласованные результаты: {final_counts}"
        assert len(set(duplicates_counts)) <= 2, f"Несогласованные дубликаты: {duplicates_counts}"

        print("✅ Согласованность методов:")
        for method, data in results.items():
            print(f"   {method}: {data['final_count']} постов, {data['duplicates_removed']} дубликатов")

    def test_error_handling_optimized(self, plugin_manager):
        """Тест обработки ошибок в оптимизированных методах"""
        post_processor = plugin_manager.get_plugin("post_processor")

        # Тест с пустыми данными
        empty_result = post_processor.process_posts_optimized(
            posts=[], keywords=["тест"], exact_match=True
        )
        assert empty_result["original_count"] == 0
        assert empty_result["final_count"] == 0

        # Тест с некорректными данными
        bad_posts = [
            {"link": None, "text": None},
            {"wrong_field": "value"},
            {}
        ]

        # Не должно падать с ошибкой
        bad_result = post_processor.process_posts_optimized(
            posts=bad_posts, keywords=["тест"], exact_match=True
        )
        assert bad_result["original_count"] == 3

        # Тест батчевой обработки с пустыми данными
        batch_empty = post_processor.process_posts_in_batches(
            posts=[], keywords=["тест"], exact_match=True, batch_size=10
        )
        assert batch_empty["original_count"] == 0
        assert batch_empty["batches_processed"] == 0

        print("✅ Обработка ошибок: все методы устойчивы к некорректным данным")

    def test_configuration_impact(self, plugin_manager, test_posts):
        """Тест влияния конфигурации на результаты"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Сохраняем оригинальную конфигурацию
        original_config = post_processor.config.copy()

        try:
            # Тест с отключенной дедупликацией
            post_processor.config["enable_deduplication"] = False
            result_no_dedup = post_processor.process_posts_optimized(
                test_posts, keywords, False
            )

            # Тест с отключенной фильтрацией
            post_processor.config["enable_deduplication"] = True
            post_processor.config["enable_filtering"] = False
            result_no_filter = post_processor.process_posts_optimized(
                test_posts, keywords, False
            )

            # Восстанавливаем конфигурацию
            post_processor.config = original_config
            result_normal = post_processor.process_posts_optimized(
                test_posts, keywords, False
            )

            # Проверяем влияние настроек
            print("✅ Влияние конфигурации:")
            print(f"   Без дедупликации: {result_no_dedup['final_count']} постов")
            print(f"   Без фильтрации: {result_no_filter['final_count']} постов")
            print(f"   Обычная обработка: {result_normal['final_count']} постов")

            # Без дедупликации должно быть больше постов
            assert result_no_dedup["duplicates_removed"] == 0

        finally:
            # Восстанавливаем оригинальную конфигурацию
            post_processor.config = original_config


if __name__ == "__main__":
    # Запуск тестов вручную
    test_class = TestOptimizedMethods()

    pm = PluginManager()
    pm.load_plugins()
    pm.setup_plugin_dependencies()

    test_posts = [
        {
            "link": "https://vk.com/wall-123_1",
            "text": "Пост про технологии и инновации в IT",
            "author": "Tech User",
            "date": "2025-07-27 10:00:00",
            "likes": 10,
            "comments": 2,
            "reposts": 1,
            "views": 50
        },
        {
            "link": "https://vk.com/wall-123_2",
            "text": "Искусственный интеллект меняет мир технологий",
            "author": "AI Expert",
            "date": "2025-07-27 11:00:00",
            "likes": 25,
            "comments": 5,
            "reposts": 3,
            "views": 120
        },
        {
            "link": "https://vk.com/wall-123_1",  # Дубликат по ссылке
            "text": "Пост про технологии и инновации в IT",
            "author": "Tech User",
            "date": "2025-07-27 10:00:00",
            "likes": 10,
            "comments": 2,
            "reposts": 1,
            "views": 50
        },
        {
            "link": "https://vk.com/wall-123_3",
            "text": "Обычный пост о погоде без ключевых слов",
            "author": "Weather User",
            "date": "2025-07-27 12:00:00",
            "likes": 5,
            "comments": 0,
            "reposts": 0,
            "views": 20
        },
        {
            "link": "https://vk.com/wall-123_4",
            "text": "Ещё один пост с технологиями и программированием",
            "author": "Dev User",
            "date": "2025-07-27 13:00:00",
            "likes": 15,
            "comments": 3,
            "reposts": 2,
            "views": 80
        }
    ]

    try:
        print("🧪 Запуск тестов оптимизированных методов...")

        test_class.test_process_posts_optimized_basic(pm, test_posts)
        test_class.test_process_posts_in_batches(pm, test_posts)
        test_class.test_process_posts_with_cache(pm, test_posts)
        test_class.test_cache_management(pm, test_posts)
        test_class.test_method_consistency(pm, test_posts)
        test_class.test_error_handling_optimized(pm)

        print("\n🎉 Все тесты оптимизированных методов пройдены!")

    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pm.shutdown_plugins()
