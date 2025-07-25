"""
Ядро системы VK Search Project
"""

from .plugin_manager import PluginManager
from .config_manager import ConfigManager
from .event_system import EventSystem
from .logger_utils import setup_logger, log_function_call

__all__ = ['PluginManager', 'ConfigManager', 'EventSystem'] 