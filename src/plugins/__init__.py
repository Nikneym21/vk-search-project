"""
Модуль плагинов для VK Search Project
"""

# Импорты плагинов
from .vk_search.vk_search_plugin import VKSearchPlugin
from .post_processor.filter.filter_plugin import FilterPlugin
from .post_processor.text_processing.text_processing_plugin import TextProcessingPlugin
from .post_processor.deduplication.deduplication_plugin import DeduplicationPlugin
from .post_processor.post_processor_plugin import PostProcessorPlugin
from .token_manager.token_manager_plugin import TokenManagerPlugin
from .database.database_plugin import DatabasePlugin
from .google_sheets.google_sheets_plugin import GoogleSheetsPlugin
from .link_comparator.link_comparator_plugin import LinkComparatorPlugin
from .settings_manager.settings_manager_plugin import SettingsManagerPlugin
from .logger.logger_plugin import LoggerPlugin
from .monitoring.monitoring_plugin import MonitoringPlugin

# Список всех доступных плагинов
__all__ = [
    'VKSearchPlugin',
    'FilterPlugin',
    'TextProcessingPlugin',
    'DeduplicationPlugin',
    'PostProcessorPlugin',
    'TokenManagerPlugin',
    'DatabasePlugin',
    'GoogleSheetsPlugin',
    'LinkComparatorPlugin',
    'SettingsManagerPlugin',
    'LoggerPlugin',
    'MonitoringPlugin'
]

# Словарь классов плагинов для автоматической загрузки
PLUGIN_CLASSES = {
    'vk_search': VKSearchPlugin,
    'filter': FilterPlugin,
    'text_processing': TextProcessingPlugin,
    'deduplication': DeduplicationPlugin,
    'post_processor': PostProcessorPlugin,
    'token_manager': TokenManagerPlugin,
    'database': DatabasePlugin,
    'google_sheets': GoogleSheetsPlugin,
    'link_comparator': LinkComparatorPlugin,
    'settings_manager': SettingsManagerPlugin,
    'logger': LoggerPlugin,
    'monitoring': MonitoringPlugin
}
