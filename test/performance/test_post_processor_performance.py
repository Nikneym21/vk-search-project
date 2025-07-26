"""
Тесты производительности для PostProcessorPlugin
Бенчмарки оптимизированных методов обработки постов
"""

import pytest
import time
from datetime import datetime
from typing import Dict, List

from src.core.plugin_manager import PluginManager


class TestPostProcessorPerformance:
    """Тесты производительности PostProcessorPlugin"""

    @pytest.fixture
    def plugin_manager(self):
        """Фикстура для создания PluginManager"""
        pm = PluginManager()
        pm.load_plugins()
        pm.setup_plugin_dependencies()
        yield pm
        pm.shutdown_plugins()

    @pytest.fixture
    def small_dataset(self):
        """Малый датасет для быстрых тестов (100 постов)"""
        return self._generate_posts(100)

    @pytest.fixture
    def medium_dataset(self):
        """Средний датасет (1000 постов)"""
        return self._generate_posts(1000)

    @pytest.fixture
    def large_dataset(self):
        """Большой датасет (5000 постов)"""
        return self._generate_posts(5000)

    def _generate_posts(self, count: int) -> List[Dict]:
        """Генерация тестовых постов"""
        posts = []
        keywords_variants = [
            "технологии и инновации в современном мире",
            "искусственный интеллект и машинное обучение",
            "разработка программного обеспечения",
            "цифровая трансформация бизнеса",
            "интернет вещей и автоматизация",
            "блокчейн и криптовалюты",
            "кибербезопасность и защита данных",
            "облачные технологии и виртуализация"
        ]

        for i in range(count):
            # Добавляем некоторое количество дубликатов (10%)
            if i % 10 == 0 and i > 0:
                link = f"https://vk.com/wall-123_{i-1}"  # Дубликат предыдущего
            else:
                link = f"https://vk.com/wall-123_{i}"

            text = keywords_variants[i % len(keywords_variants)]
            if i % 7 == 0:  # Некоторые посты без ключевых слов
                text = f"Обычный пост номер {i} без специальных терминов"

            posts.append({
                "link": link,
                "text": text,
                "author": f"Test User {i % 20}",
                "date": f"2025-07-{27 + (i % 3):02d} {10 + (i % 12):02d}:00:00",
                "likes": i % 100,
                "comments": i % 20,
                "reposts": i % 10,
                "views": i * 5
            })

        return posts

    @pytest.mark.benchmark
    def test_standard_processing_performance(self, plugin_manager, medium_dataset, benchmark):
        """Бенчмарк стандартной обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект", "разработка"]

        result = benchmark(
            post_processor.process_posts,
            medium_dataset,
            keywords,
            False
        )

        assert result["final_count"] > 0
        assert result["processing_time"] > 0
        print(f"\n📊 Стандартная обработка: {result['processing_time']:.3f}с → {result['final_count']} постов")

    @pytest.mark.benchmark
    def test_optimized_processing_performance(self, plugin_manager, medium_dataset, benchmark):
        """Бенчмарк оптимизированной обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект", "разработка"]

        result = benchmark(
            post_processor.process_posts_optimized,
            medium_dataset,
            keywords,
            False,
            True,  # early_termination
            True   # lazy_processing
        )

        assert result["final_count"] > 0
        assert result["optimization_level"] == "high"
        print(f"\n📊 Оптимизированная обработка: {result['processing_time']:.3f}с → {result['final_count']} постов")
        print(f"    Ленивых пропусков: {result.get('lazy_skips', 0)}")

    @pytest.mark.benchmark
    def test_batch_processing_performance(self, plugin_manager, large_dataset, benchmark):
        """Бенчмарк батчевой обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект", "разработка"]

        result = benchmark(
            post_processor.process_posts_in_batches,
            large_dataset,
            keywords,
            False,
            500  # batch_size
        )

        assert result["final_count"] > 0
        assert result["optimization_level"] == "batch"
        print(f"\n📊 Батчевая обработка: {result['processing_time']:.3f}с → {result['final_count']} постов")
        print(f"    Батчей обработано: {result['batches_processed']}")

    @pytest.mark.benchmark
    def test_cached_processing_performance(self, plugin_manager, medium_dataset, benchmark):
        """Бенчмарк кэшированной обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект", "разработка"]

        # Первый прогон для заполнения кэша
        post_processor.process_posts_with_cache(medium_dataset, keywords, False, True)

        # Второй прогон с кэшем для бенчмарка
        result = benchmark(
            post_processor.process_posts_with_cache,
            medium_dataset,
            keywords,
            False,
            True
        )

        assert result["final_count"] > 0
        assert result["optimization_level"] == "cached"
        print(f"\n📊 Кэшированная обработка: {result['processing_time']:.3f}с → {result['final_count']} постов")
        print(f"    Эффективность кэша: {result.get('cache_efficiency', 0):.1f}%")

    @pytest.mark.benchmark
    def test_parallel_processing_performance(self, plugin_manager, large_dataset, benchmark):
        """Бенчмарк параллельной обработки"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект", "разработка"]

        try:
            result = benchmark(
                post_processor.process_posts_parallel,
                large_dataset,
                keywords,
                False,
                4  # max_workers
            )

            assert result["final_count"] > 0
            assert result["optimization_level"] == "parallel"
            print(f"\n📊 Параллельная обработка: {result['processing_time']:.3f}с → {result['final_count']} постов")
            print(f"    Потоков использовано: {result.get('threads_used', 0)}")

        except ImportError:
            pytest.skip("concurrent.futures недоступен")

    def test_performance_comparison(self, plugin_manager, medium_dataset):
        """Сравнение производительности всех методов"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект"]

        methods = {
            "standard": lambda: post_processor.process_posts(medium_dataset, keywords, False),
            "optimized": lambda: post_processor.process_posts_optimized(medium_dataset, keywords, False),
            "batches": lambda: post_processor.process_posts_in_batches(medium_dataset, keywords, False, 200),
            "cached_first": lambda: post_processor.process_posts_with_cache(medium_dataset, keywords, False, True),
            "cached_second": lambda: post_processor.process_posts_with_cache(medium_dataset, keywords, False, True)
        }

        results = {}

        for method_name, method_func in methods.items():
            start_time = time.time()
            result = method_func()
            end_time = time.time()

            actual_time = end_time - start_time
            reported_time = result.get("processing_time", actual_time)

            results[method_name] = {
                "actual_time": actual_time,
                "reported_time": reported_time,
                "final_count": result["final_count"],
                "optimization_level": result.get("optimization_level", "standard")
            }

        # Выводим результаты
        print(f"\n📊 Сравнение производительности ({len(medium_dataset)} постов):")
        print("-" * 70)
        print(f"{'Метод':<15} {'Время (с)':<12} {'Результат':<10} {'Оптимизация':<15}")
        print("-" * 70)

        for method, data in results.items():
            print(f"{method:<15} {data['actual_time']:<12.3f} {data['final_count']:<10} {data['optimization_level']:<15}")

        # Проверяем улучшения
        standard_time = results["standard"]["actual_time"]
        optimized_time = results["optimized"]["actual_time"]

        if optimized_time < standard_time:
            improvement = ((standard_time - optimized_time) / standard_time) * 100
            print(f"\n✅ Оптимизированный метод быстрее на {improvement:.1f}%")

        # Проверяем эффект кэширования
        cached_first = results["cached_first"]["actual_time"]
        cached_second = results["cached_second"]["actual_time"]

        if cached_second < cached_first:
            cache_improvement = ((cached_first - cached_second) / cached_first) * 100
            print(f"💾 Кэширование ускорило обработку на {cache_improvement:.1f}%")

    def test_scalability(self, plugin_manager):
        """Тест масштабируемости при увеличении объёма данных"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        dataset_sizes = [100, 500, 1000, 2000]
        results = {}

        for size in dataset_sizes:
            dataset = self._generate_posts(size)

            start_time = time.time()
            result = post_processor.process_posts_optimized(dataset, keywords, False)
            end_time = time.time()

            processing_time = end_time - start_time
            throughput = size / processing_time  # постов в секунду

            results[size] = {
                "time": processing_time,
                "throughput": throughput,
                "final_count": result["final_count"]
            }

        print(f"\n📈 Тест масштабируемости:")
        print("-" * 50)
        print(f"{'Размер':<10} {'Время (с)':<12} {'Постов/с':<12} {'Результат':<10}")
        print("-" * 50)

        for size, data in results.items():
            print(f"{size:<10} {data['time']:<12.3f} {data['throughput']:<12.1f} {data['final_count']:<10}")

        # Проверяем линейную масштабируемость
        small_throughput = results[dataset_sizes[0]]["throughput"]
        large_throughput = results[dataset_sizes[-1]]["throughput"]

        # Пропускная способность не должна сильно падать
        throughput_ratio = large_throughput / small_throughput
        assert throughput_ratio > 0.5, f"Сильное падение производительности: {throughput_ratio:.2f}"

        print(f"\n📊 Коэффициент масштабируемости: {throughput_ratio:.2f}")

    def test_memory_efficiency(self, plugin_manager, large_dataset):
        """Тест эффективности использования памяти"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии"]

        # Тестируем батчевую обработку (должна быть более экономной)
        import psutil
        process = psutil.Process()

        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        result = post_processor.process_posts_in_batches(
            large_dataset, keywords, False, batch_size=100
        )

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        print(f"\n💾 Использование памяти:")
        print(f"    До обработки: {memory_before:.1f} MB")
        print(f"    После обработки: {memory_after:.1f} MB")
        print(f"    Использовано: {memory_used:.1f} MB")
        print(f"    Постов обработано: {len(large_dataset)}")
        print(f"    MB на 1000 постов: {(memory_used / len(large_dataset)) * 1000:.2f}")

        # Память не должна расти слишком сильно
        memory_per_post = memory_used / len(large_dataset)
        assert memory_per_post < 0.1, f"Слишком большое потребление памяти: {memory_per_post:.4f} MB/пост"

    def test_cache_efficiency(self, plugin_manager, medium_dataset):
        """Тест эффективности кэширования"""
        post_processor = plugin_manager.get_plugin("post_processor")
        keywords = ["технологии", "интеллект"]

        # Очищаем кэш
        post_processor.clear_cache()

        # Первый прогон - заполнение кэша
        start_time = time.time()
        result1 = post_processor.process_posts_with_cache(medium_dataset, keywords, False, True)
        time1 = time.time() - start_time

        # Второй прогон - использование кэша
        start_time = time.time()
        result2 = post_processor.process_posts_with_cache(medium_dataset, keywords, False, True)
        time2 = time.time() - start_time

        # Третий прогон с немного другими ключевыми словами
        start_time = time.time()
        result3 = post_processor.process_posts_with_cache(medium_dataset, ["разработка"], False, True)
        time3 = time.time() - start_time

        print(f"\n💾 Тест кэширования:")
        print(f"    Первый прогон (заполнение): {time1:.3f}с")
        print(f"    Второй прогон (кэш): {time2:.3f}с")
        print(f"    Третий прогон (частичный кэш): {time3:.3f}с")

        # Второй прогон должен быть быстрее
        if time2 < time1:
            improvement = ((time1 - time2) / time1) * 100
            print(f"    Ускорение кэша: {improvement:.1f}%")

        # Проверяем статистику кэша
        cache_stats = post_processor.get_cache_stats()
        print(f"    Статистика кэша: {cache_stats}")

        # Кэш должен содержать данные
        if cache_stats["cache_enabled"]:
            assert cache_stats["total_memory_items"] > 0

        # Результаты должны быть одинаковыми
        assert result1["final_count"] == result2["final_count"]


if __name__ == "__main__":
    # Запуск тестов производительности вручную
    test_class = TestPostProcessorPerformance()

    # Создаём тестовое окружение
    pm = PluginManager()
    pm.load_plugins()
    pm.setup_plugin_dependencies()

    # Генерируем тестовые данные
    small_data = test_class._generate_posts(100)
    medium_data = test_class._generate_posts(1000)

    try:
        print("🚀 Запуск тестов производительности...")

        # Сравнение методов
        test_class.test_performance_comparison(pm, medium_data)

        # Тест масштабируемости
        test_class.test_scalability(pm)

        print("\n🎉 Тесты производительности завершены!")

    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pm.shutdown_plugins()
