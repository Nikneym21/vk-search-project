"""
Главный модуль приложения VK Search Project
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any
import tkinter as tk

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gui.main_interface import MainInterface
from src.core.logger_utils import setup_logger
from loguru import logger


class VKSearchApplication:
    """Главный класс приложения"""
    
    def __init__(self):
        self.main_window = None
        
    def initialize(self) -> bool:
        """Инициализация приложения"""
        try:
            logger.info("Инициализация VK Search Application")
            
            # Настройка логирования
            # setup_logger(log_file="logs/app.log", level="DEBUG")
            
            logger.info("Приложение успешно инициализировано")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации приложения: {e}")
            return False
    
    def run_gui(self):
        """Запуск графического интерфейса"""
        try:
            logger.info("Запуск графического интерфейса")
            
            # Создаем главное окно
            self.main_window = tk.Tk()
            
            # Создаем главный интерфейс (PluginManager создается внутри MainInterface)
            main_interface = MainInterface(self.main_window)
            
            # Настраиваем обработчик закрытия
            self.main_window.protocol("WM_DELETE_WINDOW", main_interface.on_closing)
            
            logger.info("Графический интерфейс запущен")
            
            # Запускаем главный цикл
            self.main_window.mainloop()
            
        except Exception as e:
            logger.error(f"Ошибка запуска GUI: {e}")
            raise
    
    def shutdown(self):
        """Завершение работы приложения"""
        try:
            logger.info("Завершение работы приложения")
            
            if self.main_window:
                self.main_window.quit()
            
            logger.info("Приложение завершено")
            
        except Exception as e:
            logger.error(f"Ошибка завершения приложения: {e}")


def main():
    """Главная функция приложения"""
    try:
        # Создаем приложение
        app = VKSearchApplication()
        
        # Инициализируем
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


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 