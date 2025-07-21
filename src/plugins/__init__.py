"""
Модуль плагинов для VK Search Project
"""

# Импорты всех плагинов
from .base_plugin import BasePlugin

# Плагины данных
from .data_manager.data_manager_plugin import DataManagerPlugin
from .database.database_plugin import DatabasePlugin

# Плагины интеграции
from .google_sheets.google_sheets_plugin import GoogleSheetsPlugin
from .vk_search.vk_search_plugin import VKSearchPlugin

# Плагины обработки
from .text_processing.text_processing_plugin import TextProcessingPlugin
from .link_comparator.link_comparator_plugin import LinkComparatorPlugin

# Плагины управления
from .token_manager.token_manager_plugin import TokenManagerPlugin

# Список всех доступных плагинов
__all__ = [
    'BasePlugin',
    'DataManagerPlugin',
    'DatabasePlugin', 
    'GoogleSheetsPlugin',
    'VKSearchPlugin',
    'TextProcessingPlugin',
    'LinkComparatorPlugin',
    'TokenManagerPlugin'
]

# Словарь плагинов для автоматической загрузки
PLUGIN_CLASSES = {
    'DataManagerPlugin': DataManagerPlugin,
    'DatabasePlugin': DatabasePlugin,
    'GoogleSheetsPlugin': GoogleSheetsPlugin,
    'VKSearchPlugin': VKSearchPlugin,
    'TextProcessingPlugin': TextProcessingPlugin,
    'LinkComparatorPlugin': LinkComparatorPlugin,
    'TokenManagerPlugin': TokenManagerPlugin
} 