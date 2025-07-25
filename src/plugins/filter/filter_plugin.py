"""
Плагин для локальной фильтрации данных по ключевым фразам
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from ...core.event_system import EventType
from ..base_plugin import BasePlugin


class FilterPlugin(BasePlugin):
    """Плагин для локальной фильтрации постов по ключевым фразам"""
    
    def __init__(self):
        super().__init__()
        self.name = "FilterPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для локальной фильтрации постов по ключевым фразам с очисткой текста"
        
        # Конфигурация по умолчанию
        self.config = {
            "enable_text_cleaning": True,
            "enable_exact_match": True,
            "enable_unique_filtering": True,
            "min_text_length": 3,
            "max_text_length": 10000
        }
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Filter")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        self.log_info("Плагин Filter инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Filter")
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Filter завершен")
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        return {
            "enabled": self.is_enabled(),
            "config": self.get_config()
        }

    def filter_unique_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрация уникальных постов по (owner_id, post_id)
        
        Args:
            posts: Список постов для фильтрации
            
        Returns:
            Список уникальных постов
        """
        if not posts:
            return []
        
        seen = set()
        unique = []
        
        for post in posts:
            owner_id = post.get('owner_id')
            post_id = post.get('id') or post.get('post_id')
            
            if owner_id is not None and post_id is not None:
                key = (owner_id, post_id)
                if key not in seen:
                    seen.add(key)
                    unique.append(post)
        
        self.log_info(f"Фильтрация уникальных постов: {len(posts)} -> {len(unique)}")
        return unique

    def filter_posts_by_keyword(self, posts: List[Dict[str, Any]], keyword: str, exact_match: bool = True) -> List[Dict[str, Any]]:
        """
        Фильтрация постов по ключевому слову (без очистки текста)
        
        Args:
            posts: Список постов для фильтрации
            keyword: Ключевое слово для поиска
            exact_match: Точное совпадение (True) или частичное (False)
            
        Returns:
            Список отфильтрованных постов
        """
        if not posts or not keyword:
            return []
        
        filtered = []
        keyword_lower = keyword.lower()
        
        for post in posts:
            text = str(post.get('text', '') or post.get('post_text', ''))
            text_lower = text.lower()
            
            if exact_match:
                # Точное вхождение
                if keyword_lower in text_lower:
                    filtered.append(post)
            else:
                # Частичное вхождение (по словам)
                words = text_lower.split()
                if keyword_lower in words:
                    filtered.append(post)
        
        self.log_info(f"Фильтрация по ключу '{keyword}': {len(posts)} -> {len(filtered)}")
        return filtered

    def filter_posts_by_keyword_with_text_cleaning(self, posts: List[Dict[str, Any]], keyword: str, exact_match: bool = True) -> List[Dict[str, Any]]:
        """
        Фильтрация постов по ключевому слову с очисткой текста
        
        Args:
            posts: Список постов для фильтрации
            keyword: Ключевое слово для поиска
            exact_match: Точное совпадение (True) или частичное (False)
            
        Returns:
            Список отфильтрованных постов
        """
        if not posts or not keyword:
            return []
        
        try:
            # Импортируем TextProcessingPlugin для очистки текста
            from ..text_processing.text_processing_plugin import TextProcessingPlugin
            text_plugin = TextProcessingPlugin()
            text_plugin.initialize()
            
            # Очищаем ключевое слово
            keyword_clean = text_plugin.clean_text_completely(keyword)
            
            filtered = []
            for post in posts:
                # Получаем текст поста
                text = str(post.get('text', '') or post.get('post_text', ''))
                
                # Очищаем текст поста
                text_clean = text_plugin.clean_text_completely(text)
                
                # Проверяем вхождение ключа
                if keyword_clean in text_clean:
                    filtered.append(post)
            
            text_plugin.shutdown()
            
            self.log_info(f"Фильтрация с очисткой текста по ключу '{keyword}': {len(posts)} -> {len(filtered)}")
            return filtered
            
        except Exception as e:
            self.log_error(f"Ошибка фильтрации с очисткой текста: {e}")
            # Fallback к простой фильтрации без очистки
            return self.filter_posts_by_keyword(posts, keyword, exact_match)

    def filter_posts_by_multiple_keywords(self, posts: List[Dict[str, Any]], keywords: List[str], 
                                        exact_match: bool = True, use_text_cleaning: bool = True) -> List[Dict[str, Any]]:
        """
        Фильтрация постов по нескольким ключевым словам
        
        Args:
            posts: Список постов для фильтрации
            keywords: Список ключевых слов
            exact_match: Точное совпадение (True) или частичное (False)
            use_text_cleaning: Использовать очистку текста
            
        Returns:
            Список отфильтрованных постов
        """
        if not posts or not keywords:
            return []
        
        filtered = []
        
        for post in posts:
            text = str(post.get('text', '') or post.get('post_text', ''))
            
            for keyword in keywords:
                if use_text_cleaning:
                    # Используем фильтрацию с очисткой текста
                    temp_filtered = self.filter_posts_by_keyword_with_text_cleaning([post], keyword, exact_match)
                else:
                    # Используем простую фильтрацию
                    temp_filtered = self.filter_posts_by_keyword([post], keyword, exact_match)
                
                if temp_filtered:
                    filtered.append(post)
                    break  # Нашли совпадение, переходим к следующему посту
        
        self.log_info(f"Фильтрация по {len(keywords)} ключам: {len(posts)} -> {len(filtered)}")
        return filtered

    def filter_posts_comprehensive(self, posts: List[Dict[str, Any]], keywords: List[str] = None,
                                 exact_match: bool = True, use_text_cleaning: bool = True,
                                 remove_duplicates: bool = True) -> List[Dict[str, Any]]:
        """
        Комплексная фильтрация постов по ключевым фразам
        
        Args:
            posts: Список постов для фильтрации
            keywords: Список ключевых слов (опционально)
            exact_match: Точное совпадение (True) или частичное (False)
            use_text_cleaning: Использовать очистку текста
            remove_duplicates: Удалять дубликаты
            
        Returns:
            Список отфильтрованных постов
        """
        if not posts:
            return []
        
        filtered = posts.copy()
        
        # 1. Фильтрация по ключевым словам
        if keywords:
            if len(keywords) == 1:
                # Один ключ
                if use_text_cleaning:
                    filtered = self.filter_posts_by_keyword_with_text_cleaning(filtered, keywords[0], exact_match)
                else:
                    filtered = self.filter_posts_by_keyword(filtered, keywords[0], exact_match)
            else:
                # Несколько ключей
                filtered = self.filter_posts_by_multiple_keywords(filtered, keywords, exact_match, use_text_cleaning)
        
        # 2. Удаление дубликатов
        if remove_duplicates:
            filtered = self.filter_unique_posts(filtered)
        
        self.log_info(f"Комплексная фильтрация: {len(posts)} -> {len(filtered)}")
        return filtered 

    async def filter_posts_comprehensive_parallel(self, posts: List[Dict[str, Any]], keywords: List[str], 
                                               exact_match: bool = True) -> List[Dict[str, Any]]:
        """
        Комплексная фильтрация с параллельной обработкой
        """
        if not posts:
            return []
        
        self.log_info(f"🚀 Параллельная фильтрация {len(posts)} постов по {len(keywords)} ключам")
        
        # Создаем задачи для параллельной обработки
        tasks = []
        chunk_size = max(1, len(posts) // 10)  # Разбиваем на чанки для параллельной обработки
        
        for i in range(0, len(posts), chunk_size):
            chunk = posts[i:i + chunk_size]
            task = self._process_chunk_parallel(chunk, keywords, exact_match)
            tasks.append(task)
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks)
        
        # Объединяем результаты
        filtered_posts = []
        for result in results:
            filtered_posts.extend(result)
        
        # Удаляем дубликаты
        unique_posts = self.filter_unique_posts(filtered_posts)
        
        self.log_info(f"✅ Параллельная фильтрация завершена: {len(posts)} -> {len(unique_posts)}")
        return unique_posts
    
    async def _process_chunk_parallel(self, chunk: List[Dict[str, Any]], keywords: List[str], 
                                    exact_match: bool) -> List[Dict[str, Any]]:
        """
        Параллельная обработка чанка постов
        """
        filtered_chunk = []
        
        # Создаем задачи для каждого поста в чанке
        post_tasks = []
        for post in chunk:
            task = self._process_single_post_parallel(post, keywords, exact_match)
            post_tasks.append(task)
        
        # Выполняем обработку постов параллельно
        results = await asyncio.gather(*post_tasks, return_exceptions=True)
        
        # Собираем результаты
        for result in results:
            if isinstance(result, dict) and result:  # Если пост прошел фильтрацию
                filtered_chunk.append(result)
            elif isinstance(result, Exception):
                self.log_error(f"Ошибка обработки поста: {result}")
        
        return filtered_chunk
    
    async def _process_single_post_parallel(self, post: Dict[str, Any], keywords: List[str], 
                                          exact_match: bool) -> Optional[Dict[str, Any]]:
        """
        Параллельная обработка одного поста
        """
        try:
            # Получаем текст поста
            text = self._extract_post_text(post)
            if not text:
                return None
            
            # Очищаем текст
            cleaned_text = await self._clean_text_async(text)
            
            # Проверяем соответствие ключевым словам
            for keyword in keywords:
                if self._check_keyword_match(cleaned_text, keyword, exact_match):
                    return post
            
            return None
            
        except Exception as e:
            self.log_error(f"Ошибка обработки поста: {e}")
            return None
    
    async def _clean_text_async(self, text: str) -> str:
        """
        Асинхронная очистка текста
        """
        # Получаем TextProcessingPlugin
        plugin_manager = self.get_plugin_manager()
        if plugin_manager:
            text_plugin = plugin_manager.get_plugin('text_processing')
            if text_plugin:
                return text_plugin.clean_text_completely(text)
        
        # Fallback к базовой очистке
        return self._basic_text_clean(text)
    
    def _basic_text_clean(self, text: str) -> str:
        """
        Базовая очистка текста (fallback)
        """
        import re
        # Удаляем эмодзи
        text = re.sub(r'[^\w\s]', ' ', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower() 