import os
from ...core.event_system import event_system, EventType
from ..base_plugin import BasePlugin
from datetime import datetime

class LoggerPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "LoggerPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для централизованного логирования событий и ошибок всех плагинов"
        self.log_file = "logs/plugin_events.log"
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def initialize(self):
        event_system.subscribe(EventType.ERROR, self.on_error)
        event_system.subscribe("log_error", self.on_error)
        event_system.subscribe("log_warning", self.on_warning)
        event_system.subscribe("log_info", self.on_info)
        event_system.subscribe("log_debug", self.on_debug)
        print("[LoggerPlugin] Подписан на события логирования.")

    def shutdown(self):
        # Отписка не обязательна для простого логгера
        pass

    def _write_log(self, level, message):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {message}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line)
        print(line, end="")

    def on_error(self, data):
        self._write_log("ERROR", str(data))
    def on_warning(self, data):
        self._write_log("WARNING", str(data))
    def on_info(self, data):
        self._write_log("INFO", str(data))
    def on_debug(self, data):
        self._write_log("DEBUG", str(data)) 