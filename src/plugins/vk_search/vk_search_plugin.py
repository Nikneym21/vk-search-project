"""
Плагин для поиска по VK API
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...core.event_system import EventType
from ..base_plugin import BasePlugin


class VKSearchPlugin(BasePlugin):
    """Плагин для поиска по VK API"""
    
    def __init__(self):
        super().__init__()
        self.name = "VKSearchPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для поиска постов в VK через API"
        
        # Оптимизированная конфигурация для ускорения
        self.config = {
            "access_token": None,
            "api_version": "5.131",
            "request_delay": 0.1,  # Уменьшено с 0.3 до 0.1
            "max_requests_per_second": 8,  # Увеличено с 3 до 8
            "timeout": 15,  # Уменьшено с 30 до 15
            "max_retries": 3,
            "batch_size": 8,  # Увеличено с 3 до 8
            "max_batches": 10,  # Увеличено с 5 до 10
            "use_connection_pooling": True,
            "enable_caching": True,
            "cache_ttl": 300,  # 5 минут
            "adaptive_rate_limiting": True,
            "min_delay": 0.05,  # Минимальная задержка
            "max_delay": 1.0,   # Максимальная задержка
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
            "preload_enabled": True
        }
        
        # Предзагрузка популярных запросов
        self.popular_queries = [
            "новости", "технологии", "программирование", "python", "разработка",
            "web", "mobile", "ai", "машинное обучение", "data science"
        ]
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина VK Search")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        self.log_info("Плагин VK Search инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
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
                delay = min(self.config["max_delay"], 
                           self.config["request_delay"] * (1.5 ** self.rate_limit_hits))
            else:
                # Если все хорошо, постепенно уменьшаем задержку
                delay = max(self.config["min_delay"], 
                           self.config["request_delay"] * 0.95)
            
            # Ограничиваем задержку в заданных пределах
            delay = max(self.config["min_delay"], 
                       min(self.config["max_delay"], delay))
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
            self.cache_stats["popular_queries"][cache_key] = \
                self.cache_stats["popular_queries"].get(cache_key, 0) + 1
        else:
            self.cache_stats["misses"] += 1
    
    def _analyze_query_patterns(self, query: str):
        """Анализирует паттерны запросов"""
        # Простой анализ: разбиваем запрос на слова
        words = query.lower().split()
        for word in words:
            if len(word) > 2:  # Игнорируем короткие слова
                self.cache_stats["query_patterns"][word] = \
                    self.cache_stats["query_patterns"].get(word, 0) + 1
    
    def _preload_popular_queries(self):
        """Предзагружает популярные запросы"""
        if not self.config["enable_caching"] or not self.cache_stats["preload_enabled"]:
            return
        
        self.log_info("🔄 Предзагрузка популярных запросов...")
        
        # Получаем топ-5 самых популярных запросов
        popular = sorted(
            self.cache_stats["popular_queries"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
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
        return hashlib.md5(key_data.encode()).hexdigest()

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
        top_queries = sorted(
            self.cache_stats["popular_queries"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Топ паттернов запросов
        top_patterns = sorted(
            self.cache_stats["query_patterns"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
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
                "requests_per_second": round(self.requests_made / max(1, avg_response_time), 2) if avg_response_time > 0 else 0
            },
            "intelligent_caching": {
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
                "total_cache_requests": total_cache_requests,
                "cache_hit_rate": round(cache_hit_rate, 3),
                "top_popular_queries": top_queries,
                "top_query_patterns": top_patterns,
                "cache_size_limit": self.cache_stats["cache_size_limit"],
                "preload_enabled": self.cache_stats["preload_enabled"]
            }
        }

    async def search_multiple_queries(self, queries: List[str], start_date, end_date, 
                                    exact_match: bool = True, minus_words: List[str] = None, batch_size: int = 3) -> List[Dict[str, Any]]:
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

    async def _search_single_query(self, session, query: str, start_date, end_date, 
                                  exact_match: bool, minus_words: List[str] = None) -> List[Dict[str, Any]]:
        """
        Поиск по одному запросу
        """
        params = {
            'q': f'"{query}"' if exact_match else query,
            'count': 200,
            'extended': 1,
            'access_token': self.config["access_token"],
            'v': self.config["api_version"]
        }
        
        # Добавляем параметры даты если они есть
        if start_date is not None:
            params['start_time'] = start_date
        if end_date is not None:
            params['end_time'] = end_date
            
        # Добавляем минус-слова
        if minus_words:
            for word in minus_words:
                if word.strip():
                    params['q'] += f' -{word.strip()}'
        
        # Выполняем поиск
        posts = await self._fetch_vk_batch(session, params, query)
        return posts

    async def _fetch_vk_batch(self, session, params, query, retry_count=3):
        """
        Оптимизированное получение одной партии результатов от VK API с интеллектуальным кэшированием
        """
        import time
        
        # Анализируем паттерны запроса
        self._analyze_query_patterns(query)
        
        # Проверяем кэш
        cache_key = self._get_cache_key(params)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            # Логируем cache hit только для небольших объемов
            if self.requests_made < 50:
                self.log_info(f"📋 Кэш-хит для запроса '{query}'")
            self._update_cache_stats(cache_key, True)
            return self.cache[cache_key]["data"]
        
        self._update_cache_stats(cache_key, False)
        start_time = time.time()
        
        for attempt in range(retry_count):
            try:
                await self._rate_limit()
                
                # Обновляем статистику использования токена
                token = params.get('access_token')
                if token:
                    self._update_token_usage(token)
                
                async with session.get('https://api.vk.com/method/newsfeed.search', params=params) as response:
                    self.requests_made += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'error' in data:
                            error_code = data['error'].get('error_code')
                            if error_code == 6:  # Too many requests per second
                                # Логируем rate limit только для первых случаев
                                if self.rate_limit_hits < 10:
                                    self.log_warning(f"Rate limit для запроса '{query}', ожидание...")
                                self.rate_limit_hits += 1
                                await asyncio.sleep(1)
                                continue
                            else:
                                # Логируем ошибки API только для небольших объемов
                                if self.requests_made < 100:
                                    self.log_error(f"Ошибка VK API для запроса '{query}': {data['error']}")
                                return []
                        
                        if 'response' in data:
                            items = data['response'].get('items', [])
                            
                            # Интеллектуальное кэширование
                            if self.config["enable_caching"]:
                                self.cache[cache_key] = {
                                    "data": items,
                                    "timestamp": time.time(),
                                    "query": query,
                                    "params": params
                                }
                                
                                # Умная очистка кэша при необходимости
                                self._smart_cache_cleanup()
                            
                            # Записываем время ответа
                            response_time = time.time() - start_time
                            self.response_times.append(response_time)
                            
                            # Сбрасываем счетчик rate limit если запрос успешен
                            if self.rate_limit_hits > 0:
                                self.rate_limit_hits = max(0, self.rate_limit_hits - 1)
                            
                            return items
                        else:
                            # Логируем неожиданные ответы только для небольших объемов
                            if self.requests_made < 50:
                                self.log_error(f"Неожиданный ответ VK API для запроса '{query}': {data}")
                            return []
                    else:
                        # Логируем HTTP ошибки только для небольших объемов
                        if self.requests_made < 50:
                            self.log_error(f"HTTP ошибка {response.status} для запроса '{query}'")
                        return []
                        
            except Exception as e:
                # Логируем ошибки только для небольших объемов
                if self.requests_made < 100:
                    self.log_error(f"Ошибка запроса для '{query}': {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1)
                    continue
                return []
        
        return []

    def _parse_datetime(self, datetime_str: str) -> int:
        """
        Парсинг даты в timestamp
        """
        try:
            dt = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
            return int(dt.timestamp())
        except ValueError as e:
            raise ValueError(f"Неверный формат даты: {datetime_str}") 

    async def mass_search_with_tokens(self, keyword_token_pairs: List[tuple], start_date, end_date, exact_match: bool = True, minus_words: List[str] = None, batch_size: int = None) -> List[Dict[str, Any]]:
        """
        Оптимизированный массовый асинхронный поиск с умной ротацией токенов
        """
        import time
        from datetime import datetime, timedelta, timezone
        
        # Используем конфигурационный batch_size если не передан
        if batch_size is None:
            batch_size = self.config["batch_size"]
        
        # Оптимизированное логирование для больших объемов
        total_queries = len(keyword_token_pairs)
        if total_queries > 10:
            self.log_info(f"🚀 Массовый поиск: {total_queries} запросов, batch_size={batch_size}")
        else:
            self.log_info(f"🚀 Оптимизированный массовый поиск для {len(keyword_token_pairs)} запросов")
            self.log_info(f"⚙️ Batch size: {batch_size}, Max batches: {self.config['max_batches']}")
        
        # Переводим start_date/end_date из МСК в UTC, если они строки
        def moscow_to_utc_timestamp(dt_str):
            moscow_tz = timezone(timedelta(hours=3))
            dt = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            dt = dt.replace(tzinfo=moscow_tz)
            dt_utc = dt.astimezone(timezone.utc)
            return int(dt_utc.timestamp())
        
        _start_ts = start_date
        _end_ts = end_date
        if isinstance(start_date, str):
            _start_ts = moscow_to_utc_timestamp(start_date)
        if isinstance(end_date, str):
            _end_ts = moscow_to_utc_timestamp(end_date)
        
        all_posts = []
        
        # Оптимизированные настройки HTTP клиента
        timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
        
        if self.config["use_connection_pooling"]:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
        else:
            connector = None
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Обрабатываем запросы батчами с улучшенной параллелизацией
            for i in range(0, len(keyword_token_pairs), batch_size):
                batch = keyword_token_pairs[i:i+batch_size]
                tasks = []
                
                # Логируем прогресс для больших объемов
                if total_queries > 20 and i % (batch_size * 5) == 0:
                    progress = (i / len(keyword_token_pairs)) * 100
                    self.log_info(f"📊 Прогресс: {progress:.1f}% ({i}/{total_queries} запросов)")
                
                for keyword, token in batch:
                    # Умная ротация токенов - выбираем токен с наименьшей нагрузкой
                    available_tokens = [t for _, t in keyword_token_pairs]
                    best_token = self._get_best_token(available_tokens)
                    
                    params = {
                        'q': f'"{keyword}"' if exact_match else keyword,
                        'count': 200,
                        'extended': 1,
                        'access_token': best_token,
                        'v': self.config["api_version"]
                    }
                    
                    if _start_ts is not None:
                        params['start_time'] = _start_ts
                    if _end_ts is not None:
                        params['end_time'] = _end_ts
                    
                    if minus_words:
                        for word in minus_words:
                            if word.strip():
                                params['q'] += f' -{word.strip()}'
                    
                    # Увеличиваем количество батчей для получения большего количества постов
                    max_batches = self.config["max_batches"]
                    offsets = [j * 200 for j in range(max_batches)]
                    
                    for offset in offsets:
                        params_copy = params.copy()
                        params_copy['offset'] = offset
                        tasks.append(self._fetch_vk_batch(session, params_copy, keyword))
                
                # Выполняем все задачи параллельно
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        all_posts.extend(result)
                    elif isinstance(result, Exception):
                        # Логируем только первые ошибки для больших объемов
                        if total_queries <= 20 or self.requests_made < 50:
                            self.log_error(f"Ошибка поиска: {result}")
                
                # Логируем статистику по батчам для больших объемов
                if total_queries > 20 and len(all_posts) > 0:
                    self.log_info(f"📈 Батч {i//batch_size + 1}: получено {len(all_posts)} постов")
        
        # Очищаем старый кэш
        self._cleanup_cache()
        
        # Финальная статистика
        if total_queries > 10:
            self.log_info(f"✅ Завершено: {len(all_posts)} постов, {self.requests_made} запросов")
        else:
            self.log_info(f"✅ Получено {len(all_posts)} постов от VK API")
            self.log_info(f"📊 Статистика: {self.requests_made} запросов, {len(self.response_times)} измерений времени")
        
        return all_posts
    
    def _cleanup_cache(self):
        """Очищает устаревшие записи кэша"""
        if not self.config["enable_caching"]:
            return
        
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if not self._is_cache_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self.log_info(f"🧹 Очищено {len(expired_keys)} устаревших записей кэша") 