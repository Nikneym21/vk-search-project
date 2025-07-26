"""
Плагин для управления настройками приложения
Обеспечивает автосохранение и загрузку настроек интерфейса и парсера
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin


class SettingsManagerPlugin(BasePlugin):
    """Плагин для управления настройками приложения"""

    def __init__(self):
        super().__init__()
        self.name = "SettingsManager"
        self.version = "1.0.0"
        self.description = "Плагин для управления настройками интерфейса и парсера"

        # Пути к файлам настроек
        self.settings_dir = "data"
        self.window_settings_file = "window_settings.json"
        self.interface_settings_file = "interface_settings.json"
        self.parser_settings_file = "parser_settings.json"
        self.sheets_settings_file = "sheets_settings.json"

        # Создаем папку для настроек если её нет
        os.makedirs(self.settings_dir, exist_ok=True)

        # Кэш настроек
        self._window_settings: Dict[str, Any] = {}
        self._interface_settings: Dict[str, Any] = {}
        self._parser_settings: Dict[str, Any] = {}
        self._sheets_settings: Dict[str, Any] = {}

    def initialize(self) -> None:
        """Инициализация плагина"""
        try:
            # Загружаем существующие настройки
            self._load_all_settings()
            self.log_info("Плагин настроек инициализирован")
            self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
        except Exception as e:
            self.log_error(f"Ошибка инициализации: {str(e)}")
            raise

    def shutdown(self) -> None:
        """Завершение работы плагина"""
        try:
            # Сохраняем все настройки перед выключением
            self._save_all_settings()
            self.log_info("Плагин настроек завершил работу")
            self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        except Exception as e:
            self.log_error(f"Ошибка завершения работы: {str(e)}")

    def save_window_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки окна"""
        try:
            settings["last_saved"] = datetime.now().isoformat()
            self._window_settings.update(settings)

            file_path = os.path.join(self.settings_dir, self.window_settings_file)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._window_settings, f, indent=2, ensure_ascii=False)

            self.log_info("Настройки окна сохранены")
            self.emit_event(EventType.DATA_UPDATED, {"type": "window_settings", "data": settings})
            return True
        except Exception as e:
            self.log_error(f"Ошибка сохранения настроек окна: {str(e)}")
            return False

    def load_window_settings(self) -> Dict[str, Any]:
        """Загружает настройки окна"""
        try:
            file_path = os.path.join(self.settings_dir, self.window_settings_file)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self._window_settings = json.load(f)
                self.log_info("Настройки окна загружены")
            else:
                # Возвращаем настройки по умолчанию
                self._window_settings = {"window_width": 1200, "window_height": 800, "window_x": 100, "window_y": 100}
        except Exception as e:
            self.log_error(f"Ошибка загрузки настроек окна: {str(e)}")
            self._window_settings = {}

        return self._window_settings.copy()

    def save_interface_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки интерфейса"""
        try:
            settings["last_saved"] = datetime.now().isoformat()
            self._interface_settings.update(settings)

            file_path = os.path.join(self.settings_dir, self.interface_settings_file)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._interface_settings, f, indent=2, ensure_ascii=False)

            self.log_info("Настройки интерфейса сохранены")
            self.emit_event(EventType.DATA_UPDATED, {"type": "interface_settings", "data": settings})
            return True
        except Exception as e:
            self.log_error(f"Ошибка сохранения настроек интерфейса: {str(e)}")
            return False

    def load_interface_settings(self) -> Dict[str, Any]:
        """Загружает настройки интерфейса"""
        try:
            file_path = os.path.join(self.settings_dir, self.interface_settings_file)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self._interface_settings = json.load(f)
                self.log_info("Настройки интерфейса загружены")
            else:
                self._interface_settings = {}
        except Exception as e:
            self.log_error(f"Ошибка загрузки настроек интерфейса: {str(e)}")
            self._interface_settings = {}

        return self._interface_settings.copy()

    def save_parser_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки парсера"""
        try:
            settings["last_saved"] = datetime.now().isoformat()
            self._parser_settings.update(settings)

            file_path = os.path.join(self.settings_dir, self.parser_settings_file)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._parser_settings, f, indent=2, ensure_ascii=False)

            self.log_info("Настройки парсера сохранены")
            self.emit_event(EventType.DATA_UPDATED, {"type": "parser_settings", "data": settings})
            return True
        except Exception as e:
            self.log_error(f"Ошибка сохранения настроек парсера: {str(e)}")
            return False

    def load_parser_settings(self) -> Dict[str, Any]:
        """Загружает настройки парсера"""
        try:
            file_path = os.path.join(self.settings_dir, self.parser_settings_file)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self._parser_settings = json.load(f)
                self.log_info("Настройки парсера загружены")
            else:
                self._parser_settings = {}
        except Exception as e:
            self.log_error(f"Ошибка загрузки настроек парсера: {str(e)}")
            self._parser_settings = {}

        return self._parser_settings.copy()

    def save_sheets_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки Google Sheets"""
        try:
            settings["last_saved"] = datetime.now().isoformat()
            self._sheets_settings.update(settings)

            file_path = os.path.join(self.settings_dir, self.sheets_settings_file)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._sheets_settings, f, indent=2, ensure_ascii=False)

            self.log_info("Настройки Google Sheets сохранены")
            self.emit_event(EventType.DATA_UPDATED, {"type": "sheets_settings", "data": settings})
            return True
        except Exception as e:
            self.log_error(f"Ошибка сохранения настроек Google Sheets: {str(e)}")
            return False

    def load_sheets_settings(self) -> Dict[str, Any]:
        """Загружает настройки Google Sheets"""
        try:
            file_path = os.path.join(self.settings_dir, self.sheets_settings_file)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self._sheets_settings = json.load(f)
                self.log_info("Настройки Google Sheets загружены")
            else:
                self._sheets_settings = {}
        except Exception as e:
            self.log_error(f"Ошибка загрузки настроек Google Sheets: {str(e)}")
            self._sheets_settings = {}

        return self._sheets_settings.copy()

    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """Получает конкретную настройку"""
        try:
            if category == "window":
                return self._window_settings.get(key, default)
            elif category == "interface":
                return self._interface_settings.get(key, default)
            elif category == "parser":
                return self._parser_settings.get(key, default)
            elif category == "sheets":
                return self._sheets_settings.get(key, default)
            else:
                self.log_warning(f"Неизвестная категория настроек: {category}")
                return default
        except Exception as e:
            self.log_error(f"Ошибка получения настройки {category}.{key}: {str(e)}")
            return default

    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """Устанавливает конкретную настройку"""
        try:
            if category == "window":
                self._window_settings[key] = value
                return self.save_window_settings(self._window_settings)
            elif category == "interface":
                self._interface_settings[key] = value
                return self.save_interface_settings(self._interface_settings)
            elif category == "parser":
                self._parser_settings[key] = value
                return self.save_parser_settings(self._parser_settings)
            elif category == "sheets":
                self._sheets_settings[key] = value
                return self.save_sheets_settings(self._sheets_settings)
            else:
                self.log_warning(f"Неизвестная категория настроек: {category}")
                return False
        except Exception as e:
            self.log_error(f"Ошибка установки настройки {category}.{key}: {str(e)}")
            return False

    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает все настройки"""
        return {
            "window": self._window_settings.copy(),
            "interface": self._interface_settings.copy(),
            "parser": self._parser_settings.copy(),
            "sheets": self._sheets_settings.copy(),
        }

    def _load_all_settings(self) -> None:
        """Загружает все настройки"""
        self.load_window_settings()
        self.load_interface_settings()
        self.load_parser_settings()
        self.load_sheets_settings()

    def _save_all_settings(self) -> None:
        """Сохраняет все настройки"""
        self.save_window_settings(self._window_settings)
        self.save_interface_settings(self._interface_settings)
        self.save_parser_settings(self._parser_settings)
        self.save_sheets_settings(self._sheets_settings)

    def _reset_all_settings(self):
        """Сбрасывает все настройки"""
        # Очищаем в памяти
        self._window_settings = {}
        self._interface_settings = {}
        self._parser_settings = {}
        self._sheets_settings = {}

        # Удаляем файлы настроек
        for file_name in [
            self.window_settings_file,
            self.interface_settings_file,
            self.parser_settings_file,
            self.sheets_settings_file,
        ]:
            file_path = os.path.join(self.settings_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)

        self.log_info("Все настройки сброшены")

    def _reset_category_settings(self, category: str) -> bool:
        """Сбрасывает настройки конкретной категории"""
        # Словарь соответствий категорий
        category_map = {
            "window": (self._window_settings, self.window_settings_file),
            "interface": (self._interface_settings, self.interface_settings_file),
            "parser": (self._parser_settings, self.parser_settings_file),
            "sheets": (self._sheets_settings, self.sheets_settings_file),
        }

        if category not in category_map:
            self.log_warning(f"Неизвестная категория настроек: {category}")
            return False

        # Очищаем настройки в памяти
        settings_dict, file_name = category_map[category]
        settings_dict.clear()

        # Удаляем файл настроек
        file_path = os.path.join(self.settings_dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

        self.log_info(f"Настройки категории {category} сброшены")
        return True

    def reset_settings(self, category: Optional[str] = None) -> bool:
        """Сбрасывает настройки"""
        try:
            if category is None:
                self._reset_all_settings()
            else:
                if not self._reset_category_settings(category):
                    return False

            self.emit_event(EventType.DATA_UPDATED, {"type": "settings_reset", "category": category})
            return True

        except Exception as e:
            self.log_error(f"Ошибка сброса настроек: {e}")
            return False
