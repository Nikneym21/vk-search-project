"""
Адаптер для интеграции плагина настроек с интерфейсами
Обеспечивает автоматическое сохранение и загрузку настроек
"""

import tkinter as tk
from typing import Dict, Any, Optional
from loguru import logger

# Импортируем плагин настроек
try:
    from ..plugins.settings_manager.settings_manager_plugin import SettingsManagerPlugin
    SETTINGS_PLUGIN_AVAILABLE = True
except ImportError:
    SETTINGS_PLUGIN_AVAILABLE = False
    logger.warning("Плагин настроек недоступен")


class SettingsAdapter:
    """Адаптер для работы с настройками в интерфейсах"""
    
    def __init__(self, settings_plugin: Optional[SettingsManagerPlugin] = None):
        self.settings_plugin = settings_plugin
        self._auto_save_enabled = True
        
    def set_settings_plugin(self, plugin: SettingsManagerPlugin) -> None:
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
    
    def bind_variable_to_setting(self, var: tk.Variable, category: str, key: str, 
                                auto_save: bool = True) -> None:
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
    
    def bind_text_widget_to_setting(self, text_widget: tk.Text, category: str, key: str,
                                   auto_save: bool = True) -> None:
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
            text_widget.bind("<KeyRelease>", 
                           lambda event: self._auto_save_text_widget(text_widget, category, key))
    
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
    
    def create_settings_manager(self) -> Optional[SettingsManagerPlugin]:
        """Создает экземпляр плагина настроек"""
        if not SETTINGS_PLUGIN_AVAILABLE:
            logger.error("Плагин настроек недоступен")
            return None
        
        try:
            plugin = SettingsManagerPlugin()
            plugin.initialize()
            self.set_settings_plugin(plugin)
            return plugin
        except Exception as e:
            logger.error(f"Ошибка создания плагина настроек: {str(e)}")
            return None 