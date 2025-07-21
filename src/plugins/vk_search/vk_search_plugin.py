"""
Плагин для поиска данных ВКонтакте
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from loguru import logger

from ...core.event_system import EventType
from ..base_plugin import BasePlugin


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