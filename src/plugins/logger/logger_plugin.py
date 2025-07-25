import os
from loguru import logger
from ...core.event_system import event_system, EventType
from ..base_plugin import BasePlugin
from datetime import datetime

class LoggerPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "LoggerPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для централизованного логирования событий и ошибок всех плагинов"

    def initialize(self):
        event_system.subscribe(EventType.ERROR, self.on_error)
        event_system.subscribe("log_error", self.on_error)
        event_system.subscribe("log_warning", self.on_warning)
        event_system.subscribe("log_info", self.on_info)
        event_system.subscribe("log_debug", self.on_debug)
        print("[LoggerPlugin] Подписан на события логирования.")

    def shutdown(self):
        pass

    def on_error(self, data):
        logger.error(f"[LoggerPlugin] {data}")
    def on_warning(self, data):
        logger.warning(f"[LoggerPlugin] {data}")
    def on_info(self, data):
        logger.info(f"[LoggerPlugin] {data}")
    def on_debug(self, data):
        logger.debug(f"[LoggerPlugin] {data}") 