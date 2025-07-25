#!/usr/bin/env python3
"""
Плагин мониторинга производительности в реальном времени
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..base_plugin import BasePlugin
from ...core.event_system import EventType


class MonitoringPlugin(BasePlugin):
    """Плагин для мониторинга производительности системы"""
    
    def __init__(self):
        super().__init__()
        self.name = "MonitoringPlugin"
        self.version = "1.0.0"
        self.description = "Мониторинг производительности в реальном времени"
        
        # Конфигурация мониторинга
        self.config = {
            "enabled": True,
            "metrics_interval": 5,  # секунды
            "alert_thresholds": {
                "response_time": 2.0,  # секунды
                "rate_limit_hits": 10,  # количество
                "cache_hit_rate": 0.3,  # 30%
                "error_rate": 0.1,  # 10%
                "memory_usage": 0.8  # 80%
            },
            "metrics_history_size": 100,
            "enable_alerts": True,
            "enable_dashboard": True
        }
        
        # Метрики производительности
        self.metrics = {
            "response_times": [],
            "rate_limit_hits": 0,
            "cache_hit_rate": 0.0,
            "error_count": 0,
            "total_requests": 0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "active_connections": 0
        }
        
        # История метрик
        self.metrics_history = []
        
        # Алерты
        self.alerts = []
        
        # Мониторинг задач
        self.monitoring_task = None
        
    def initialize(self) -> None:
        """Инициализация плагина мониторинга"""
        self.log_info("Инициализация плагина мониторинга")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина мониторинга")
            return
        
        # Запускаем мониторинг
        if self.config["enabled"]:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.log_info("Мониторинг запущен")
        
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина мониторинга")
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return []
    
    def get_plugin_manager(self):
        """Получает PluginManager"""
        return self.plugin_manager
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while True:
            try:
                await self._collect_metrics()
                await self._check_alerts()
                await self._update_dashboard()
                
                # Сохраняем историю метрик
                self._save_metrics_history()
                
                await asyncio.sleep(self.config["metrics_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(5)
    
    async def _collect_metrics(self):
        """Сбор метрик производительности"""
        try:
            # Получаем метрики от других плагинов
            plugin_manager = self.get_plugin_manager()
            if not plugin_manager:
                return
            
            # Метрики VKSearchPlugin
            vk_plugin = plugin_manager.get_plugin('vk_search')
            if vk_plugin:
                vk_stats = vk_plugin.get_statistics()
                if vk_stats:
                    self.metrics["response_times"] = vk_stats.get("performance_metrics", {}).get("average_response_time", 0.0)
                    self.metrics["rate_limit_hits"] = vk_stats.get("performance_metrics", {}).get("rate_limit_hits", 0)
                    
                    # Метрики интеллектуального кэширования
                    intelligent_cache = vk_stats.get("intelligent_caching", {})
                    if intelligent_cache:
                        self.metrics["cache_hit_rate"] = intelligent_cache.get("cache_hit_rate", 0.0)
                        self.metrics["total_requests"] = intelligent_cache.get("total_cache_requests", 0)
            
            # Системные метрики
            self.metrics["memory_usage"] = self._get_memory_usage()
            self.metrics["cpu_usage"] = self._get_cpu_usage()
            self.metrics["active_connections"] = self._get_active_connections()
            
            self.log_info(f"📊 Метрики собраны: RT={self.metrics['response_times']:.3f}s, "
                         f"Cache={self.metrics['cache_hit_rate']:.1%}, "
                         f"Memory={self.metrics['memory_usage']:.1%}")
            
        except Exception as e:
            self.log_error(f"Ошибка сбора метрик: {e}")
    
    async def _check_alerts(self):
        """Проверка алертов"""
        if not self.config["enable_alerts"]:
            return
        
        alerts = []
        thresholds = self.config["alert_thresholds"]
        
        # Проверка времени ответа
        if isinstance(self.metrics["response_times"], (int, float)) and self.metrics["response_times"] > thresholds["response_time"]:
            alerts.append(f"⚠️ Высокое время ответа: {self.metrics['response_times']:.2f}s")
        
        # Проверка rate limit hits
        if isinstance(self.metrics["rate_limit_hits"], (int, float)) and self.metrics["rate_limit_hits"] > thresholds["rate_limit_hits"]:
            alerts.append(f"🚨 Много rate limit hits: {self.metrics['rate_limit_hits']}")
        
        # Проверка cache hit rate
        if isinstance(self.metrics["cache_hit_rate"], (int, float)) and self.metrics["cache_hit_rate"] < thresholds["cache_hit_rate"]:
            alerts.append(f"📉 Низкий cache hit rate: {self.metrics['cache_hit_rate']:.1%}")
        
        # Проверка использования памяти
        if isinstance(self.metrics["memory_usage"], (int, float)) and self.metrics["memory_usage"] > thresholds["memory_usage"]:
            alerts.append(f"💾 Высокое использование памяти: {self.metrics['memory_usage']:.1%}")
        
        # Логируем алерты
        for alert in alerts:
            self.log_warning(alert)
            self.alerts.append({
                "timestamp": datetime.now().isoformat(),
                "message": alert,
                "level": "warning"
            })
        
        # Ограничиваем количество алертов
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
    
    async def _update_dashboard(self):
        """Обновление дашборда"""
        if not self.config["enable_dashboard"]:
            return
        
        # Создаем дашборд данных
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "alerts": self.alerts[-10:],  # Последние 10 алертов
            "status": "healthy" if not self.alerts else "warning"
        }
        
        # Сохраняем дашборд
        self._save_dashboard(dashboard_data)
    
    def _save_metrics_history(self):
        """Сохранение истории метрик"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics.copy()
        }
        
        self.metrics_history.append(history_entry)
        
        # Ограничиваем размер истории
        if len(self.metrics_history) > self.config["metrics_history_size"]:
            self.metrics_history = self.metrics_history[-self.config["metrics_history_size"]:]
    
    def _save_dashboard(self, data: dict):
        """Сохранение данных дашборда"""
        try:
            with open("data/dashboard.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_error(f"Ошибка сохранения дашборда: {e}")
    
    def _get_memory_usage(self) -> float:
        """Получение использования памяти"""
        try:
            import psutil
            return psutil.virtual_memory().percent / 100.0
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Получение использования CPU"""
        try:
            import psutil
            return psutil.cpu_percent() / 100.0
        except ImportError:
            return 0.0
    
    def _get_active_connections(self) -> int:
        """Получение количества активных соединений"""
        try:
            import psutil
            return len(psutil.net_connections())
        except ImportError:
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику мониторинга"""
        return {
            "enabled": self.is_enabled(),
            "config": self.get_config(),
            "current_metrics": self.metrics,
            "alerts_count": len(self.alerts),
            "history_size": len(self.metrics_history),
            "dashboard_enabled": self.config["enable_dashboard"],
            "alerts_enabled": self.config["enable_alerts"]
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Возвращает данные для дашборда"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "alerts": self.alerts[-10:],
            "history": self.metrics_history[-20:],  # Последние 20 записей
            "status": "healthy" if not self.alerts else "warning"
        } 