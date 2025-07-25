"""
Плагин для поиска данных ВКонтакте
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from loguru import logger

from ...core.event_system import EventType
from ..base_plugin import BasePlugin
from ..text_processing.text_processing_plugin import TextProcessingPlugin

import time
from datetime import datetime


class VKSearchPlugin(BasePlugin):
    """Плагин для поиска данных ВКонтакте"""
    
    def __init__(self):
        super().__init__()
        self.name = "VKSearchPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для поиска и анализа данных ВКонтакте"
        
        # Конфигурация по умолчанию
        self.config = {
            "api_version": "5.131",
            "request_delay": 0.1,  # Было 0.5
            "max_requests_per_second": 10,  # Было 3
            "timeout": 30,
            "access_token": None
        }
        
        self._request_count = 0
        self._last_request_time = 0
    
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
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин VK Search завершен")
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = ["access_token"]
        
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False
        
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["access_token"]
    
    async def search_posts(self, session, query: str, count: int = 100, 
                          owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Поиск постов по запросу"""
        if not self.is_enabled():
            raise RuntimeError("Плагин отключен")
        
        self.emit_event(EventType.SEARCH_STARTED, {
            "query": query,
            "count": count,
            "owner_id": owner_id
        })
        
        try:
            await self._rate_limit()
            
            params = {
                "q": query,
                "count": count,
                "access_token": self.config["access_token"],
                "v": self.config["api_version"]
            }
            
            if owner_id:
                params["owner_id"] = owner_id
            
            url = "https://api.vk.com/method/newsfeed.search"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "error" in data:
                        self.log_error(f"Ошибка VK API: {data['error']}")
                        return []
                    
                    posts = data.get("response", {}).get("items", [])
                    
                    self.emit_event(EventType.SEARCH_COMPLETED, {
                        "query": query,
                        "found_count": len(posts)
                    })
                    
                    return posts
                else:
                    self.log_error(f"HTTP ошибка: {response.status}")
                    return []
                    
        except Exception as e:
            self.log_error(f"Ошибка поиска постов: {e}")
            self.emit_event(EventType.ERROR_OCCURRED, {"error": str(e)})
            return []
    
    async def get_group_posts(self, session, group_id: int, count: int = 100) -> List[Dict[str, Any]]:
        """Получение постов группы"""
        if not self.is_enabled():
            raise RuntimeError("Плагин отключен")
        
        try:
            await self._rate_limit()
            
            params = {
                "owner_id": -group_id,  # Отрицательный ID для групп
                "count": count,
                "access_token": self.config["access_token"],
                "v": self.config["api_version"]
            }
            
            url = "https://api.vk.com/method/wall.get"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "error" in data:
                        self.log_error(f"Ошибка VK API: {data['error']}")
                        return []
                    
                    posts = data.get("response", {}).get("items", [])
                    return posts
                else:
                    self.log_error(f"HTTP ошибка: {response.status}")
                    return []
                    
        except Exception as e:
            self.log_error(f"Ошибка получения постов группы: {e}")
            return []
    
    async def get_user_info(self, session, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        if not self.is_enabled():
            raise RuntimeError("Плагин отключен")
        
        try:
            await self._rate_limit()
            
            params = {
                "user_ids": user_id,
                "fields": "id,first_name,last_name,screen_name,photo_100",
                "access_token": self.config["access_token"],
                "v": self.config["api_version"]
            }
            
            url = "https://api.vk.com/method/users.get"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "error" in data:
                        self.log_error(f"Ошибка VK API: {data['error']}")
                        return None
                    
                    users = data.get("response", [])
                    return users[0] if users else None
                else:
                    self.log_error(f"HTTP ошибка: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_error(f"Ошибка получения информации о пользователе: {e}")
            return None
    
    async def _rate_limit(self) -> None:
        """Ограничение частоты запросов"""
        import time
        
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        min_interval = 1.0 / self.config["max_requests_per_second"]
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self._last_request_time = time.time()
        self._request_count += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        return {
            "requests_made": self._request_count,
            "enabled": self.is_enabled(),
            "config": self.get_config()
        } 

    async def search_multiple_queries(self, queries: List[str], start_date, end_date, 
                                    exact_match: bool = True, minus_words: List[str] = None, batch_size: int = 3) -> List[Dict[str, Any]]:
        import time
        t0 = time.time()
        self.log_info(f"🚀 Начинаем асинхронный поиск для {len(queries)} запросов")
        all_posts = []
        timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for i in range(0, len(queries), batch_size):
                batch = queries[i:i+batch_size]
                tasks = [self._search_single_query(session, q, start_date, end_date, exact_match, minus_words) for q in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, list):
                        all_posts.extend(result)
                    elif isinstance(result, Exception):
                        self.log_error(f"Ошибка поиска: {result}")
        t1 = time.time()
        self.log_info(f"⏱️ Время на запросы: {t1-t0:.2f} сек")
        t2 = time.time()
        unique_posts = self.filter_unique_posts(all_posts)
        t3 = time.time()
        num_duplicates = len(all_posts) - len(unique_posts)
        self.log_info(f"✅ Найдено {len(unique_posts)} уникальных постов для всех запросов (до фильтрации: {len(all_posts)}, дублей: {num_duplicates})")
        self.log_info(f"⏱️ Время на фильтрацию: {t3-t2:.2f} сек")
        return unique_posts

    async def _search_single_query(self, session, query: str, start_date, end_date, 
                                  exact_match: bool, minus_words: List[str] = None) -> List[Dict[str, Any]]:
        await self._rate_limit()
        try:
            self.log_info(f"🔍 Поиск: '{query[:50]}...'")
            # Конвертируем даты
            if isinstance(start_date, int) and isinstance(end_date, int):
                start_timestamp = start_date
                end_timestamp = end_date
            else:
                start_timestamp = self._parse_datetime(f"{start_date} 00:00")
                end_timestamp = self._parse_datetime(f"{end_date} 23:59")
            # Формируем поисковый запрос
            search_query = f'"{query}"' if exact_match else query
            if minus_words:
                for word in minus_words:
                    if word.strip():
                        search_query += f' -{word.strip()}'
            params = {
                'q': search_query,
                'count': 200,
                'start_time': start_timestamp,
                'end_time': end_timestamp,
                'extended': 1,
                'access_token': self.config["access_token"],
                'v': self.config["api_version"]
            }
            # Параллельная загрузка по offset
            max_batches = 5
            offsets = [i * 200 for i in range(max_batches)]
            tasks = []
            for offset in offsets:
                params_copy = params.copy()
                params_copy['offset'] = offset
                tasks.append(self._fetch_vk_batch(session, params_copy, query))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            posts = []
            for result in results:
                if isinstance(result, list):
                    posts.extend(result)
                elif isinstance(result, Exception):
                    self.log_error(f"Ошибка поиска по offset: {result}")
            self.log_info(f"📊 Найдено {len(posts)} постов для '{query[:30]}...' (до фильтрации дублей)")
            # Фильтрация дублей по (owner_id, post_id)
            unique_posts = self.filter_unique_posts(posts)
            self.log_info(f"📊 Уникальных постов для '{query[:30]}...': {len(unique_posts)}")
            return unique_posts
        except Exception as e:
            self.log_error(f"Ошибка поиска '{query[:30]}...': {e}")
            return []

    async def _fetch_vk_batch(self, session, params, query, retry_count=3):
        for attempt in range(retry_count):
            try:
                async with session.get("https://api.vk.com/method/newsfeed.search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "error" in data:
                            err = data["error"]
                            if err.get("error_code") == 6:
                                self.log_error(f"VK API rate limit (error 6): {err}. Попытка {attempt+1}/{retry_count}")
                                await asyncio.sleep(2)  # Пауза перед повтором
                                continue
                            self.log_error(f"Ошибка VK API: {err}")
                            return []
                        posts = data.get("response", {}).get("items", [])
                        return posts
                    else:
                        self.log_error(f"HTTP ошибка: {response.status}")
                        return []
            except Exception as e:
                self.log_error(f"Ошибка поиска по offset: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2)
            return []

    def _process_post(self, item: Dict, query: str) -> Optional[Dict]:
        if not isinstance(item, dict):
            print("VKSearchPlugin: item is not a dict!", type(item), item)
            self.log_error(f"VKSearchPlugin: item is not a dict! {type(item)} {item}")
            return None
        try:
            owner_id = item.get('owner_id')
            post_id = item.get('id')
            post = {
                'keyword': query,
                'post_text': item.get('text', ''),
                'author': self._get_author_name(item),
                'date': datetime.fromtimestamp(item.get('date', 0)).strftime("%d.%m.%Y"),
                'time': datetime.fromtimestamp(item.get('date', 0)).strftime("%H:%M"),
                'timestamp': item.get('date', 0),
                'likes': item.get('likes', {}).get('count', 0),
                'comments': item.get('comments', {}).get('count', 0),
                'shares': item.get('reposts', {}).get('count', 0),
                'post_id': item.get('id'),
                'owner_id': item.get('owner_id'),
                'attachments': self._get_attachments(item),
                "Ссылка": f"https://vk.com/wall{owner_id}_{post_id}"
            }
            return post
        except Exception as e:
            self.log_error(f"Ошибка обработки поста: {e}")
            return None

    def filter_unique_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Фильтрует уникальные посты по (owner_id, id)"""
        seen = set()
        unique_posts = []
        for post in posts:
            key = (post.get('owner_id'), post.get('id'))
            if key not in seen:
                seen.add(key)
                unique_posts.append(post)
        return unique_posts

    def _get_author_name(self, item: Dict) -> str:
        try:
            owner_id = item.get('owner_id', 0)
            if owner_id < 0:
                return f"Группа {abs(owner_id)}"
            else:
                return f"Пользователь {owner_id}"
        except:
            return "Неизвестно"

    def _get_attachments(self, item: Dict) -> str:
        attachments = item.get('attachments', [])
        if not attachments:
            return "Без вложений"
        types = []
        for att in attachments:
            att_type = att.get('type', '')
            if att_type:
                types.append(att_type)
        return ", ".join(types) if types else "Без вложений"

    def _parse_datetime(self, datetime_str: str) -> int:
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
        text_plugin = TextProcessingPlugin()
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
                        # Локальная фильтрация по ключу (точное вхождение с очисткой текста)
                        if exact_match:
                            filtered = []
                            for post in result:
                                text = str(post.get('text', '') or post.get('post_text', ''))
                                text_clean = text_plugin.clean_text_completely(text)
                                keyword_clean = text_plugin.clean_text_completely(keyword)
                                if keyword_clean in text_clean:
                                    filtered.append(post)
                            all_posts.extend(filtered)
                        else:
                            all_posts.extend(result)
                    elif isinstance(result, Exception):
                        self.log_error(f"Ошибка поиска: {result}")
        # Фильтрация уникальных постов
        unique_posts = self.filter_unique_posts(all_posts)
        num_duplicates = len(all_posts) - len(unique_posts)
        self.log_info(f"✅ Найдено {len(unique_posts)} уникальных постов для всех запросов (до фильтрации: {len(all_posts)}, дублей: {num_duplicates})")
        return unique_posts 