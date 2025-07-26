"""
Плагин для фильтрации постов по тексту и ключевым словам
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import re

from ...core.event_system import EventType
from ..base_plugin import BasePlugin


class TextFilterPlugin(BasePlugin):
    """Плагин для фильтрации постов по тексту и ключевым словам"""
    
    def __init__(self):
        super().__init__()
        self.name = "TextFilterPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для фильтрации постов по тексту и ключевым словам с очисткой текста"
        
        # Конфигурация по умолчанию
        self.config = {
            "enable_text_cleaning": True,
            "enable_exact_match": True,
            "min_text_length": 3,
            "max_text_length": 10000,
            "case_sensitive": False,
            "enable_regex": False
        }
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина TextFilter")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        self.log_info("Плагин TextFilter инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина TextFilter")
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин TextFilter завершен")
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        min_length = self.config.get("min_text_length", 3)
        max_length = self.config.get("max_text_length", 10000)
        return min_length <= max_length
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        return {
            "enabled": self.is_enabled(),
            "config": self.get_config()
        }

    def _extract_post_text(self, post: Dict[str, Any]) -> str:
        """
        Извлекает текст из поста
        """
        text = post.get('text', '')
        if not text:
            text = post.get('message', '')
        if not text:
            text = post.get('content', '')
        
        return text

    def _clean_text(self, text: str) -> str:
        """
        Очищает текст от лишних символов
        """
        if not text:
            return ""
        
        # Удаляем эмодзи и лишние символы
        text = re.sub(r'[^\w\s]', ' ', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Приводим к нижнему регистру если не чувствителен к регистру
        if not self.config.get("case_sensitive", False):
            text = text.lower()
        
        return text

    def _check_keyword_match(self, text: str, keyword: str, exact_match: bool) -> bool:
        """
        Проверяет соответствие текста ключевому слову
        
        Args:
            text: Текст для проверки
            keyword: Ключевое слово
            exact_match: Точное совпадение (True) или частичное (False)
            
        Returns:
            True если есть совпадение, False иначе
        """
        if not text or not keyword:
            return False
        
        # Очищаем текст если включено
        if self.config.get("enable_text_cleaning", True):
            cleaned_text = self._clean_text(text)
        else:
            cleaned_text = text
        
        # Подготавливаем ключевое слово
        if not self.config.get("case_sensitive", False):
            keyword_lower = keyword.lower()
        else:
            keyword_lower = keyword
        
        if exact_match:
            # Точное совпадение (включая границы слов)
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            return bool(re.search(pattern, cleaned_text))
        else:
            # Частичное совпадение
            return keyword_lower in cleaned_text

    def filter_posts_by_keyword(self, posts: List[Dict[str, Any]], keyword: str, exact_match: bool = True) -> List[Dict[str, Any]]:
        """
        Фильтрация постов по одному ключевому слову
        
        Args:
            posts: Список постов для фильтрации
            keyword: Ключевое слово для поиска
            exact_match: Точное совпадение (True) или частичное (False)
            
        Returns:
            Список отфильтрованных постов
        """
        if not posts:
            return []
        
        filtered_posts = []
        
        for post in posts:
            text = self._extract_post_text(post)
            if self._check_keyword_match(text, keyword, exact_match):
                filtered_posts.append(post)
        
        self.log_info(f"Фильтрация по ключевому слову '{keyword}': {len(posts)} -> {len(filtered_posts)}")
        return filtered_posts

    def filter_posts_by_multiple_keywords(self, posts: List[Dict[str, Any]], keywords: List[str], 
                                        exact_match: bool = True, match_all: bool = False) -> List[Dict[str, Any]]:
        """
        Фильтрация постов по нескольким ключевым словам
        
        Args:
            posts: Список постов для фильтрации
            keywords: Список ключевых слов
            exact_match: Точное совпадение (True) или частичное (False)
            match_all: True - пост должен содержать все ключевые слова, False - хотя бы одно
            
        Returns:
            Список отфильтрованных постов
        """
        if not posts or not keywords:
            return []
        
        filtered_posts = []
        
        for post in posts:
            text = self._extract_post_text(post)
            matches = 0
            
            for keyword in keywords:
                if self._check_keyword_match(text, keyword, exact_match):
                    matches += 1
            
            # Проверяем условие соответствия
            if match_all:
                # Пост должен содержать все ключевые слова
                if matches == len(keywords):
                    filtered_posts.append(post)
            else:
                # Пост должен содержать хотя бы одно ключевое слово
                if matches > 0:
                    filtered_posts.append(post)
        
        self.log_info(f"Фильтрация по {len(keywords)} ключевым словам: {len(posts)} -> {len(filtered_posts)}")
        return filtered_posts

    async def filter_posts_parallel(self, posts: List[Dict[str, Any]], keywords: List[str], 
                                  exact_match: bool = True, match_all: bool = False) -> List[Dict[str, Any]]:
        """
        Параллельная фильтрация постов по ключевым словам
        
        Args:
            posts: Список постов для фильтрации
            keywords: Список ключевых слов
            exact_match: Точное совпадение (True) или частичное (False)
            match_all: True - пост должен содержать все ключевые слова, False - хотя бы одно
            
        Returns:
            Список отфильтрованных постов
        """
        if not posts or not keywords:
            return []
        
        self.log_info(f"🚀 Параллельная фильтрация {len(posts)} постов по {len(keywords)} ключам")
        
        # Создаем задачи для параллельной обработки
        tasks = []
        chunk_size = max(1, len(posts) // 10)
        
        for i in range(0, len(posts), chunk_size):
            chunk = posts[i:i + chunk_size]
            task = self._process_chunk_parallel(chunk, keywords, exact_match, match_all)
            tasks.append(task)
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks)
        
        # Объединяем результаты
        filtered_posts = []
        for result in results:
            filtered_posts.extend(result)
        
        self.log_info(f"✅ Параллельная фильтрация завершена: {len(posts)} -> {len(filtered_posts)}")
        return filtered_posts

    async def _process_chunk_parallel(self, chunk: List[Dict[str, Any]], keywords: List[str], 
                                    exact_match: bool, match_all: bool) -> List[Dict[str, Any]]:
        """
        Параллельная обработка чанка постов
        """
        filtered_chunk = []
        
        # Создаем задачи для каждого поста в чанке
        post_tasks = []
        for post in chunk:
            task = self._process_single_post_parallel(post, keywords, exact_match, match_all)
            post_tasks.append(task)
        
        # Выполняем обработку постов параллельно
        results = await asyncio.gather(*post_tasks, return_exceptions=True)
        
        # Собираем результаты
        for result in results:
            if isinstance(result, dict) and result:
                filtered_chunk.append(result)
            elif isinstance(result, Exception):
                self.log_error(f"Ошибка обработки поста: {result}")
        
        return filtered_chunk

    async def _process_single_post_parallel(self, post: Dict[str, Any], keywords: List[str], 
                                          exact_match: bool, match_all: bool) -> Optional[Dict[str, Any]]:
        """
        Параллельная обработка одного поста
        """
        try:
            text = self._extract_post_text(post)
            if not text:
                return None
            
            matches = 0
            for keyword in keywords:
                if self._check_keyword_match(text, keyword, exact_match):
                    matches += 1
            
            # Проверяем условие соответствия
            if match_all:
                # Пост должен содержать все ключевые слова
                if matches == len(keywords):
                    return post
            else:
                # Пост должен содержать хотя бы одно ключевое слово
                if matches > 0:
                    return post
            
            return None
            
        except Exception as e:
            self.log_error(f"Ошибка обработки поста: {e}")
            return None

    def get_keyword_statistics(self, posts: List[Dict[str, Any]], keywords: List[str], 
                             exact_match: bool = True) -> Dict[str, Any]:
        """
        Возвращает статистику по ключевым словам
        
        Args:
            posts: Список постов для анализа
            keywords: Список ключевых слов
            
        Returns:
            Словарь со статистикой
        """
        if not posts or not keywords:
            return {
                "total_posts": 0,
                "keywords": {},
                "total_matches": 0
            }
        
        keyword_stats = {}
        total_matches = 0
        
        for keyword in keywords:
            matches = 0
            for post in posts:
                text = self._extract_post_text(post)
                if self._check_keyword_match(text, keyword, exact_match):
                    matches += 1
            
            keyword_stats[keyword] = matches
            total_matches += matches
        
        return {
            "total_posts": len(posts),
            "keywords": keyword_stats,
            "total_matches": total_matches
        } 