"""
Модуль плагинов для VK Search Project
"""

# Импорты плагинов
from .vk_search.vk_search_plugin import VKSearchPlugin
from .data_manager.data_manager_plugin import DataManagerPlugin
from .database.database_plugin import DatabasePlugin
from .google_sheets.google_sheets_plugin import GoogleSheetsPlugin
from .text_processing.text_processing_plugin import TextProcessingPlugin
from .link_comparator.link_comparator_plugin import LinkComparatorPlugin
from .settings_manager.settings_manager_plugin import SettingsManagerPlugin
from .token_manager.token_manager_plugin import TokenManagerPlugin

__all__ = [
    'VKSearchPlugin',
    'DataManagerPlugin', 
    'DatabasePlugin',
    'GoogleSheetsPlugin',
    'TextProcessingPlugin',
    'LinkComparatorPlugin',
    'SettingsManagerPlugin',
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
    'TokenManagerPlugin': TokenManagerPlugin,
    'SettingsManagerPlugin': SettingsManagerPlugin
} 