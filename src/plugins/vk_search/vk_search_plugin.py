"""
Плагин для поиска данных ВКонтакте
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from loguru import logger

from ...core.event_system import EventType
from ..base_plugin import BasePlugin

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
            "request_delay": 0.5,
            "max_requests_per_second": 3,
            "timeout": 30,
            "access_token": None
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._last_request_time = 0
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина VK Search")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        # Создаем сессию для HTTP запросов
        timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
        self.session = aiohttp.ClientSession(timeout=timeout)
        
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
        required_keys = ["access_token"]
        
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False
        
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["access_token"]
    
    async def search_posts(self, query: str, count: int = 100, 
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
            
            async with self.session.get(url, params=params) as response:
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
    
    async def get_group_posts(self, group_id: int, count: int = 100) -> List[Dict[str, Any]]:
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
            
            async with self.session.get(url, params=params) as response:
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
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
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
            
            async with self.session.get(url, params=params) as response:
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
        """
        Асинхронный массовый поиск по нескольким запросам с фильтрацией дублей и обработкой постов
        """
        self.log_info(f"🚀 Начинаем асинхронный поиск для {len(queries)} запросов")
        all_posts = []
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]
            tasks = [self._search_single_query(q, start_date, end_date, exact_match, minus_words) for q in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_posts.extend(result)
                elif isinstance(result, Exception):
                    self.log_error(f"Ошибка поиска: {result}")
        unique_posts = self.filter_unique_posts(all_posts)
        num_duplicates = len(all_posts) - len(unique_posts)
        self.log_info(f"✅ Найдено {len(unique_posts)} уникальных постов для всех запросов (до фильтрации: {len(all_posts)}, дублей: {num_duplicates})")
        return unique_posts

    async def _search_single_query(self, query: str, start_date, end_date, 
                                  exact_match: bool, minus_words: List[str] = None) -> List[Dict[str, Any]]:
        """Асинхронный поиск по одному запросу с обработкой и нормализацией постов"""
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
            posts = []
            offset = 0
            max_requests = 25
            for request_num in range(max_requests):
                params['offset'] = offset
                async with self.session.get("https://api.vk.com/method/newsfeed.search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'error' in data:
                            self.log_error(f"API ошибка: {data['error']}")
                            break
                        items = data.get('response', {}).get('items', [])
                        if not items:
                            break
                        for item in items:
                            post = self._process_post(item, query)
                            if post:
                                posts.append(post)
                        offset += len(items)
                        await asyncio.sleep(self.config.get("request_delay", 0.5))
                    else:
                        self.log_error(f"HTTP ошибка: {response.status}")
                        break
            self.log_info(f"📊 Найдено {len(posts)} постов для '{query[:30]}...'")
            return posts
        except Exception as e:
            self.log_error(f"Ошибка поиска '{query[:30]}...': {e}")
            return []

    def _process_post(self, item: Dict, query: str) -> Optional[Dict]:
        """Обработка и нормализация поста под экспорт/анализ"""
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
        """Фильтрация уникальных постов по (owner_id, post_id)"""
        seen = set()
        unique = []
        for post in posts:
            key = (post.get('owner_id'), post.get('post_id'))
            if key not in seen:
                seen.add(key)
                unique.append(post)
        return unique

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