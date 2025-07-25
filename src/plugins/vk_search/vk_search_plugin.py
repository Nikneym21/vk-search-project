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
        
        # Конфигурация по умолчанию
        self.config = {
            "access_token": None,
            "api_version": "5.131",
            "request_delay": 0.3,
            "max_requests_per_second": 3,
            "timeout": 30,
            "max_retries": 3
        }
        
        # Статистика
        self.requests_made = 0
        self.session = None
    
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
        """Rate limiting для VK API"""
        delay = self.config["request_delay"]
        if delay > 0:
            await asyncio.sleep(delay)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        return {
            "requests_made": self.requests_made,
            "enabled": self.is_enabled(),
            "config": self.get_config()
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
        Получение одной партии результатов от VK API
        """
        for attempt in range(retry_count):
            try:
                await self._rate_limit()
                
                async with session.get('https://api.vk.com/method/newsfeed.search', params=params) as response:
                    self.requests_made += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'error' in data:
                            error_code = data['error'].get('error_code')
                            if error_code == 6:  # Too many requests per second
                                self.log_warning(f"Rate limit для запроса '{query}', ожидание...")
                                await asyncio.sleep(1)
                                continue
                            else:
                                self.log_error(f"Ошибка VK API для запроса '{query}': {data['error']}")
                                return []
                        
                        if 'response' in data:
                            items = data['response'].get('items', [])
                            return items
                        else:
                            self.log_error(f"Неожиданный ответ VK API для запроса '{query}': {data}")
                            return []
                    else:
                        self.log_error(f"HTTP ошибка {response.status} для запроса '{query}'")
                        return []
                        
            except Exception as e:
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

    async def mass_search_with_tokens(self, keyword_token_pairs: List[tuple], start_date, end_date, exact_match: bool = True, minus_words: List[str] = None, batch_size: int = 3) -> List[Dict[str, Any]]:
        """
        Массовый асинхронный поиск: для каждого ключевого слова используется свой токен.
        keyword_token_pairs: список кортежей (keyword, token)
        start_date/end_date: могут быть либо int (timestamp UTC), либо str в формате '%d.%m.%Y %H:%M' (МСК)
        """
        import time
        from datetime import datetime, timedelta, timezone
        
        self.log_info(f"🚀 Массовый асинхронный поиск для {len(keyword_token_pairs)} запросов с разными токенами")
        
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
        timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for i in range(0, len(keyword_token_pairs), batch_size):
                batch = keyword_token_pairs[i:i+batch_size]
                tasks = []
                
                for keyword, token in batch:
                    params = {
                        'q': f'"{keyword}"' if exact_match else keyword,
                        'count': 200,
                        'extended': 1,
                        'access_token': token,
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
                    
                    max_batches = 5
                    offsets = [j * 200 for j in range(max_batches)]
                    
                    for offset in offsets:
                        params_copy = params.copy()
                        params_copy['offset'] = offset
                        tasks.append(self._fetch_vk_batch(session, params_copy, keyword))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        all_posts.extend(result)
                    elif isinstance(result, Exception):
                        self.log_error(f"Ошибка поиска: {result}")
        
        self.log_info(f"✅ Получено {len(all_posts)} постов от VK API для всех запросов")
        return all_posts 