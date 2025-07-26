import os
import time
from collections import defaultdict, deque
from loguru import logger
from src.core.event_system import event_system, EventType
from src.plugins.base_plugin import BasePlugin
from datetime import datetime

class LoggerPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "LoggerPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для централизованного логирования событий и ошибок всех плагинов"
        
        # Конфигурация для больших объемов
        self.config = {
            "batch_logging": True,
            "batch_size": 50,
            "batch_timeout": 5.0,  # секунды
            "rate_limit": {
                "info": 10,      # максимум логов в секунду
                "warning": 5,
                "error": 3,
                "debug": 20
            },
            "filter_patterns": [
                "cache-hit",      # фильтруем частые cache hits
                "rate_limit",     # фильтруем частые rate limits
                "progress"        # фильтруем прогресс батчей
            ],
            "high_volume_mode": False,
            "log_summary_interval": 30  # секунды
        }
        
        # Состояние для batch логирования
        self.batch_logs = defaultdict(list)
        self.last_batch_time = defaultdict(float)
        self.rate_limit_counters = defaultdict(lambda: {"count": 0, "last_reset": time.time()})
        self.log_summary = {
            "total_logs": 0,
            "errors": 0,
            "warnings": 0,
            "info": 0,
            "debug": 0,
            "last_summary": time.time()
        }

    def initialize(self):
        event_system.subscribe(EventType.ERROR, self.on_error)
        event_system.subscribe("log_error", self.on_error)
        event_system.subscribe("log_warning", self.on_warning)
        event_system.subscribe("log_info", self.on_info)
        event_system.subscribe("log_debug", self.on_debug)
        event_system.subscribe("high_volume_mode", self.set_high_volume_mode)
        print("[LoggerPlugin] Подписан на события логирования.")

    def shutdown(self):
        # Выводим финальную сводку
        self._print_log_summary()
        pass

    def set_high_volume_mode(self, enabled=True):
        """Включает режим для больших объемов данных"""
        self.config["high_volume_mode"] = enabled
        if enabled:
            logger.info("🔧 LoggerPlugin: включен режим для больших объемов данных")
        else:
            logger.info("🔧 LoggerPlugin: обычный режим логирования")

    def _should_log(self, level: str, message: str) -> bool:
        """Проверяет, нужно ли логировать сообщение"""
        current_time = time.time()
        
        # Rate limiting
        counter = self.rate_limit_counters[level]
        if current_time - counter["last_reset"] >= 1.0:
            counter["count"] = 0
            counter["last_reset"] = current_time
        
        if counter["count"] >= self.config["rate_limit"][level]:
            return False
        
        # Фильтрация паттернов для больших объемов
        if self.config["high_volume_mode"]:
            for pattern in self.config["filter_patterns"]:
                if pattern in message.lower():
                    return False
        
        counter["count"] += 1
        return True

    def _batch_log(self, level: str, message: str):
        """Добавляет лог в batch"""
        current_time = time.time()
        self.batch_logs[level].append({
            "message": message,
            "timestamp": current_time
        })
        
        # Проверяем, нужно ли вывести batch
        if (len(self.batch_logs[level]) >= self.config["batch_size"] or 
            current_time - self.last_batch_time[level] >= self.config["batch_timeout"]):
            self._flush_batch(level)

    def _flush_batch(self, level: str):
        """Выводит batch логов"""
        if not self.batch_logs[level]:
            return
        
        logs = self.batch_logs[level]
        count = len(logs)
        
        if count == 1:
            # Одиночный лог
            logger.log(level.upper(), f"[LoggerPlugin] {logs[0]['message']}")
        else:
            # Batch лог
            logger.log(level.upper(), f"[LoggerPlugin] Batch {count} {level} logs")
            for log in logs[:3]:  # Показываем первые 3
                logger.log(level.upper(), f"  - {log['message']}")
            if count > 3:
                logger.log(level.upper(), f"  ... и еще {count - 3} логов")
        
        # Очищаем batch
        self.batch_logs[level] = []
        self.last_batch_time[level] = time.time()

    def _update_log_summary(self, level: str):
        """Обновляет сводку логов"""
        self.log_summary["total_logs"] += 1
        self.log_summary[level] += 1
        
        # Выводим сводку каждые N секунд
        current_time = time.time()
        if current_time - self.log_summary["last_summary"] >= self.config["log_summary_interval"]:
            self._print_log_summary()
            self.log_summary["last_summary"] = current_time

    def _print_log_summary(self):
        """Выводит сводку логов"""
        summary = self.log_summary
        logger.info(f"📊 Сводка логов: {summary['total_logs']} всего "
                   f"(error: {summary['errors']}, warning: {summary['warnings']}, "
                   f"info: {summary['info']}, debug: {summary['debug']})")

    def on_error(self, data):
        if self._should_log("error", str(data)):
            if self.config["batch_logging"]:
                self._batch_log("error", str(data))
            else:
                logger.error(f"[LoggerPlugin] {data}")
            self._update_log_summary("errors")

    def on_warning(self, data):
        if self._should_log("warning", str(data)):
            if self.config["batch_logging"]:
                self._batch_log("warning", str(data))
            else:
                logger.warning(f"[LoggerPlugin] {data}")
            self._update_log_summary("warnings")

    def on_info(self, data):
        if self._should_log("info", str(data)):
            if self.config["batch_logging"]:
                self._batch_log("info", str(data))
            else:
                logger.info(f"[LoggerPlugin] {data}")
            self._update_log_summary("info")

    def on_debug(self, data):
        if self._should_log("debug", str(data)):
            if self.config["batch_logging"]:
                self._batch_log("debug", str(data))
            else:
                logger.debug(f"[LoggerPlugin] {data}")
            self._update_log_summary("debug") 