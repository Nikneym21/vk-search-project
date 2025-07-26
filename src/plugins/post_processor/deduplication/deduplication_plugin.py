"""
Плагин для удаления дубликатов постов
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin


class DeduplicationPlugin(BasePlugin):
    """Плагин для удаления дубликатов постов"""
    
    def __init__(self):
        super().__init__()
        self.name = "DeduplicationPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для удаления дубликатов постов по различным критериям"
        
        # Конфигурация по умолчанию
        self.config = {
            "deduplication_method": "link_hash",  # link_hash, text, content_hash
            "enable_logging": True,
            "batch_size": 1000
        }
        
        # Связи с другими плагинами
        self.database_plugin = None
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Deduplication")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        self.log_info("Плагин Deduplication инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Deduplication")
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Deduplication завершен")
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        method = self.config.get("deduplication_method")
        valid_methods = ["link_hash", "text", "content_hash"]
        return method in valid_methods
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["deduplication_method"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        return {
            "enabled": self.is_enabled(),
            "config": self.get_config(),
            "method": self.config.get("deduplication_method")
        }

    def remove_duplicates_by_link_hash(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Удаляет дубликаты постов по хешу ссылки
        
        Args:
            posts: Список постов для дедупликации
            
        Returns:
            Список уникальных постов
        """
        if not posts:
            return []
        
        seen = set()
        unique = []
        duplicates_count = 0
        
        for post in posts:
            link = post.get('link')
            if link:
                import hashlib
                link_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                
                if link_hash not in seen:
                    seen.add(link_hash)
                    unique.append(post)
                else:
                    duplicates_count += 1
        
        self.log_info(f"Дедупликация по link_hash: {len(posts)} -> {len(unique)} (удалено {duplicates_count})")
        return unique

    def remove_duplicates_by_text(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Удаляет дубликаты постов по тексту
        
        Args:
            posts: Список постов для дедупликации
            
        Returns:
            Список уникальных постов
        """
        if not posts:
            return []
        
        seen = set()
        unique = []
        duplicates_count = 0
        
        for post in posts:
            text = self._extract_post_text(post)
            if text:
                text_hash = hash(text.lower().strip())
                if text_hash not in seen:
                    seen.add(text_hash)
                    unique.append(post)
                else:
                    duplicates_count += 1
        
        self.log_info(f"Дедупликация по тексту: {len(posts)} -> {len(unique)} (удалено {duplicates_count})")
        return unique

    def remove_duplicates_by_content_hash(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Удаляет дубликаты постов по хешу контента (комбинация текста и метаданных)
        
        Args:
            posts: Список постов для дедупликации
            
        Returns:
            Список уникальных постов
        """
        if not posts:
            return []
        
        seen = set()
        unique = []
        duplicates_count = 0
        
        for post in posts:
            # Создаем хеш на основе текста и основных метаданных
            text = self._extract_post_text(post)
            owner_id = post.get('owner_id', 0)
            date = post.get('date', 0)
            
            content_string = f"{text}_{owner_id}_{date}"
            content_hash = hash(content_string.lower().strip())
            
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(post)
            else:
                duplicates_count += 1
        
        self.log_info(f"Дедупликация по content_hash: {len(posts)} -> {len(unique)} (удалено {duplicates_count})")
        return unique

    def remove_duplicates(self, posts: List[Dict[str, Any]], method: str = None) -> List[Dict[str, Any]]:
        """
        Удаляет дубликаты постов используя указанный метод
        
        Args:
            posts: Список постов для дедупликации
            method: Метод дедупликации (post_id, text, content_hash)
            
        Returns:
            Список уникальных постов
        """
        if not posts:
            return []
        
        if method is None:
            method = self.config.get("deduplication_method", "post_id")
        
        self.log_info(f"Запуск дедупликации {len(posts)} постов методом: {method}")
        
        if method == "post_id":
            return self.remove_duplicates_by_post_id(posts)
        elif method == "text":
            return self.remove_duplicates_by_text(posts)
        elif method == "content_hash":
            return self.remove_duplicates_by_content_hash(posts)
        else:
            self.log_error(f"Неизвестный метод дедупликации: {method}")
            return posts

    async def remove_duplicates_parallel(self, posts: List[Dict[str, Any]], method: str = None) -> List[Dict[str, Any]]:
        """
        Асинхронная дедупликация постов с параллельной обработкой
        
        Args:
            posts: Список постов для дедупликации
            method: Метод дедупликации
            
        Returns:
            Список уникальных постов
        """
        if not posts:
            return []
        
        if method is None:
            method = self.config.get("deduplication_method", "post_id")
        
        self.log_info(f"🚀 Параллельная дедупликация {len(posts)} постов методом: {method}")
        
        # Для небольших списков используем синхронную обработку
        if len(posts) < 1000:
            return self.remove_duplicates(posts, method)
        
        # Для больших списков используем параллельную обработку
        batch_size = self.config.get("batch_size", 1000)
        tasks = []
        
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            task = self._process_batch_parallel(batch, method)
            tasks.append(task)
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks)
        
        # Объединяем результаты
        all_unique_posts = []
        for result in results:
            all_unique_posts.extend(result)
        
        # Финальная дедупликация объединенных результатов
        final_unique = self.remove_duplicates(all_unique_posts, method)
        
        self.log_info(f"✅ Параллельная дедупликация завершена: {len(posts)} -> {len(final_unique)}")
        return final_unique

    async def _process_batch_parallel(self, batch: List[Dict[str, Any]], method: str) -> List[Dict[str, Any]]:
        """
        Параллельная обработка батча постов
        """
        try:
            return self.remove_duplicates(batch, method)
        except Exception as e:
            self.log_error(f"Ошибка обработки батча: {e}")
            return batch

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

    def get_duplicate_statistics(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Возвращает статистику дубликатов в списке постов
        
        Args:
            posts: Список постов для анализа
            
        Returns:
            Словарь со статистикой
        """
        if not posts:
            return {
                "total": 0,
                "unique_by_link_hash": 0,
                "unique_by_text": 0,
                "unique_by_content_hash": 0,
                "duplicates_by_link_hash": 0,
                "duplicates_by_text": 0,
                "duplicates_by_content_hash": 0
            }
        
        total = len(posts)
        unique_by_link_hash = len(self.remove_duplicates_by_link_hash(posts))
        unique_by_text = len(self.remove_duplicates_by_text(posts))
        unique_by_content_hash = len(self.remove_duplicates_by_content_hash(posts))
        
        return {
            "total": total,
            "unique_by_link_hash": unique_by_link_hash,
            "unique_by_text": unique_by_text,
            "unique_by_content_hash": unique_by_content_hash,
            "duplicates_by_link_hash": total - unique_by_link_hash,
            "duplicates_by_text": total - unique_by_text,
            "duplicates_by_content_hash": total - unique_by_content_hash
        }
    
    def set_database_plugin(self, database_plugin):
        """Устанавливает связь с плагином базы данных"""
        self.database_plugin = database_plugin
        self.log_info("DatabasePlugin подключен к DeduplicationPlugin")
    
    def clean_duplicates_from_database(self, task_id: int = None) -> int:
        """
        Очистка дубликатов из базы данных по ссылкам
        
        Args:
            task_id: ID задачи (None для всех задач)
            
        Returns:
            Количество удаленных дубликатов
        """
        if not self.database_plugin:
            self.log_error("DatabasePlugin не подключен")
            return 0
        
        try:
            # Находим дубликаты
            duplicates = self.database_plugin.find_duplicates(task_id)
            
            if not duplicates:
                self.log_info("Дубликаты не найдены")
                return 0
            
            # Удаляем дубликаты (оставляем только первый)
            removed_count = 0
            cursor = self.database_plugin.connection.cursor()
            
            for duplicate_group in duplicates:
                if len(duplicate_group) > 1:
                    # Оставляем первый пост, удаляем остальные
                    for duplicate in duplicate_group[1:]:
                        cursor.execute('DELETE FROM posts WHERE id = ?', (duplicate['id'],))
                        removed_count += 1
            
            self.database_plugin.connection.commit()
            
            # Обновляем статистику задачи
            if task_id:
                self.database_plugin._update_task_statistics(task_id)
            
            self.log_info(f"Удалено {removed_count} дубликатов из БД")
            return removed_count
            
        except Exception as e:
            self.log_error(f"Ошибка очистки дубликатов из БД: {e}")
            return 0
    
    def get_database_duplicate_statistics(self, task_id: int = None) -> Dict[str, Any]:
        """
        Получает статистику дубликатов из базы данных
        
        Args:
            task_id: ID задачи (None для всех задач)
            
        Returns:
            Словарь со статистикой
        """
        if not self.database_plugin:
            self.log_error("DatabasePlugin не подключен")
            return {}
        
        try:
            duplicates = self.database_plugin.find_duplicates(task_id)
            
            total_duplicates = 0
            duplicate_groups = 0
            
            for duplicate_group in duplicates:
                if len(duplicate_group) > 1:
                    duplicate_groups += 1
                    total_duplicates += len(duplicate_group) - 1  # -1 потому что один оставляем
            
            return {
                "duplicate_groups": duplicate_groups,
                "total_duplicates": total_duplicates,
                "method": "link_hash"
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики дубликатов: {e}")
            return {} 