#!/usr/bin/env python3
"""
Юнит-тест для VKSearchPlugin
Проверяет базовую функциональность плагина
"""

import unittest
import sys
import os
import aiohttp
import json
import asyncio
import csv
from datetime import datetime
import glob
import pandas as pd
from src.plugins.vk_search.vk_search_plugin import VKSearchPlugin
from src.plugins.post_processor.text_processing.text_processing_plugin import TextProcessingPlugin

# Добавляем путь к src для импорта плагинов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

TIMEZONE_OFFSET = -7  # Владивосток -> Москва

class TestVKSearchPlugin(unittest.TestCase):
    """Тесты для VKSearchPlugin"""

    def setUp(self):
        """Инициализация перед каждым тестом"""
        self.plugin = VKSearchPlugin()
        self.plugin.config["access_token"] = "test_token"
        self.plugin.initialize()

    def tearDown(self):
        """Очистка после каждого теста"""
        self.plugin.shutdown()

    def test_plugin_initialization(self):
        """Тест инициализации плагина"""
        self.assertTrue(self.plugin.is_enabled())
        self.assertEqual(self.plugin.name, "VKSearchPlugin")
        self.assertEqual(self.plugin.version, "1.0.0")

    def test_config_validation(self):
        """Тест валидации конфигурации"""
        # С валидным токеном
        self.assertTrue(self.plugin.validate_config())

        # Без токена
        self.plugin.config["access_token"] = None
        self.assertFalse(self.plugin.validate_config())

        # Восстанавливаем токен
        self.plugin.config["access_token"] = "test_token"
        self.assertTrue(self.plugin.validate_config())

    def test_required_config_keys(self):
        """Тест обязательных ключей конфигурации"""
        required_keys = self.plugin.get_required_config_keys()
        self.assertIn("access_token", required_keys)

    def test_rate_limit_config(self):
        """Тест конфигурации rate limit"""
        self.assertIn("request_delay", self.plugin.config)
        self.assertIn("max_requests_per_second", self.plugin.config)
        self.assertIn("timeout", self.plugin.config)

        # Проверяем, что значения разумные
        self.assertGreater(self.plugin.config["request_delay"], 0)
        self.assertGreater(self.plugin.config["max_requests_per_second"], 0)
        self.assertGreater(self.plugin.config["timeout"], 0)

    def test_statistics(self):
        """Тест получения статистики плагина"""
        stats = self.plugin.get_statistics()
        self.assertIn("requests_made", stats)
        self.assertIn("enabled", stats)
        self.assertIn("config", stats)
        self.assertTrue(stats["enabled"])

    def test_parse_datetime(self):
        """Тест парсинга даты"""
        # Тест валидной даты
        timestamp = self.plugin._parse_datetime("25.07.2025 15:30")
        self.assertIsInstance(timestamp, int)
        self.assertGreater(timestamp, 0)

        # Тест невалидной даты
        with self.assertRaises(ValueError):
            self.plugin._parse_datetime("invalid_date")

    def test_real_mass_search_with_tokens(self):
        """Реальный массовый поиск по VK API с несколькими ключевыми словами"""
        # 1. Получаем токен
        with open("config/vk_token.txt", encoding="utf-8") as f:
            tokens = [line.strip() for line in f if line.strip()]
        real_token = tokens[0]

        # 2. Получаем ключевые слова и даты
        with open("data/parser_settings.json", encoding="utf-8") as f:
            settings = json.load(f)
        keywords = [k.strip() for k in settings["keywords"].split("\n") if k.strip()]
        test_keywords = keywords[:4]  # Берём первые 3-4 фразы
        # Даты поиска: с 24.07.2025 по 24.07.2025
        start_date = "24.07.2025"
        end_date = "24.07.2025"

        # 3. Готовим пары (ключевое слово, токен)
        keyword_token_pairs = [(kw, real_token) for kw in test_keywords]

        # 4. Запускаем массовый поиск
        async def run_mass_search():
            plugin = VKSearchPlugin()
            plugin.config["access_token"] = real_token
            plugin.initialize()
            # Преобразуем даты в timestamp
            start_ts = plugin._parse_datetime(f"{start_date} 00:00")
            end_ts = plugin._parse_datetime(f"{end_date} 23:59")
            results = await plugin.mass_search_with_tokens(
                keyword_token_pairs,
                start_date=start_ts,
                end_date=end_ts,
                exact_match=settings.get("exact_match", False),
                minus_words=None
            )
            return results

        results = asyncio.run(run_mass_search())
        print(f"Найдено постов: {len(results)}")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "VK API вернул пустой результат — проверьте токен и параметры запроса")

    def test_export_raw_results_no_internal_filter(self):
        """Массовый поиск по VK API без внутренней фильтрации, экспорт в CSV для сравнения с другим парсером"""
        import csv
        from datetime import datetime
        import aiohttp
        # 1. Получаем все токены
        with open("config/vk_token.txt", encoding="utf-8") as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            raise Exception("Нет доступных токенов в config/vk_token.txt")

        # 2. Ключевые слова и даты
        with open("data/parser_settings.json", encoding="utf-8") as f:
            settings = json.load(f)
        keywords = [k.strip() for k in settings["keywords"].split("\n") if k.strip()]
        test_keywords = keywords[:4]
        start_date = "24.07.2025"
        end_date = "24.07.2025"

        # 3. Назначаем каждому ключу свой токен (по кругу)
        keyword_token_pairs = [(kw, tokens[i % len(tokens)]) for i, kw in enumerate(test_keywords)]

        async def run_mass_search():
            plugin = VKSearchPlugin()
            plugin.config["access_token"] = tokens[0]
            plugin.initialize()
            start_ts = plugin._parse_datetime(f"{start_date} 00:00")
            end_ts = plugin._parse_datetime(f"{end_date} 23:59")
            all_posts = []
            timeout = aiohttp.ClientTimeout(total=plugin.config["timeout"])
            max_batches = 5
            offsets = [j * 200 for j in range(max_batches)]
            max_parallel_offset = 5
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for keyword, token in keyword_token_pairs:
                    params = {
                        'q': keyword,
                        'count': 200,
                        'start_time': start_ts,
                        'end_time': end_ts,
                        'extended': 1,
                        'access_token': token,
                        'v': plugin.config["api_version"]
                    }
                    posts_for_keyword = []
                    for i in range(0, len(offsets), max_parallel_offset):
                        offset_batch = offsets[i:i+max_parallel_offset]
                        tasks = []
                        for offset in offset_batch:
                            params_copy = params.copy()
                            params_copy['offset'] = offset
                            tasks.append(plugin._fetch_vk_batch(session, params_copy, keyword))
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for result in results:
                            if isinstance(result, list):
                                posts_for_keyword.extend(result)
                            elif isinstance(result, Exception):
                                plugin.log_error(f"Ошибка поиска: {result}")
                        await asyncio.sleep(0.3)
                    # Используем FilterPlugin для фильтрации
                    from src.plugins.filter.filter_plugin import FilterPlugin
                    filter_plugin = FilterPlugin()
                    filter_plugin.initialize()
                    filtered = filter_plugin.filter_posts_by_keyword_with_text_cleaning(posts_for_keyword, keyword, exact_match=False)
                    all_posts.extend(filtered)
            return all_posts

        results = asyncio.run(run_mass_search())
        # Экспортируем в CSV с нужными колонками
        csv_columns = [
            "Ссылка", "Текст", "Тип", "Автор", "Ссылка на автора", "Дата", "Лайков", "Комментариев", "Репостов", "Переходов", "Просмотров вики страницы", "Просмотров", "Лайков / Просмотров", "Комментариев / Просмотров", "Репостов / Просмотров", "Переходов / Просмотров", "Просмотров вики страницы / Просмотров поста"
        ]
        def get_stat(post, key):
            v = post.get(key, 0)
            if isinstance(v, dict):
                return v.get('count', 0)
            return v
        def get_value(post, key):
            # Маппинг для соответствия колонок
            if key == "Ссылка":
                return f"https://vk.com/wall{post.get('owner_id')}_{post.get('id')}"
            if key == "Текст":
                return post.get('text', '')
            if key == "Тип":
                return "Пост"
            if key == "Автор":
                return post.get('author_name', '')
            if key == "Ссылка на автора":
                owner_id = post.get('owner_id')
                if owner_id < 0:
                    return f"https://vk.com/club{abs(owner_id)}"
                else:
                    return f"https://vk.com/id{owner_id}"
            if key == "Дата":
                dt = datetime.fromtimestamp(post.get('date'))
                return dt.strftime("%H:%M %d.%m.%Y")
            if key == "Лайков":
                return get_stat(post, 'likes')
            if key == "Комментариев":
                return get_stat(post, 'comments')
            if key == "Репостов":
                return get_stat(post, 'reposts')
            if key == "Переходов":
                return 0
            if key == "Просмотров вики страницы":
                return 0
            if key == "Просмотров":
                return get_stat(post, 'views')
            # Отношения — считаем если есть просмотры
            if key == "Лайков / Просмотров":
                likes = get_stat(post, 'likes')
                views = get_stat(post, 'views')
                return f"{(likes/views*100):.3f}%" if views else "0%"
            if key == "Комментариев / Просмотров":
                comments = get_stat(post, 'comments')
                views = get_stat(post, 'views')
                return f"{(comments/views*100):.3f}%" if views else "0%"
            if key == "Репостов / Просмотров":
                reposts = get_stat(post, 'reposts')
                views = get_stat(post, 'views')
                return f"{(reposts/views*100):.3f}%" if views else "0%"
            if key == "Переходов / Просмотров":
                return "0%"
            if key == "Просмотров вики страницы / Просмотров поста":
                return "0%"
            return ""
        with open("vk_raw_results_24.07.2025.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(csv_columns)
            for post in results:
                row = [get_value(post, col) for col in csv_columns]
                writer.writerow(row)
        print(f"Экспортировано {len(results)} постов в vk_raw_results_24.07.2025.csv")

    def test_export_raw_results_no_exact_match(self):
        """Массовый поиск по VK API без точного совпадения (exact_match=False), экспорт в CSV для сравнения с эталоном"""
        import csv
        from datetime import datetime
        import aiohttp
        # 1. Получаем все токены
        with open("config/vk_token.txt", encoding="utf-8") as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            raise Exception("Нет доступных токенов в config/vk_token.txt")

        # 2. Ключевые слова и даты
        with open("data/parser_settings.json", encoding="utf-8") as f:
            settings = json.load(f)
        keywords = [k.strip() for k in settings["keywords"].split("\n") if k.strip()]
        test_keywords = keywords[:4]
        start_date = "24.07.2025"
        end_date = "24.07.2025"

        # 3. Назначаем каждому ключу свой токен (по кругу)
        keyword_token_pairs = [(kw, tokens[i % len(tokens)]) for i, kw in enumerate(test_keywords)]

        async def run_mass_search():
            plugin = VKSearchPlugin()
            plugin.config["access_token"] = tokens[0]
            plugin.initialize()
            start_ts = plugin._parse_datetime(f"{start_date} 00:00")
            end_ts = plugin._parse_datetime(f"{end_date} 23:59")
            all_posts = []
            timeout = aiohttp.ClientTimeout(total=plugin.config["timeout"])
            max_batches = 5
            offsets = [j * 200 for j in range(max_batches)]
            max_parallel_offset = 5
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for keyword, token in keyword_token_pairs:
                    params = {
                        'q': keyword,
                        'count': 200,
                        'start_time': start_ts,
                        'end_time': end_ts,
                        'extended': 1,
                        'access_token': token,
                        'v': plugin.config["api_version"]
                    }
                    posts_for_keyword = []
                    for i in range(0, len(offsets), max_parallel_offset):
                        offset_batch = offsets[i:i+max_parallel_offset]
                        tasks = []
                        for offset in offset_batch:
                            params_copy = params.copy()
                            params_copy['offset'] = offset
                            tasks.append(plugin._fetch_vk_batch(session, params_copy, keyword))
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for result in results:
                            if isinstance(result, list):
                                posts_for_keyword.extend(result)
                            elif isinstance(result, Exception):
                                plugin.log_error(f"Ошибка поиска: {result}")
                        await asyncio.sleep(0.3)
                    # Используем FilterPlugin для фильтрации
                    from src.plugins.filter.filter_plugin import FilterPlugin
                    filter_plugin = FilterPlugin()
                    filter_plugin.initialize()
                    filtered = filter_plugin.filter_posts_by_keyword_with_text_cleaning(posts_for_keyword, keyword, exact_match=False)
                    all_posts.extend(filtered)
            return all_posts

        results = asyncio.run(run_mass_search())
        # Экспортируем в CSV с нужными колонками
        csv_columns = [
            "Ссылка", "Текст", "Тип", "Автор", "Ссылка на автора", "Дата", "Лайков", "Комментариев", "Репостов", "Переходов", "Просмотров вики страницы", "Просмотров", "Лайков / Просмотров", "Комментариев / Просмотров", "Репостов / Просмотров", "Переходов / Просмотров", "Просмотров вики страницы / Просмотров поста"
        ]
        def get_stat(post, key):
            v = post.get(key, 0)
            if isinstance(v, dict):
                return v.get('count', 0)
            return v
        def get_value(post, key):
            if key == "Ссылка":
                return f"https://vk.com/wall{post.get('owner_id')}_{post.get('id')}"
            if key == "Текст":
                return post.get('text', '')
            if key == "Тип":
                return "Пост"
            if key == "Автор":
                return post.get('author_name', '')
            if key == "Ссылка на автора":
                owner_id = post.get('owner_id')
                if owner_id < 0:
                    return f"https://vk.com/club{abs(owner_id)}"
                else:
                    return f"https://vk.com/id{owner_id}"
            if key == "Дата":
                dt = datetime.fromtimestamp(post.get('date'))
                return dt.strftime("%H:%M %d.%m.%Y")
            if key == "Лайков":
                return get_stat(post, 'likes')
            if key == "Комментариев":
                return get_stat(post, 'comments')
            if key == "Репостов":
                return get_stat(post, 'reposts')
            if key == "Переходов":
                return 0
            if key == "Просмотров вики страницы":
                return 0
            if key == "Просмотров":
                return get_stat(post, 'views')
            if key == "Лайков / Просмотров":
                likes = get_stat(post, 'likes')
                views = get_stat(post, 'views')
                return f"{(likes/views*100):.3f}%" if views else "0%"
            if key == "Комментариев / Просмотров":
                comments = get_stat(post, 'comments')
                views = get_stat(post, 'views')
                return f"{(comments/views*100):.3f}%" if views else "0%"
            if key == "Репостов / Просмотров":
                reposts = get_stat(post, 'reposts')
                views = get_stat(post, 'views')
                return f"{(reposts/views*100):.3f}%" if views else "0%"
            if key == "Переходов / Просмотров":
                return "0%"
            if key == "Просмотров вики страницы / Просмотров поста":
                return "0%"
            return ""
        with open("vk_raw_results_no_exact_24.07.2025.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(csv_columns)
            for post in results:
                row = [get_value(post, col) for col in csv_columns]
                writer.writerow(row)
        print(f"Экспортировано {len(results)} постов в vk_raw_results_no_exact_24.07.2025.csv")

    def test_export_raw_results_no_date_filter(self):
        """Массовый поиск по VK API без фильтрации по дате (start_time и end_time не передаются), экспорт в CSV для сравнения с эталоном"""
        import csv
        from datetime import datetime
        import aiohttp
        # 1. Получаем все токены
        with open("config/vk_token.txt", encoding="utf-8") as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            raise Exception("Нет доступных токенов в config/vk_token.txt")

        # 2. Ключевые слова
        with open("data/parser_settings.json", encoding="utf-8") as f:
            settings = json.load(f)
        keywords = [k.strip() for k in settings["keywords"].split("\n") if k.strip()]
        test_keywords = keywords[:4]

        # 3. Назначаем каждому ключу свой токен (по кругу)
        keyword_token_pairs = [(kw, tokens[i % len(tokens)]) for i, kw in enumerate(test_keywords)]

        async def run_mass_search():
            plugin = VKSearchPlugin()
            plugin.config["access_token"] = tokens[0]
            plugin.initialize()
            # Для тестов без фильтрации по дате задаём широкий диапазон (например, сутки)
            start_ts = plugin._parse_datetime("24.07.2025 00:00")
            end_ts = plugin._parse_datetime("24.07.2025 23:59")
            all_posts = []
            timeout = aiohttp.ClientTimeout(total=plugin.config["timeout"])
            max_batches = 5
            offsets = [j * 200 for j in range(max_batches)]
            max_parallel_offset = 5
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for keyword, token in keyword_token_pairs:
                    params = {
                        'q': keyword,
                        'count': 200,
                        'extended': 1,
                        'access_token': token,
                        'v': plugin.config["api_version"]
                    }
                    posts_for_keyword = []
                    for i in range(0, len(offsets), max_parallel_offset):
                        offset_batch = offsets[i:i+max_parallel_offset]
                        tasks = []
                        for offset in offset_batch:
                            params_copy = params.copy()
                            params_copy['offset'] = offset
                            tasks.append(plugin._fetch_vk_batch(session, params_copy, keyword))
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for result in results:
                            if isinstance(result, list):
                                posts_for_keyword.extend(result)
                            elif isinstance(result, Exception):
                                plugin.log_error(f"Ошибка поиска: {result}")
                        await asyncio.sleep(0.3)
                    # Используем FilterPlugin для фильтрации
                    from src.plugins.filter.filter_plugin import FilterPlugin
                    filter_plugin = FilterPlugin()
                    filter_plugin.initialize()
                    filtered = filter_plugin.filter_posts_by_keyword_with_text_cleaning(posts_for_keyword, keyword, exact_match=False)
                    all_posts.extend(filtered)
            return all_posts

        results = asyncio.run(run_mass_search())
        # Экспортируем в CSV с нужными колонками
        csv_columns = [
            "Ссылка", "Текст", "Тип", "Автор", "Ссылка на автора", "Дата", "Лайков", "Комментариев", "Репостов", "Переходов", "Просмотров вики страницы", "Просмотров", "Лайков / Просмотров", "Комментариев / Просмотров", "Репостов / Просмотров", "Переходов / Просмотров", "Просмотров вики страницы / Просмотров поста"
        ]
        def get_stat(post, key):
            v = post.get(key, 0)
            if isinstance(v, dict):
                return v.get('count', 0)
            return v
        def get_value(post, key):
            if key == "Ссылка":
                return f"https://vk.com/wall{post.get('owner_id')}_{post.get('id')}"
            if key == "Текст":
                return post.get('text', '')
            if key == "Тип":
                return "Пост"
            if key == "Автор":
                return post.get('author_name', '')
            if key == "Ссылка на автора":
                owner_id = post.get('owner_id')
                if owner_id < 0:
                    return f"https://vk.com/club{abs(owner_id)}"
                else:
                    return f"https://vk.com/id{owner_id}"
            if key == "Дата":
                dt = datetime.fromtimestamp(post.get('date'))
                return dt.strftime("%H:%M %d.%m.%Y")
            if key == "Лайков":
                return get_stat(post, 'likes')
            if key == "Комментариев":
                return get_stat(post, 'comments')
            if key == "Репостов":
                return get_stat(post, 'reposts')
            if key == "Переходов":
                return 0
            if key == "Просмотров вики страницы":
                return 0
            if key == "Просмотров":
                return get_stat(post, 'views')
            if key == "Лайков / Просмотров":
                likes = get_stat(post, 'likes')
                views = get_stat(post, 'views')
                return f"{(likes/views*100):.3f}%" if views else "0%"
            if key == "Комментариев / Просмотров":
                comments = get_stat(post, 'comments')
                views = get_stat(post, 'views')
                return f"{(comments/views*100):.3f}%" if views else "0%"
            if key == "Репостов / Просмотров":
                reposts = get_stat(post, 'reposts')
                views = get_stat(post, 'views')
                return f"{(reposts/views*100):.3f}%" if views else "0%"
            if key == "Переходов / Просмотров":
                return "0%"
            if key == "Просмотров вики страницы / Просмотров поста":
                return "0%"
            return ""
        with open("vk_raw_results_no_date_24.07.2025.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(csv_columns)
            for post in results:
                row = [get_value(post, col) for col in csv_columns]
                writer.writerow(row)
        print(f"Экспортировано {len(results)} постов в vk_raw_results_no_date_24.07.2025.csv")

    def test_export_raw_results_exact_match_no_date(self):
        """Массовый поиск по VK API с точным совпадением (exact_match=True), фильтрация по дате на стороне API (start_time/end_time в UTC, рассчитанные из Москвы), экспорт в JSON для отладки"""
        import aiohttp
        from datetime import datetime, timedelta, timezone
        # 1. Получаем все токены
        with open("config/vk_token.txt", encoding="utf-8") as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            raise Exception("Нет доступных токенов в config/vk_token.txt")
        # 2. Ключевые слова (используем все)
        with open("data/parser_settings.json", encoding="utf-8") as f:
            settings = json.load(f)
        keywords = [k.strip() for k in settings["keywords"].split("\n") if k.strip()]
        test_keywords = keywords  # используем все ключи
        # 3. Назначаем каждому ключу свой токен (по кругу)
        keyword_token_pairs = [(kw, tokens[i % len(tokens)]) for i, kw in enumerate(test_keywords)]
        # 4. Переводим московское время в UTC для фильтрации на стороне API
        def moscow_to_utc_timestamp(dt_str):
            moscow_tz = timezone(timedelta(hours=3))
            dt = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            dt = dt.replace(tzinfo=moscow_tz)
            dt_utc = dt.astimezone(timezone.utc)
            return int(dt_utc.timestamp())
        start_ts_utc = moscow_to_utc_timestamp("24.07.2025 00:00")
        end_ts_utc = moscow_to_utc_timestamp("24.07.2025 23:59")
        async def run_mass_search():
            plugin = VKSearchPlugin()
            plugin.config["access_token"] = tokens[0] # For validation only
            plugin.initialize()
            all_posts = []
            timeout = aiohttp.ClientTimeout(total=plugin.config["timeout"])
            max_batches = 5
            offsets = [j * 200 for j in range(max_batches)]
            max_parallel_offset = 5
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for keyword, token in keyword_token_pairs:
                    params = {
                        'q': f'"{keyword}"',
                        'count': 200,
                        'extended': 1,
                        'access_token': token,
                        'v': plugin.config["api_version"],
                        'start_time': start_ts_utc,
                        'end_time': end_ts_utc
                    }
                    posts_for_keyword = []
                    for i in range(0, len(offsets), max_parallel_offset):
                        offset_batch = offsets[i:i+max_parallel_offset]
                        tasks = []
                        for offset in offset_batch:
                            params_copy = params.copy()
                            params_copy['offset'] = offset
                            tasks.append(plugin._fetch_vk_batch(session, params_copy, keyword))
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for result in results:
                            if isinstance(result, list):
                                posts_for_keyword.extend(result)
                            elif isinstance(result, Exception):
                                plugin.log_error(f"Ошибка поиска: {result}")
                        await asyncio.sleep(0.3)
                    # Локальная фильтрация по ключу (точное вхождение с очисткой текста)
                    text_plugin = TextProcessingPlugin()
                    keyword_clean = text_plugin.clean_text_completely(keyword)
                    filtered = []
                    for post in posts_for_keyword:
                        text = str(post.get('text', '') or post.get('post_text', ''))
                        text_clean = text_plugin.clean_text_completely(text)
                        if keyword_clean in text_clean:
                            filtered.append(post)
                    all_posts.extend(filtered)
            # Только фильтрация уникальных постов по (owner_id, id)
            seen = set()
            unique_posts = []
            for post in all_posts:
                key = (post.get('owner_id'), post.get('id'))
                if key not in seen:
                    seen.add(key)
                    unique_posts.append(post)
            return unique_posts
        raw_results = asyncio.run(run_mass_search())
        with open("vk_raw_results_exact_no_date_24.07.2025.json", "w", encoding="utf-8") as f:
            json.dump(raw_results, f, ensure_ascii=False, indent=2)
        print(f"Экспортировано {len(raw_results)} постов в vk_raw_results_exact_no_date_24.07.2025.json")
        self.assertEqual(len(raw_results), 49, f"Ожидалось 49 постов, получено {len(raw_results)}")

    def test_local_exact_match_filter(self):
        """Локальная фильтрация по точному вхождению (с очисткой текста) на последнем парсинге"""
        # 1. Найти последний search_*.csv
        result_files = sorted(glob.glob('data/results/search_*.csv'))
        assert result_files, "Нет файлов search_*.csv в data/results/"
        last_result = result_files[-1]
        df = pd.read_csv(last_result)
        print(f"Загружено {len(df)} постов из {last_result}")
        # 2. Ключевые фразы
        import json
        with open("data/parser_settings.json", encoding="utf-8") as f:
            settings = json.load(f)
        keywords = [k.strip() for k in settings["keywords"].split("\n") if k.strip()]
        # 3. Инициализация плагинов
        vk_plugin = VKSearchPlugin()
        text_plugin = TextProcessingPlugin()
        # 4. Локальная фильтрация: хотя бы одна фраза содержится в тексте (точно, с очисткой)
        filtered = []
        for _, row in df.iterrows():
            text = str(row.get('text', ''))
            text_clean = text_plugin.clean_text_completely(text)
            for keyword in keywords:
                keyword_clean = text_plugin.clean_text_completely(keyword)
                if keyword_clean in text_clean:
                    filtered.append(row.to_dict())
                    break
        print(f"Отфильтровано {len(filtered)} постов из {len(df)}")
        self.assertGreater(len(filtered), 0, "Не найдено ни одного поста с ключевыми фразами")
        # 5. Экспорт отфильтрованных результатов
        filtered_df = pd.DataFrame(filtered)
        output_file = f"filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filtered_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Экспортировано в {output_file}")


if __name__ == '__main__':
    unittest.main()
