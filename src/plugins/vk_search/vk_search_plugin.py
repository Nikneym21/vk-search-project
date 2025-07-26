"""
Плагин для поиска по VK API
"""

import asyncio
import time
from typing import Any, Dict, List

import aiohttp

from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin
from src.plugins.vk_search.vk_time_utils import to_vk_timestamp


class VKSearchPlugin(BasePlugin):
    """Плагин для поиска по VK API"""

    def __init__(self):
        super().__init__()
        self.name = "VKSearchPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для поиска постов в VK через API"

        # Зависимости плагинов
        self.token_manager = None

        # Оптимизированная конфигурация для ускорения
        self.config = {
            "access_token": None,
            "api_version": "5.131",
            "request_delay": 0.05,  # Уменьшено с 0.1 до 0.05 (агрессивнее)
            "max_requests_per_second": 12,  # Увеличено с 8 до 12
            "timeout": 10,  # Уменьшено с 15 до 10
            "max_retries": 3,
            "batch_size": 12,  # Увеличено с 8 до 12
            "max_batches": 15,  # Увеличено с 10 до 15
            "use_connection_pooling": True,
            "enable_caching": True,
            "cache_ttl": 600,  # Увеличено до 10 минут
            "adaptive_rate_limiting": True,
            "min_delay": 0.03,  # Еще меньше минимальная задержка
            "max_delay": 0.8,  # Уменьшена максимальная задержка
        }

        # Статистика и метрики производительности
        self.requests_made = 0
        self.session = None
        self.cache = {}
        self.token_usage = {}
        self.rate_limit_hits = 0
        self.response_times = []
        self.last_request_time = 0

        # Интеллектуальное кэширование
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "popular_queries": {},
            "query_patterns": {},
            "cache_size_limit": 1000,
            "preload_enabled": True,
        }

        # Предзагрузка популярных запросов
        self.popular_queries = [
            "новости",
            "технологии",
            "программирование",
            "python",
            "разработка",
            "web",
            "mobile",
            "ai",
            "машинное обучение",
            "data science",
        ]

    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина VK Search")

        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return

        self.log_info("Плагин VK Search инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})

    def set_token_manager(self, token_manager):
        """Устанавливает связь с TokenManagerPlugin"""
        self.token_manager = token_manager
        self.log_info("TokenManager подключен к VKSearchPlugin")

    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина VK Search")

        if self.session:
            asyncio.create_task(self.session.close())

        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин VK Search завершен")

    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        if not self.config.get("access_token"):
            self.log_error("Отсутствует access_token")
            return False
        return True

    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["access_token"]

    async def _rate_limit(self) -> None:
        """Адаптивный Rate limiting для VK API"""
        current_time = time.time()

        # Адаптивная регулировка задержки
        if self.config["adaptive_rate_limiting"]:
            # Если недавно был rate limit, увеличиваем задержку
            if self.rate_limit_hits > 0:
                delay = min(self.config["max_delay"], self.config["request_delay"] * (1.5**self.rate_limit_hits))
            else:
                # Если все хорошо, постепенно уменьшаем задержку
                delay = max(self.config["min_delay"], self.config["request_delay"] * 0.95)

            # Ограничиваем задержку в заданных пределах
            delay = max(self.config["min_delay"], min(self.config["max_delay"], delay))
        else:
            delay = self.config["request_delay"]

        if delay > 0:
            await asyncio.sleep(delay)

        self.last_request_time = current_time

    def _get_best_token(self, available_tokens: List[str]) -> str:
        """Выбирает токен с наименьшей нагрузкой"""
        if not self.token_usage:
            return available_tokens[0]

        # Находим токен с наименьшим количеством запросов
        best_token = min(self.token_usage.items(), key=lambda x: x[1])[0]

        # Если токен не в списке доступных, берем первый
        if best_token not in available_tokens:
            return available_tokens[0]

        return best_token

    def _update_token_usage(self, token: str):
        """Обновляет статистику использования токена"""
        self.token_usage[token] = self.token_usage.get(token, 0) + 1

    def _is_cache_valid(self, cache_entry: dict) -> bool:
        """Проверяет валидность кэша"""
        if not self.config["enable_caching"]:
            return False

        current_time = time.time()
        return current_time - cache_entry["timestamp"] < self.config["cache_ttl"]

    def _update_cache_stats(self, cache_key: str, hit: bool):
        """Обновляет статистику кэша"""
        if hit:
            self.cache_stats["hits"] += 1
            # Увеличиваем счетчик популярности запроса
            self.cache_stats["popular_queries"][cache_key] = self.cache_stats["popular_queries"].get(cache_key, 0) + 1
        else:
            self.cache_stats["misses"] += 1

    def _analyze_query_patterns(self, query: str):
        """Анализирует паттерны запросов"""
        # Простой анализ: разбиваем запрос на слова
        words = query.lower().split()
        for word in words:
            if len(word) > 2:  # Игнорируем короткие слова
                self.cache_stats["query_patterns"][word] = self.cache_stats["query_patterns"].get(word, 0) + 1

    def _preload_popular_queries(self):
        """Предзагружает популярные запросы"""
        if not self.config["enable_caching"] or not self.cache_stats["preload_enabled"]:
            return

        self.log_info("🔄 Предзагрузка популярных запросов...")

        # Получаем топ-5 самых популярных запросов
        popular = sorted(self.cache_stats["popular_queries"].items(), key=lambda x: x[1], reverse=True)[:5]

        # Добавляем базовые популярные запросы
        for query in self.popular_queries:
            if query not in [p[0] for p in popular]:
                popular.append((query, 1))

        self.log_info(f"📊 Найдено {len(popular)} популярных запросов для предзагрузки")

    def _smart_cache_cleanup(self):
        """Умная очистка кэша с сохранением популярных запросов"""
        if len(self.cache) <= self.cache_stats["cache_size_limit"]:
            return

        self.log_info("🧹 Умная очистка кэша...")

        # Сортируем кэш по популярности и времени
        cache_items = []
        for key, entry in self.cache.items():
            popularity = self.cache_stats["popular_queries"].get(key, 0)
            age = time.time() - entry["timestamp"]
            score = popularity - (age / 3600)  # Популярность минус возраст в часах
            cache_items.append((key, score))

        # Удаляем наименее популярные и старые записи
        cache_items.sort(key=lambda x: x[1])
        to_remove = len(self.cache) - self.cache_stats["cache_size_limit"] // 2

        for key, _ in cache_items[:to_remove]:
            del self.cache[key]

        self.log_info(f"🧹 Удалено {to_remove} записей из кэша")

    def _get_cache_key(self, params: dict) -> str:
        """Генерирует ключ кэша для параметров запроса"""
        import hashlib

        key_data = str(sorted(params.items()))
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает расширенную статистику плагина с интеллектуальными метриками"""
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)

        # Интеллектуальные метрики кэша
        total_cache_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        cache_hit_rate = 0
        if total_cache_requests > 0:
            cache_hit_rate = self.cache_stats["hits"] / total_cache_requests

        # Топ популярных запросов
        top_queries = sorted(self.cache_stats["popular_queries"].items(), key=lambda x: x[1], reverse=True)[:5]

        # Топ паттернов запросов
        top_patterns = sorted(self.cache_stats["query_patterns"].items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "requests_made": self.requests_made,
            "enabled": self.is_enabled(),
            "config": self.get_config(),
            "performance_metrics": {
                "average_response_time": round(avg_response_time, 3),
                "rate_limit_hits": self.rate_limit_hits,
                "cache_size": len(self.cache),
                "cache_hit_rate": round(cache_hit_rate, 3),
                "token_usage": self.token_usage,
                "requests_per_second": (
                    round(self.requests_made / max(1, avg_response_time), 2) if avg_response_time > 0 else 0
                ),
            },
            "intelligent_caching": {
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
                "total_cache_requests": total_cache_requests,
                "cache_hit_rate": round(cache_hit_rate, 3),
                "top_popular_queries": top_queries,
                "top_query_patterns": top_patterns,
                "cache_size_limit": self.cache_stats["cache_size_limit"],
                "preload_enabled": self.cache_stats["preload_enabled"],
            },
        }

    async def search_multiple_queries(
        self,
        queries: List[str],
        start_date,
        end_date,
        exact_match: bool = True,
        minus_words: List[str] = None,
        batch_size: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Поиск по нескольким запросам
        """
        self.log_info(f"🔍 Поиск по {len(queries)} запросам")

        # Подготавливаем пары (запрос, токен)
        keyword_token_pairs = [(query, self.config["access_token"]) for query in queries]

        # Вызываем массовый поиск
        return await self.mass_search_with_tokens(
            keyword_token_pairs, start_date, end_date, exact_match, minus_words, batch_size
        )

    async def _search_single_query(
        self, session, query: str, start_date, end_date, exact_match: bool, minus_words: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск по одному запросу
        """
        params = {
            "q": f'"{query}"' if exact_match else query,
            "count": 200,
            "extended": 1,
            "access_token": self.config["access_token"],
            "v": self.config["api_version"],
        }

        # Добавляем параметры даты если они есть
        if start_date is not None:
            params["start_time"] = start_date
        if end_date is not None:
            params["end_time"] = end_date

        # Добавляем минус-слова
        if minus_words:
            for word in minus_words:
                if word.strip():
                    params["q"] += f" -{word.strip()}"

        # Выполняем поиск
        posts = await self._fetch_vk_batch(session, params, query)
        return posts

    def _check_cache_for_request(self, params, query):
        """Проверяет кэш для запроса"""
        cache_key = self._get_cache_key(params)

        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            # Логируем cache hit только для небольших объемов
            if self.requests_made < 50:
                self.log_info(f"📋 Кэш-хит для запроса '{query}'")
            self._update_cache_stats(cache_key, True)
            return self.cache[cache_key]["data"]

        self._update_cache_stats(cache_key, False)
        return None

    async def _handle_vk_api_response(self, response, query, start_time, params, cache_key):
        """Обрабатывает ответ от VK API"""
        import time

        if response.status != 200:
            if self.requests_made < 50:
                self.log_error(f"HTTP ошибка {response.status} для запроса '{query}'")
            return []

        data = await response.json()

        if "error" in data:
            return await self._handle_api_error(data["error"], query)

        if "response" not in data:
            if self.requests_made < 50:
                self.log_error(f"Неожиданный ответ VK API для запроса '{query}': {data}")
            return []

        items = data["response"].get("items", [])

        # Кэширование результата
        self._cache_response(cache_key, items, query, params)

        # Записываем время ответа
        response_time = time.time() - start_time
        self.response_times.append(response_time)

        # Сбрасываем счетчик rate limit если запрос успешен
        if self.rate_limit_hits > 0:
            self.rate_limit_hits = max(0, self.rate_limit_hits - 1)

        return items

    async def _handle_api_error(self, error, query):
        """Обрабатывает ошибки VK API"""
        error_code = error.get("error_code")

        if error_code == 6:  # Too many requests per second
            if self.rate_limit_hits < 10:
                self.log_warning(f"Rate limit для запроса '{query}', ожидание...")
            self.rate_limit_hits += 1
            await asyncio.sleep(1)
            return "retry"  # Специальный код для повтора
        else:
            if self.requests_made < 100:
                self.log_error(f"Ошибка VK API для запроса '{query}': {error}")
            return []

    def _cache_response(self, cache_key, items, query, params):
        """Сохраняет ответ в кэш"""
        import time

        if self.config["enable_caching"]:
            self.cache[cache_key] = {
                "data": items,
                "timestamp": time.time(),
                "query": query,
                "params": params,
            }
            # Умная очистка кэша при необходимости
            self._smart_cache_cleanup()

    async def _make_vk_request(self, session, params, query, attempt):
        """Выполняет один запрос к VK API"""
        import time

        await self._rate_limit()

        # Обновляем статистику использования токена
        token = params.get("access_token")
        if token:
            self._update_token_usage(token)

        start_time = time.time()
        cache_key = self._get_cache_key(params)

        try:
            async with session.get("https://api.vk.com/method/newsfeed.search", params=params) as response:
                self.requests_made += 1
                return await self._handle_vk_api_response(response, query, start_time, params, cache_key)

        except Exception as e:
            if self.requests_made < 100:
                self.log_error(f"Ошибка запроса для '{query}': {e}")
            return []

    async def _fetch_vk_batch(self, session, params, query, retry_count=3):
        """
        Оптимизированное получение одной партии результатов от VK API с интеллектуальным кэшированием
        """
        # Анализируем паттерны запроса
        self._analyze_query_patterns(query)

        # Проверяем кэш
        cached_result = self._check_cache_for_request(params, query)
        if cached_result is not None:
            return cached_result

        # Попытки запроса с retry логикой
        for attempt in range(retry_count):
            result = await self._make_vk_request(session, params, query, attempt)

            if result == "retry":
                continue  # Повторяем запрос при rate limit
            elif isinstance(result, list):
                return result  # Успешный результат

            # При других ошибках ждём перед повтором
            if attempt < retry_count - 1:
                await asyncio.sleep(1)

        return []  # Все попытки исчерпаны

    def _parse_datetime(self, datetime_str: str) -> int:
        """
        Парсинг даты в timestamp с использованием vk_time_utils
        """
        try:
            # Разбиваем строку на дату и время
            date_part, time_part = datetime_str.split(" ")
            return to_vk_timestamp(date_part, time_part, "Europe/Moscow")
        except ValueError:
            raise ValueError(f"Неверный формат даты: {datetime_str}. Ожидается формат: DD.MM.YYYY HH:MM")

    def _convert_dates_to_timestamps(self, start_date, end_date):
        """Конвертирует даты в timestamp для VK API"""
        _start_ts = start_date
        _end_ts = end_date

        if isinstance(start_date, str):
            date_part, time_part = start_date.split(" ")
            _start_ts = to_vk_timestamp(date_part, time_part, "Europe/Moscow")

        if isinstance(end_date, str):
            date_part, time_part = end_date.split(" ")
            _end_ts = to_vk_timestamp(date_part, time_part, "Europe/Moscow")

        return _start_ts, _end_ts

    def _log_search_progress(self, total_queries, batch_size, current_index=None, progress_type="start"):
        """Логирует прогресс поиска с оптимизацией для больших объёмов"""
        if progress_type == "start":
            if total_queries > 10:
                self.log_info(f"🚀 Массовый поиск: {total_queries} запросов, batch_size={batch_size}")
            else:
                self.log_info(f"🚀 Оптимизированный массовый поиск для {total_queries} запросов")
                self.log_info(f"⚙️ Batch size: {batch_size}, Max batches: {self.config['max_batches']}")

        elif progress_type == "batch" and current_index is not None:
            if total_queries > 20 and current_index % (batch_size * 5) == 0:
                progress = (current_index / total_queries) * 100
                self.log_info(f"📊 Прогресс: {progress:.1f}% ({current_index}/{total_queries} запросов)")

        elif progress_type == "batch_result":
            if total_queries > 20:
                batch_num = (current_index // batch_size) + 1
                self.log_info(f"📈 Батч {batch_num}: получено постов")

    def _create_search_params(self, keyword, token, exact_match, start_ts, end_ts, minus_words):
        """Создаёт параметры для поискового запроса"""
        params = {
            "q": f'"{keyword}"' if exact_match else keyword,
            "count": 200,
            "extended": 1,
            "access_token": token,
            "v": self.config["api_version"],
        }

        if start_ts is not None:
            params["start_time"] = start_ts
        if end_ts is not None:
            params["end_time"] = end_ts

        if minus_words:
            for word in minus_words:
                if word.strip():
                    params["q"] += f" -{word.strip()}"

        return params

    async def _process_search_batch(self, session, batch, exact_match, start_ts, end_ts, minus_words):
        """Обрабатывает один батч поисковых запросов"""
        tasks = []

        for keyword, token in batch:
            # Умная ротация токенов - выбираем токен с наименьшей нагрузкой
            available_tokens = [t for _, t in batch]
            best_token = self._get_best_token(available_tokens)

            params = self._create_search_params(keyword, best_token, exact_match, start_ts, end_ts, minus_words)

            # Создаём задачи для разных offset'ов
            max_batches = self.config["max_batches"]
            offsets = [j * 200 for j in range(max_batches)]

            for offset in offsets:
                params_copy = params.copy()
                params_copy["offset"] = offset
                tasks.append(self._fetch_vk_batch(session, params_copy, keyword))

        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        batch_posts = []

        for result in results:
            if isinstance(result, list):
                batch_posts.extend(result)
            elif isinstance(result, Exception):
                self._handle_search_error(result)

        return batch_posts

    def _handle_search_error(self, error):
        """Обрабатывает ошибки поиска с оптимизацией логирования"""
        # Логируем только первые ошибки для больших объемов
        if self.requests_made < 50:
            self.log_error(f"Ошибка поиска: {error}")

    def _log_final_statistics(self, total_queries, total_posts):
        """Логирует финальную статистику поиска"""
        if total_queries > 10:
            self.log_info(f"✅ Завершено: {total_posts} постов, {self.requests_made} запросов")
        else:
            self.log_info(f"✅ Получено {total_posts} постов от VK API")
            self.log_info(f"📊 Статистика: {self.requests_made} запросов, {len(self.response_times)} измерений времени")

    async def mass_search_with_tokens(
        self,
        keyword_token_pairs: List[tuple] = None,
        queries: List[str] = None,
        tokens: List[str] = None,
        start_date=None,
        end_date=None,
        exact_match: bool = True,
        minus_words: List[str] = None,
        batch_size: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Оптимизированный массовый асинхронный поиск с умной ротацией токенов

        Args:
            keyword_token_pairs: Старый формат - пары (keyword, token)
            queries: Новый формат - список запросов
            tokens: Новый формат - список токенов
        """
        # Поддержка обоих форматов вызова
        if keyword_token_pairs:
            # Старый формат
            pairs = keyword_token_pairs
        elif queries and tokens:
            # Новый формат - создаём пары с ротацией токенов
            pairs = []
            for i, query in enumerate(queries):
                token = tokens[i % len(tokens)]
                pairs.append((query, token))
        else:
            raise ValueError("Необходимо передать либо keyword_token_pairs, либо queries+tokens")

        # Используем конфигурационный batch_size если не передан
        if batch_size is None:
            batch_size = self.config["batch_size"]

        total_queries = len(pairs)

        # Конвертация дат
        start_ts, end_ts = self._convert_dates_to_timestamps(start_date, end_date)

        # Логирование начала поиска
        self._log_search_progress(total_queries, batch_size, progress_type="start")

        all_posts = []

        # Настройка HTTP клиента
        timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
        connector = (
            aiohttp.TCPConnector(
                limit=150,  # Увеличено с 100 до 150
                limit_per_host=30,  # Увеличено с 20 до 30
                ttl_dns_cache=600,  # Увеличено до 10 минут
                use_dns_cache=True,
                keepalive_timeout=30,  # Новый параметр
                enable_cleanup_closed=True  # Новый параметр
            )
        )

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Обрабатываем запросы батчами
            for i in range(0, len(pairs), batch_size):
                batch = pairs[i : i + batch_size]

                # Логирование прогресса
                self._log_search_progress(total_queries, batch_size, i, "batch")

                # Обработка батча
                batch_posts = await self._process_search_batch(
                    session, batch, exact_match, start_ts, end_ts, minus_words
                )
                all_posts.extend(batch_posts)

                # Логирование результата батча
                if total_queries > 20:
                    self._log_search_progress(total_queries, batch_size, i, "batch_result")

        # Очистка кэша и финальная статистика
        self._cleanup_cache()

        # Применяем строгую локальную фильтрацию
        if all_posts:
            # Извлекаем ключевые слова в зависимости от формата вызова
            filter_keywords = []
            if queries:
                filter_keywords = queries
            elif keyword_token_pairs:
                filter_keywords = [pair[0] for pair in keyword_token_pairs]  # Извлекаем только ключевые слова

            if filter_keywords:
                all_posts = self._strict_local_filter(all_posts, filter_keywords, exact_match)

        self._log_final_statistics(total_queries, len(all_posts))

        return all_posts

    def _cleanup_cache(self):
        """Очищает устаревшие записи кэша"""
        if not self.config["enable_caching"]:
            return

        expired_keys = []

        for key, entry in self.cache.items():
            if not self._is_cache_valid(entry):
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.log_info(f"🧹 Очищено {len(expired_keys)} устаревших записей кэша")

    def _strict_local_filter(self, posts: List[Dict], keywords: List[str], exact_match: bool = True) -> List[Dict]:
        """
        Улучшенная строгая локальная фильтрация постов по ключевым словам
        Исправляет проблемы VK API, который возвращает нерелевантные результаты
        """
        if not posts or not keywords:
            return posts

        filtered_posts = []

        for post in posts:
            text = post.get('text', '').strip() if post.get('text') else ''
            if not text:
                continue

            # Нормализация текста - убираем лишние символы но сохраняем структуру
            normalized_text = self._normalize_text_for_search(text)
            matched_keywords = []

            # Проверяем каждое ключевое слово
            for keyword in keywords:
                keyword_normalized = self._normalize_text_for_search(keyword)

                if exact_match:
                    # Более гибкая проверка: ищем ключевое слово как подстроку
                    if keyword_normalized.lower() in normalized_text.lower():
                        matched_keywords.append(keyword)
                else:
                    # Менее строгая проверка: все слова должны присутствовать
                    words = keyword_normalized.lower().split()
                    if all(word in normalized_text.lower() for word in words):
                        matched_keywords.append(keyword)

            # Добавляем пост только если есть совпадения
            if matched_keywords:
                post['keywords_matched'] = matched_keywords
                filtered_posts.append(post)

        original_count = len(posts)
        filtered_count = len(filtered_posts)
        self.log_info(f"🔍 Улучшенная фильтрация: {original_count} → {filtered_count} постов")

        return filtered_posts

    def _normalize_text_for_search(self, text: str) -> str:
        """
        Нормализация текста для поиска
        Убирает лишние символы но сохраняет основной смысл
        """
        if not text:
            return ""

        # Убираем множественные переносы строк и пробелы
        normalized = ' '.join(text.split())

        # Убираем некоторые специальные символы но сохраняем пунктуацию
        import re
        normalized = re.sub(r'[^\w\s\.\,\!\?\-\—\«\»\"\'\:\;\(\)]', ' ', normalized)

        # Убираем множественные пробелы
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    def _preload_cache_for_keywords(self, keywords: List[str]) -> None:
        """
        Предварительная загрузка кэша для популярных ключевых слов
        """
        preload_keywords = []
        for keyword in keywords:
            # Проверяем, есть ли похожие запросы в кэше
            similar_keys = [k for k in self.cache.keys() if keyword.lower() in k.lower()]
            if not similar_keys:
                preload_keywords.append(keyword)

        if preload_keywords:
            self.log_info(f"🔄 Предзагрузка кэша для {len(preload_keywords)} новых ключевых слов")

    def _get_cache_suggestions(self, query: str) -> List[str]:
        """
        Возвращает предложения из кэша для похожих запросов
        """
        suggestions = []
        query_lower = query.lower()

        for cached_key in self.cache.keys():
            if query_lower in cached_key.lower() or cached_key.lower() in query_lower:
                suggestions.append(cached_key)

        return suggestions[:5]  # Максимум 5 предложений

    def _optimize_query_order(self, keyword_token_pairs: List[tuple]) -> List[tuple]:
        """
        Оптимизирует порядок запросов: сначала кэшированные, потом новые
        """
        cached_pairs = []
        new_pairs = []

        for pair in keyword_token_pairs:
            query_key = self._get_cache_key({"q": pair[0], "token": pair[1]})
            if query_key in self.cache:
                cached_pairs.append(pair)
            else:
                new_pairs.append(pair)

        # Сначала кэшированные (быстрые), потом новые
        optimized_order = cached_pairs + new_pairs

        if len(cached_pairs) > 0:
            self.log_info(f"🎯 Оптимизация: {len(cached_pairs)} запросов из кэша, {len(new_pairs)} новых")

        return optimized_order
