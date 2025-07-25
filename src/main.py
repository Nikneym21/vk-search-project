"""
Главный модуль приложения VK Search Project
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.plugin_manager import PluginManager
from src.core.event_system import EventType, event_system
from src.core.config_manager import ConfigManager
from src.gui.main_interface import MainInterface
from src.core.logger_utils import setup_logger
from loguru import logger


class VKSearchApplication:
    """Главный класс приложения"""
    
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.config_manager = ConfigManager()
        self.main_window = None
        
    def initialize(self) -> bool:
        """Инициализация приложения"""
        try:
            logger.info("Инициализация VK Search Application")
            
            # Настройка логирования
            # setup_logger(log_file="logs/app.log", level="DEBUG")
            
            # Загрузка конфигурации
            if not self.config_manager.load_config():
                logger.error("Не удалось загрузить конфигурацию")
                return False
            
            # Инициализация менеджера плагинов
            if not self.plugin_manager.initialize():
                logger.error("Не удалось инициализировать менеджер плагинов")
                return False
            
            # Загрузка всех плагинов
            self._load_all_plugins()
            
            # Настройка обработчиков событий
            self._setup_event_handlers()
            
            logger.info("Приложение успешно инициализировано")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации приложения: {e}")
            return False
    
    def _load_all_plugins(self):
        """Загружает все доступные плагины"""
        try:
            # Список всех плагинов для загрузки
            plugins_to_load = [
                'VKSearchPlugin',
                'DataManagerPlugin', 
                'DatabasePlugin',
                'GoogleSheetsPlugin',
                'TextProcessingPlugin',
                'LinkComparatorPlugin',
                'TokenManagerPlugin'
            ]
            
            for plugin_name in plugins_to_load:
                try:
                    # Получаем конфигурацию плагина
                    plugin_config = self.config_manager.get_plugin_config(plugin_name)
                    
                    if plugin_config and plugin_config.get('enabled', True):
                        # Загружаем плагин
                        if self.plugin_manager.load_plugin(plugin_name, plugin_config.get('config', {})):
                            logger.info(f"Плагин {plugin_name} успешно загружен")
                        else:
                            logger.warning(f"Не удалось загрузить плагин {plugin_name}")
                    else:
                        logger.info(f"Плагин {plugin_name} отключен в конфигурации")
                        
                except Exception as e:
                    logger.error(f"Ошибка загрузки плагина {plugin_name}: {e}")
            
            logger.info(f"Загружено плагинов: {len(self.plugin_manager.get_loaded_plugins())}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки плагинов: {e}")
    
    def _setup_event_handlers(self):
        """Настраивает обработчики событий"""
        try:
            # Обработчик события загрузки плагина
            event_system.subscribe(EventType.PLUGIN_LOADED, self._on_plugin_loaded)
            
            # Обработчик события выгрузки плагина
            event_system.subscribe(EventType.PLUGIN_UNLOADED, self._on_plugin_unloaded)
            
            # Обработчик события обновления данных
            event_system.subscribe(EventType.DATA_UPDATED, self._on_data_updated)
            
            # Обработчик события ошибки
            event_system.subscribe(EventType.ERROR_OCCURRED, self._on_error_occurred)
            
            logger.info("Обработчики событий настроены")
            
        except Exception as e:
            logger.error(f"Ошибка настройки обработчиков событий: {e}")
    
    def _on_plugin_loaded(self, event):
        """Обработчик события загрузки плагина"""
        logger.info(f"Плагин загружен: {event.data.get('plugin_name', 'Unknown')}")
    
    def _on_plugin_unloaded(self, event):
        """Обработчик события выгрузки плагина"""
        logger.info(f"Плагин выгружен: {event.data.get('plugin_name', 'Unknown')}")
    
    def _on_data_updated(self, event):
        """Обработчик события обновления данных"""
        logger.debug(f"Данные обновлены: {event.data}")
    
    def _on_error_occurred(self, event):
        """Обработчик события ошибки"""
        logger.error(f"Произошла ошибка: {event.data}")
    
    def run_gui(self):
        """Запускает графический интерфейс"""
        try:
            logger.info("Запуск графического интерфейса")
            
            # Создаем главное окно
            self.main_window = MainInterface(self.plugin_manager, self.config_manager)
            
            # Запускаем GUI
            self.main_window.run()
            
        except Exception as e:
            logger.error(f"Ошибка запуска GUI: {e}")
    
    def shutdown(self):
        """Завершение работы приложения"""
        try:
            logger.info("Завершение работы приложения")
            
            # Закрываем GUI
            if self.main_window:
                self.main_window.destroy()
            
            # Выгружаем все плагины
            self.plugin_manager.shutdown()
            
            logger.info("Приложение завершено")
            
        except Exception as e:
            logger.error(f"Ошибка завершения приложения: {e}")


def main():
    """Главная функция приложения"""
    try:
        # Настройка логгера
        setup_logger(log_file="logs/app.log", level="DEBUG")
        # Создаем экземпляр приложения
        app = VKSearchApplication()
        
        # Инициализируем приложение
        if not app.initialize():
            logger.error("Не удалось инициализировать приложение")
            return 1
        
        # Запускаем GUI
        app.run_gui()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Приложение прервано пользователем")
        return 0
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1
    finally:
        # Завершаем работу приложения
        if 'app' in locals():
            app.shutdown()


if __name__ == "__main__":
    sys.exit(main()) 