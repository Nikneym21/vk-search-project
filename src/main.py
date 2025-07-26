"""
Главный модуль приложения VK Search Project
"""

import sys
import tkinter as tk
from pathlib import Path

from loguru import logger

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импорты модулей проекта после установки пути
from src.gui.main_interface import MainInterface  # noqa: E402


class VKSearchApplication:
    """Главный класс приложения"""

    def __init__(self):
        self.main_window = None

    def initialize(self) -> bool:
        """Инициализация приложения"""
        try:
            # Создаем папку для логов если её нет
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)

            # Настройка логирования в файл
            logger.add("logs/app.log",
                      level="DEBUG",
                      format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}",
                      rotation="10 MB",
                      retention="7 days",
                      compression="zip")

            logger.info("Инициализация VK Search Application")
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
