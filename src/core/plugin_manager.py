"""
Менеджер плагинов для управления модулями системы
"""

import os
import importlib
import inspect
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

from ..plugins.base_plugin import BasePlugin


class PluginManager:
    """Менеджер для загрузки и управления плагинами"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
    def load_plugins(self, plugins_dir: str = "src/plugins") -> None:
        """Загружает все доступные плагины из указанной директории"""
        plugins_path = Path(plugins_dir)
        
        if not plugins_path.exists():
            logger.warning(f"Директория плагинов не найдена: {plugins_dir}")
            return
            
        for plugin_dir in plugins_path.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                self._load_plugin(plugin_dir)
        # Явная загрузка LoggerPlugin
        try:
            from src.plugins.logger.logger_plugin import LoggerPlugin
            logger_plugin = LoggerPlugin()
            logger_plugin.initialize()
            self.plugins['logger'] = logger_plugin
            logger.info("LoggerPlugin загружен и инициализирован")
        except Exception as e:
            logger.error(f"LoggerPlugin не загружен: {e}")
    
    def _load_plugin(self, plugin_dir: Path) -> None:
        """Загружает отдельный плагин"""
        plugin_name = plugin_dir.name
        
        try:
            # Импортируем модуль плагина
            module_path = f"src.plugins.{plugin_name}.{plugin_name}_plugin"
            module = importlib.import_module(module_path)
            
            # Ищем класс плагина
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj != BasePlugin):
                    
                    # Создаем экземпляр плагина
                    plugin_instance = obj()
                    self.plugins[plugin_name] = plugin_instance
                    
                    logger.info(f"Плагин загружен: {plugin_name} -> {type(plugin_instance).__name__}")
                    break
            else:
                logger.warning(f"Класс плагина не найден в {plugin_name}")
                
        except ImportError as e:
            logger.error(f"Ошибка загрузки плагина {plugin_name}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке плагина {plugin_name}: {e}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Получает плагин по имени"""
        return self.plugins.get(name)
    
    def get_logger(self):
        """Получает логгер для плагинов"""
        from loguru import logger
        return logger
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Возвращает все загруженные плагины"""
        return self.plugins.copy()
    
    def execute_plugin_method(self, plugin_name: str, method_name: str, *args, **kwargs) -> Any:
        """Выполняет метод плагина"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Плагин {plugin_name} не найден")
        
        if not hasattr(plugin, method_name):
            raise AttributeError(f"Метод {method_name} не найден в плагине {plugin_name}")
        
        method = getattr(plugin, method_name)
        return method(*args, **kwargs)
    
    def initialize_plugins(self) -> None:
        """Инициализирует все загруженные плагины"""
        for name, plugin in self.plugins.items():
            try:
                plugin.initialize()
                logger.info(f"Плагин инициализирован: {name}")
            except Exception as e:
                logger.error(f"Ошибка инициализации плагина {name}: {e}")
    
    def shutdown_plugins(self) -> None:
        """Завершает работу всех плагинов"""
        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
                logger.info(f"Плагин завершен: {name}")
            except Exception as e:
                logger.error(f"Ошибка завершения плагина {name}: {e}")
    
    async def coordinate_search_and_filter(self, keywords: List[str], start_date: str, end_date: str, 
                                        exact_match: bool = True, minus_words: List[str] = None) -> List[Dict[str, Any]]:
        """
        Координация поиска и фильтрации с параллельной обработкой
        """
        import time
        from datetime import datetime
        
        start_time = time.time()
        logger = self.get_logger()
        
        try:
            logger.info(f"🚀 Координация поиска и фильтрации для {len(keywords)} ключевых слов")
            
            # Получаем VKSearchPlugin
            vk_plugin = self.get_plugin('vk_search')
            if not vk_plugin:
                raise ValueError("VKSearchPlugin не найден")
            
            # Получаем токен из TokenManagerPlugin
            token_manager = self.get_plugin('token_manager')
            if not token_manager:
                raise ValueError("TokenManagerPlugin не найден")
            
            # Получаем VK токен
            token = token_manager.get_token("vk")
            if not token:
                # Пытаемся загрузить из файла
                try:
                    with open("config/vk_token.txt", 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#') and not line.startswith('//'):
                                token = line
                                break
                except Exception as e:
                    logger.error(f"Ошибка загрузки токена из файла: {e}")
            
            if not token:
                raise ValueError("Токен VK не найден ни в TokenManager, ни в файле")
            
            # Устанавливаем токен в VKSearchPlugin
            vk_plugin.config["access_token"] = token
            logger.info("Токен VK установлен в VKSearchPlugin")
            
            # Обрабатываем даты - если передана только дата, добавляем время
            if isinstance(start_date, str) and len(start_date.split()) == 1:
                start_date = f"{start_date} 00:00"
            if isinstance(end_date, str) and len(end_date.split()) == 1:
                end_date = f"{end_date} 23:59"
            
            # Получаем все доступные токены для ротации
            all_tokens = token_manager.list_vk_tokens()
            if not all_tokens:
                # Если нет токенов в менеджере, используем токен из файла
                all_tokens = [token]
            
            logger.info(f"Доступно токенов для ротации: {len(all_tokens)}")
            
            # Создаем пары (ключевое слово, токен) с ротацией токенов
            keyword_token_pairs = []
            for i, keyword in enumerate(keywords):
                token_index = i % len(all_tokens)
                selected_token = all_tokens[token_index]
                keyword_token_pairs.append((keyword, selected_token))
            
            logger.info(f"Создано {len(keyword_token_pairs)} пар (ключевое слово, токен) с ротацией")
            
            # Выполняем поиск с параллельной фильтрацией
            raw_posts = await vk_plugin.mass_search_with_tokens(
                keyword_token_pairs, start_date, end_date, exact_match, minus_words
            )
            
            logger.info(f"📊 Получено {len(raw_posts)} сырых постов от VK API")
            
            # Параллельная фильтрация
            filter_plugin = self.get_plugin('filter')
            if not filter_plugin:
                raise ValueError("FilterPlugin не найден")
            
            # Используем новую параллельную фильтрацию
            filtered_posts = await filter_plugin.filter_posts_comprehensive_parallel(
                raw_posts, keywords, exact_match
            )
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Отфильтровано {len(filtered_posts)} постов за {execution_time:.2f} сек")
            
            return filtered_posts
            
        except Exception as e:
            logger.error(f"Ошибка координации поиска: {e}")
            return []
    
    def _format_search_results(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Форматирует результаты поиска для отображения"""
        from datetime import datetime
        
        formatted_results = []
        for post in posts:
            # Получаем информацию о посте
            owner_id = post.get('owner_id', 0)
            post_id = post.get('id', 0)
            text = post.get('text', '')
            date = post.get('date', 0)
            
            # Форматируем дату
            if date:
                dt = datetime.fromtimestamp(date)
                formatted_date = dt.strftime("%H:%M %d.%m.%Y")
            else:
                formatted_date = ""
            
            # Получаем статистику
            likes = post.get('likes', {})
            comments = post.get('comments', {})
            reposts = post.get('reposts', {})
            views = post.get('views', {})
            
            # Извлекаем значения
            likes_count = likes.get('count', 0) if isinstance(likes, dict) else likes
            comments_count = comments.get('count', 0) if isinstance(comments, dict) else comments
            reposts_count = reposts.get('count', 0) if isinstance(reposts, dict) else reposts
            views_count = views.get('count', 0) if isinstance(views, dict) else views
            
            # Формируем ссылку
            if owner_id < 0:
                author_link = f"https://vk.com/club{abs(owner_id)}"
            else:
                author_link = f"https://vk.com/id{owner_id}"
            
            formatted_post = {
                "link": f"https://vk.com/wall{owner_id}_{post_id}",
                "text": text,
                "type": "Пост",
                "author": post.get('author_name', ''),
                "author_link": author_link,
                "date": formatted_date,
                "likes": likes_count,
                "comments": comments_count,
                "reposts": reposts_count,
                "views": views_count
            }
            formatted_results.append(formatted_post)
        
        return formatted_results 