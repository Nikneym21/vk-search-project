"""
Менеджер конфигурации для управления настройками системы
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Конфигурация базы данных"""

    path: str = Field(default="data/vk_search.db")
    backup_enabled: bool = Field(default=True)
    backup_interval: int = Field(default=24)  # часы


class LoggingConfig(BaseModel):
    """Конфигурация логирования"""

    level: str = Field(default="INFO")
    file_path: str = Field(default="data/logs/app.log")
    max_size: str = Field(default="10 MB")
    rotation: str = Field(default="1 day")


class VKConfig(BaseModel):
    """Конфигурация VK API"""

    api_version: str = Field(default="5.131")
    request_delay: float = Field(default=0.5)
    max_requests_per_second: int = Field(default=3)
    timeout: int = Field(default=30)


class GoogleSheetsConfig(BaseModel):
    """Конфигурация Google Sheets"""

    credentials_file: str = Field(default="config/service_account.json")
    scopes: list = Field(default=["https://www.googleapis.com/auth/spreadsheets"])
    spreadsheet_id: Optional[str] = None


class AppConfig(BaseModel):
    """Основная конфигурация приложения"""

    app_name: str = Field(default="VK Search Project")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # Подконфигурации
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    vk: VKConfig = Field(default_factory=VKConfig)
    google_sheets: GoogleSheetsConfig = Field(default_factory=GoogleSheetsConfig)


class ConfigManager:
    """Менеджер для управления конфигурацией приложения"""

    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.config: AppConfig = AppConfig()
        self._load_config()

    def _load_config(self) -> None:
        """Загружает конфигурацию из файла"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                self.config = AppConfig(**config_data)
                logger.info(f"Конфигурация загружена из {self.config_path}")
            except Exception as e:
                logger.error(f"Ошибка загрузки конфигурации: {e}")
                self._create_default_config()
        else:
            logger.info("Файл конфигурации не найден, создается по умолчанию")
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Создает конфигурацию по умолчанию"""
        self.config = AppConfig()
        self.save_config()

    def save_config(self) -> None:
        """Сохраняет конфигурацию в файл"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config.dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Конфигурация сохранена в {self.config_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")

    def get_config(self) -> AppConfig:
        """Возвращает текущую конфигурацию"""
        return self.config

    def update_config(self, **kwargs) -> None:
        """Обновляет конфигурацию"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Неизвестный параметр конфигурации: {key}")

        self.save_config()

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Возвращает конфигурацию для конкретного плагина"""
        plugin_config_key = f"{plugin_name}_config"
        if hasattr(self.config, plugin_config_key):
            return getattr(self.config, plugin_config_key).dict()
        return {}

    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Устанавливает конфигурацию для конкретного плагина"""
        plugin_config_key = f"{plugin_name}_config"
        if hasattr(self.config, plugin_config_key):
            current_config = getattr(self.config, plugin_config_key)
            for key, value in config.items():
                if hasattr(current_config, key):
                    setattr(current_config, key, value)
            self.save_config()
        else:
            logger.warning(f"Конфигурация для плагина {plugin_name} не найдена")
