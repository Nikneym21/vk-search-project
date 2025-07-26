"""
Адаптер для интеграции плагина настроек с интерфейсами
Обеспечивает автоматическое сохранение и загрузку настроек
"""

import json
import os
import sys
import tkinter as tk
from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

# Добавляем путь к src в sys.path для корректного импорта
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

if TYPE_CHECKING:
    from src.plugins.settings_manager.settings_manager_plugin import SettingsManagerPlugin


# Простая версия плагина настроек без зависимости от BasePlugin
class SimpleSettingsManager:
    """Простой менеджер настроек без зависимости от BasePlugin"""

    def __init__(self):
        self.data_dir = "data"
        self.settings_cache = {}
        self._ensure_data_dir()
        logger.info("Простой менеджер настроек инициализирован")

    def _ensure_data_dir(self):
        """Создает папку data если её нет"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_settings_file(self, category: str) -> str:
        """Получает путь к файлу настроек"""
        return os.path.join(self.data_dir, f"{category}_settings.json")

    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """Получает настройку"""
        if category not in self.settings_cache:
            self._load_category(category)

        return self.settings_cache.get(category, {}).get(key, default)

    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """Устанавливает настройку"""
        if category not in self.settings_cache:
            self.settings_cache[category] = {}

        self.settings_cache[category][key] = value
        return self._save_category(category)

    def _load_category(self, category: str) -> None:
        """Загружает категорию настроек"""
        file_path = self._get_settings_file(category)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.settings_cache[category] = json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки настроек {category}: {e}")
                self.settings_cache[category] = {}
        else:
            self.settings_cache[category] = {}

    def _save_category(self, category: str) -> bool:
        """Сохраняет категорию настроек"""
        try:
            file_path = self._get_settings_file(category)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.settings_cache.get(category, {}), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек {category}: {e}")
            return False

    def save_window_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки окна"""
        return self.set_setting("window", "geometry", settings)

    def load_window_settings(self) -> Dict[str, Any]:
        """Загружает настройки окна"""
        return self.get_setting("window", "geometry", {})

    def save_parser_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки парсера"""
        for key, value in settings.items():
            self.set_setting("parser", key, value)
        return True

    def load_parser_settings(self) -> Dict[str, Any]:
        """Загружает настройки парсера"""
        return self.get_setting("parser", "settings", {})

    def save_sheets_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки Google Sheets"""
        for key, value in settings.items():
            self.set_setting("sheets", key, value)
        return True

    def load_sheets_settings(self) -> Dict[str, Any]:
        """Загружает настройки Google Sheets"""
        return self.get_setting("sheets", "settings", {})

    def reset_settings(self, category: Optional[str] = None) -> bool:
        """Сбрасывает настройки"""
        if category:
            if category in self.settings_cache:
                del self.settings_cache[category]
            file_path = self._get_settings_file(category)
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            self.settings_cache.clear()
            for file_name in os.listdir(self.data_dir):
                if file_name.endswith("_settings.json"):
                    os.remove(os.path.join(self.data_dir, file_name))
        return True


# Импортируем плагин настроек через PluginManager (не прямо)
# УДАЛЕН ПРЯМОЙ ИМПОРТ: from src.plugins.settings_manager.settings_manager_plugin import SettingsManagerPlugin
# Теперь плагин получается через PluginManager в методе create_settings_manager()

SETTINGS_PLUGIN_AVAILABLE = True  # Предполагаем что плагин доступен через PluginManager
logger.info("Плагин настроек будет получен через PluginManager")


class SettingsAdapter:
    """Адаптер для работы с настройками в интерфейсах"""

    def __init__(self, settings_plugin: Optional["SettingsManagerPlugin"] = None):
        self.settings_plugin = settings_plugin
        self._auto_save_enabled = True

        # Если плагин не передан, создаем простой менеджер
        if not self.settings_plugin:
            self.settings_plugin = SimpleSettingsManager()
            logger.info("Используется простой менеджер настроек")

    def set_settings_plugin(self, plugin: "SettingsManagerPlugin") -> None:
        """Устанавливает плагин настроек"""
        self.settings_plugin = plugin
        logger.info("Плагин настроек подключен к адаптеру")

    def enable_auto_save(self) -> None:
        """Включает автосохранение"""
        self._auto_save_enabled = True
        logger.info("Автосохранение настроек включено")

    def disable_auto_save(self) -> None:
        """Отключает автосохранение"""
        self._auto_save_enabled = False
        logger.info("Автосохранение настроек отключено")

    def bind_variable_to_setting(self, var: tk.Variable, category: str, key: str, auto_save: bool = True) -> None:
        """Привязывает переменную к настройке"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return

        # Загружаем значение из настроек
        value = self.settings_plugin.get_setting(category, key)
        if value is not None:
            if isinstance(var, tk.StringVar):
                var.set(str(value))
            elif isinstance(var, tk.IntVar):
                var.set(int(value))
            elif isinstance(var, tk.BooleanVar):
                var.set(bool(value))
            elif isinstance(var, tk.DoubleVar):
                var.set(float(value))

        # Привязываем автосохранение
        if auto_save and self._auto_save_enabled:
            var.trace("w", lambda *args: self._auto_save_variable(var, category, key))

    def bind_text_widget_to_setting(
        self, text_widget: tk.Text, category: str, key: str, auto_save: bool = True
    ) -> None:
        """Привязывает текстовый виджет к настройке"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return

        # Загружаем значение из настроек
        value = self.settings_plugin.get_setting(category, key, "")
        if value:
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", value)

        # Привязываем автосохранение
        if auto_save and self._auto_save_enabled:
            text_widget.bind("<KeyRelease>", lambda event: self._auto_save_text_widget(text_widget, category, key))

    def save_window_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки окна"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return False

        return self.settings_plugin.save_window_settings(settings)

    def load_window_settings(self) -> Dict[str, Any]:
        """Загружает настройки окна"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return {}

        return self.settings_plugin.load_window_settings()

    def save_parser_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки парсера"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return False

        return self.settings_plugin.save_parser_settings(settings)

    def load_parser_settings(self) -> Dict[str, Any]:
        """Загружает настройки парсера"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return {}

        return self.settings_plugin.load_parser_settings()

    def save_sheets_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохраняет настройки Google Sheets"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return False

        return self.settings_plugin.save_sheets_settings(settings)

    def load_sheets_settings(self) -> Dict[str, Any]:
        """Загружает настройки Google Sheets"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return {}

        return self.settings_plugin.load_sheets_settings()

    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """Получает конкретную настройку"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return default

        return self.settings_plugin.get_setting(category, key, default)

    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """Устанавливает конкретную настройку"""
        if not self.settings_plugin:
            logger.warning("Плагин настроек не подключен")
            return False

        return self.settings_plugin.set_setting(category, key, value)

    def _auto_save_variable(self, var: tk.Variable, category: str, key: str) -> None:
        """Автосохранение переменной"""
        try:
            value = var.get()
            self.set_setting(category, key, value)
        except Exception as e:
            logger.error(f"Ошибка автосохранения переменной {category}.{key}: {str(e)}")

    def _auto_save_text_widget(self, text_widget: tk.Text, category: str, key: str) -> None:
        """Автосохранение текстового виджета"""
        try:
            value = text_widget.get("1.0", tk.END).strip()
            self.set_setting(category, key, value)
        except Exception as e:
            logger.error(f"Ошибка автосохранения текстового виджета {category}.{key}: {str(e)}")

    def create_settings_manager(self, plugin_manager=None) -> Optional["SettingsManagerPlugin"]:
        """Создает экземпляр плагина настроек через PluginManager"""
        if plugin_manager and SETTINGS_PLUGIN_AVAILABLE:
            try:
                # Получаем плагин через PluginManager
                plugin = plugin_manager.get_plugin("settings_manager")
                if plugin:
                    self.set_settings_plugin(plugin)
                    logger.info("SettingsManagerPlugin получен через PluginManager")
                    return plugin
                else:
                    logger.warning("SettingsManagerPlugin не найден в PluginManager")
            except Exception as e:
                logger.error(f"Ошибка получения плагина настроек из PluginManager: {str(e)}")

        # Fallback: создаем простой менеджер
        logger.info("Создается простой менеджер настроек (fallback)")
        return SimpleSettingsManager()
