"""
Центральный плагин для обработки публикаций
Объединяет фильтрацию и дедупликацию
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin


class PostProcessorPlugin(BasePlugin):
    """Центральный плагин для обработки публикаций"""
    
    def __init__(self):
        super().__init__()
        self.name = "PostProcessorPlugin"
        self.version = "1.0.0"
        self.description = "Центральный плагин для обработки публикаций (фильтрация + дедупликация)"
        
        # Конфигурация по умолчанию
        self.config = {
            "enable_filtering": True,
            "enable_deduplication": True,
            "filter_method": "keywords",  # keywords, exact_match
            "deduplication_method": "link_hash",  # link_hash, text, content_hash
            "processing_order": ["deduplication", "filtering"],  # Порядок обработки
            "batch_size": 1000,
            "enable_logging": True
        }
        
        # Связи с другими плагинами
        self.filter_plugin = None
        self.deduplication_plugin = None
        self.database_plugin = None
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина PostProcessor")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        self.log_info("Плагин PostProcessor инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина PostProcessor")
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин PostProcessor завершен")
    
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
            "config": self.get_config(),
            "plugins_connected": {
                "filter": self.filter_plugin is not None,
                "deduplication": self.deduplication_plugin is not None,
                "database": self.database_plugin is not None
            }
        }
    
    def set_filter_plugin(self, filter_plugin):
        """Устанавливает связь с плагином фильтрации"""
        self.filter_plugin = filter_plugin
        self.log_info("FilterPlugin подключен к PostProcessorPlugin")
    
    def set_deduplication_plugin(self, deduplication_plugin):
        """Устанавливает связь с плагином дедупликации"""
        self.deduplication_plugin = deduplication_plugin
        self.log_info("DeduplicationPlugin подключен к PostProcessorPlugin")
    
    def set_database_plugin(self, database_plugin):
        """Устанавливает связь с плагином базы данных"""
        self.database_plugin = database_plugin
        self.log_info("DatabasePlugin подключен к PostProcessorPlugin")
    
    def process_posts(self, posts: List[Dict[str, Any]], 
                     keywords: List[str] = None, 
                     exact_match: bool = True,
                     remove_duplicates: bool = True,
                     processing_order: List[str] = None) -> Dict[str, Any]:
        """
        Централизованная обработка публикаций
        
        Args:
            posts: Список публикаций для обработки
            keywords: Ключевые слова для фильтрации
            exact_match: Точное совпадение для фильтрации
            remove_duplicates: Удалять ли дубликаты
            processing_order: Порядок обработки ['deduplication', 'filtering']
            
        Returns:
            Словарь с результатами обработки
        """
        if not posts:
            return {
                "original_count": 0,
                "final_count": 0,
                "filtered_count": 0,
                "duplicates_removed": 0,
                "processing_time": 0,
                "final_posts": []
            }
        
        start_time = datetime.now()
        original_count = len(posts)
        current_posts = posts.copy()
        
        # Определяем порядок обработки
        if processing_order is None:
            processing_order = self.config.get("processing_order", ["deduplication", "filtering"])
        
        self.log_info(f"🚀 Начало обработки {original_count} публикаций")
        self.log_info(f"📋 Порядок обработки: {processing_order}")
        
        # Обработка дубликатов
        duplicates_removed = 0
        if remove_duplicates and "deduplication" in processing_order:
            if self.deduplication_plugin:
                before_count = len(current_posts)
                current_posts = self.deduplication_plugin.remove_duplicates_by_link_hash(current_posts)
                duplicates_removed = before_count - len(current_posts)
                self.log_info(f"🗑️ Удалено {duplicates_removed} дубликатов")
            else:
                self.log_warning("DeduplicationPlugin не подключен")
        
        # Фильтрация по ключевым словам
        filtered_count = 0
        if keywords and "filtering" in processing_order:
            if self.filter_plugin:
                before_count = len(current_posts)
                current_posts = self.filter_plugin.filter_posts_by_multiple_keywords(
                    current_posts, keywords, exact_match
                )
                filtered_count = before_count - len(current_posts)
                self.log_info(f"🔍 Отфильтровано {filtered_count} публикаций")
            else:
                self.log_warning("FilterPlugin не подключен")
        
        # Вычисляем время обработки
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "original_count": original_count,
            "final_count": len(current_posts),
            "filtered_count": filtered_count,
            "duplicates_removed": duplicates_removed,
            "processing_time": processing_time,
            "final_posts": current_posts,
            "processing_order": processing_order
        }
        
        self.log_info(f"✅ Обработка завершена: {original_count} -> {len(current_posts)} "
                     f"(дубликатов: {duplicates_removed}, отфильтровано: {filtered_count})")
        
        return result
    
    def process_posts_from_database(self, task_id: int,
                                  keywords: List[str] = None,
                                  exact_match: bool = True,
                                  remove_duplicates: bool = True) -> Dict[str, Any]:
        """
        Обработка публикаций из базы данных
        
        Args:
            task_id: ID задачи
            keywords: Ключевые слова для фильтрации
            exact_match: Точное совпадение
            remove_duplicates: Удалять ли дубликаты
            
        Returns:
            Словарь с результатами обработки
        """
        if not self.database_plugin:
            self.log_error("DatabasePlugin не подключен")
            return {}
        
        try:
            # Получаем публикации из БД
            posts = self.database_plugin.get_task_posts(task_id)
            
            if not posts:
                self.log_info(f"Задача {task_id} не содержит публикаций")
                return {"task_id": task_id, "posts_count": 0}
            
            # Обрабатываем публикации
            result = self.process_posts(posts, keywords, exact_match, remove_duplicates)
            result["task_id"] = task_id
            
            return result
            
        except Exception as e:
            self.log_error(f"Ошибка обработки публикаций из БД: {e}")
            return {}
    
    def clean_database_task(self, task_id: int,
                          keywords: List[str] = None,
                          exact_match: bool = True) -> Dict[str, int]:
        """
        Очистка задачи в базе данных (удаление дубликатов + несоответствующих)
        
        Args:
            task_id: ID задачи
            keywords: Ключевые слова для проверки соответствия
            exact_match: Точное совпадение
            
        Returns:
            Словарь с результатами очистки
        """
        if not self.database_plugin:
            self.log_error("DatabasePlugin не подключен")
            return {}
        
        results = {
            "duplicates_removed": 0,
            "invalid_posts_removed": 0,
            "total_cleaned": 0
        }
        
        try:
            # Удаляем дубликаты
            if self.deduplication_plugin:
                results["duplicates_removed"] = self.deduplication_plugin.clean_duplicates_from_database(task_id)
            
            # Удаляем несоответствующие публикации
            if keywords and self.filter_plugin:
                results["invalid_posts_removed"] = self.filter_plugin.clean_by_parsing_parameters(
                    task_id, keywords, exact_match
                )
            
            results["total_cleaned"] = results["duplicates_removed"] + results["invalid_posts_removed"]
            
            self.log_info(f"🧹 Очистка задачи {task_id}: {results}")
            return results
            
        except Exception as e:
            self.log_error(f"Ошибка очистки задачи: {e}")
            return results
    
    def get_processing_statistics(self, task_id: int = None) -> Dict[str, Any]:
        """
        Получает статистику обработки
        
        Args:
            task_id: ID задачи (None для всех задач)
            
        Returns:
            Словарь со статистикой
        """
        stats = {
            "filter_plugin_connected": self.filter_plugin is not None,
            "deduplication_plugin_connected": self.deduplication_plugin is not None,
            "database_plugin_connected": self.database_plugin is not None
        }
        
        # Статистика дубликатов
        if self.deduplication_plugin:
            stats["duplicates"] = self.deduplication_plugin.get_database_duplicate_statistics(task_id)
        
        # Статистика фильтрации
        if self.filter_plugin:
            stats["filtering"] = self.filter_plugin.get_statistics()
        
        return stats 