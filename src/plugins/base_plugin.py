"""
Базовый класс для всех плагинов системы
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from loguru import logger

from ..core.event_system import EventType, event_system


class BasePlugin(ABC):
    """Базовый класс для всех плагинов"""

    def __init__(self):
        self.name: str = self.__class__.__name__
        self.version: str = "1.0.0"
        self.description: str = "Базовый плагин"
        self.enabled: bool = True
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def initialize(self) -> None:
        """Инициализация плагина"""

    @abstractmethod
    def shutdown(self) -> None:
        """Завершение работы плагина"""

    def get_info(self) -> Dict[str, Any]:
        """Возвращает информацию о плагине"""
        return {"name": self.name, "version": self.version, "description": self.description, "enabled": self.enabled}

    def set_config(self, config: Dict[str, Any]) -> None:
        """Устанавливает конфигурацию плагина"""
        self.config.update(config)
        logger.info(f"Конфигурация плагина {self.name} обновлена")

    def get_config(self) -> Dict[str, Any]:
        """Возвращает текущую конфигурацию плагина"""
        return self.config.copy()

    def enable(self) -> None:
        """Включает плагин"""
        self.enabled = True
        event_system.emit(EventType.PLUGIN_LOADED, self.name, {"enabled": True})
        logger.info(f"Плагин {self.name} включен")

    def disable(self) -> None:
        """Отключает плагин"""
        self.enabled = False
        event_system.emit(EventType.PLUGIN_UNLOADED, self.name, {"enabled": False})
        logger.info(f"Плагин {self.name} отключен")

    def is_enabled(self) -> bool:
        """Проверяет, включен ли плагин"""
        return self.enabled

    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации плагина"""
        # Базовая реализация - всегда True
        # Переопределяется в наследниках при необходимости
        return True

    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        # Базовая реализация - пустой список
        # Переопределяется в наследниках при необходимости
        return []

    def check_dependencies(self) -> bool:
        """Проверяет зависимости плагина"""
        # Базовая реализация - всегда True
        # Переопределяется в наследниках при необходимости
        return True

    def get_help(self) -> str:
        """Возвращает справку по плагину"""
        return f"Плагин {self.name} версии {self.version}\n{self.description}"

    def emit_event(self, event_type: EventType, data: Dict[str, Any] = None) -> None:
        """Отправляет событие от имени плагина"""
        event_system.emit(event_type, self.name, data or {})

    def log_info(self, message: str) -> None:
        """Логирует информационное сообщение"""
        logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str) -> None:
        """Логирует сообщение об ошибке"""
        logger.error(f"[{self.name}] {message}")

    def log_warning(self, message: str) -> None:
        """Логирует предупреждение"""
        logger.warning(f"[{self.name}] {message}")

    def log_debug(self, message: str) -> None:
        """Логирует отладочное сообщение"""
        logger.debug(f"[{self.name}] {message}")
