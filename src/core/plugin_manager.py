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
                    
                    logger.info(f"Плагин загружен: {plugin_name}")
                    break
            else:
                logger.warning(f"Класс плагина не найден в {plugin_name}")
                
        except ImportError as e:
            logger.error(f"Ошибка загрузки плагина {plugin_name}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке плагина {plugin_name}: {e}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Возвращает плагин по имени"""
        return self.plugins.get(name)
    
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