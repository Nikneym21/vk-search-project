"""
Плагин для работы с базой данных и сохранения результатов
"""

import json
import csv
import os
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ...core.event_system import EventType
from ..base_plugin import BasePlugin


class DatabasePlugin(BasePlugin):
    """Плагин для работы с базой данных и сохранения результатов"""
    
    def __init__(self):
        super().__init__()
        self.name = "DatabasePlugin"
        self.version = "1.0.0"
        self.description = "Плагин для работы с базой данных и сохранения результатов"
        
        # Конфигурация по умолчанию
        self.config = {
            "data_dir": "data/results",
            "backup_enabled": True,
            "auto_save": True,
            "max_file_size": "100MB"
        }
        
        self.data_dir = self.config["data_dir"]
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Database")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        # Создаем директорию для данных
        self.ensure_data_directory()
        
        self.log_info("Плагин Database инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Database")
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Database завершен")
    
    def ensure_data_directory(self):
        """Создает директорию для данных, если она не существует"""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
    
    def save_results_to_csv(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Сохраняет результаты в CSV файл"""
        try:
            if not results:
                raise ValueError("Нет данных для сохранения")
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"results_{timestamp}.csv"
            
            filepath = os.path.join(self.data_dir, filename)
            
            # Определяем все возможные ключи из результатов
            all_keys = set()
            for result in results:
                all_keys.update(result.keys())
            
            # Сортируем ключи для стабильного порядка
            fieldnames = sorted(list(all_keys))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            self.log_info(f"Результаты сохранены в CSV: {filepath}")
            self.emit_event(EventType.DATA_UPDATED, {
                "filepath": filepath,
                "records_count": len(results),
                "format": "csv"
            })
            
            return filepath
            
        except Exception as e:
            self.log_error(f"Ошибка сохранения в CSV: {str(e)}")
            raise
    
    def save_results_to_json(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Сохраняет результаты в JSON файл"""
        try:
            if not results:
                raise ValueError("Нет данных для сохранения")
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"results_{timestamp}.json"
            
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(results, jsonfile, ensure_ascii=False, indent=2)
            
            self.log_info(f"Результаты сохранены в JSON: {filepath}")
            self.emit_event(EventType.DATA_UPDATED, {
                "filepath": filepath,
                "records_count": len(results),
                "format": "json"
            })
            
            return filepath
            
        except Exception as e:
            self.log_error(f"Ошибка сохранения в JSON: {str(e)}")
            raise
    
    def load_results_from_csv(self, filename: str) -> List[Dict[str, Any]]:
        """Загружает результаты из CSV файла"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Файл не найден: {filepath}")
            
            results = []
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    results.append(row)
            
            self.log_info(f"Результаты загружены из CSV: {filepath}")
            return results
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки из CSV: {str(e)}")
            raise
    
    def load_results_from_json(self, filename: str) -> List[Dict[str, Any]]:
        """Загружает результаты из JSON файла"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Файл не найден: {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as jsonfile:
                results = json.load(jsonfile)
            
            self.log_info(f"Результаты загружены из JSON: {filepath}")
            return results
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки из JSON: {str(e)}")
            raise
    
    def get_available_files(self, extension: str = None) -> List[str]:
        """Возвращает список доступных файлов"""
        try:
            files = []
            for file in os.listdir(self.data_dir):
                if extension is None or file.endswith(extension):
                    files.append(file)
            
            return sorted(files)
            
        except Exception as e:
            self.log_error(f"Ошибка получения списка файлов: {str(e)}")
            return []
    
    def delete_file(self, filename: str) -> bool:
        """Удаляет файл"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                self.log_warning(f"Файл не найден: {filepath}")
                return False
            
            os.remove(filepath)
            self.log_info(f"Файл удален: {filepath}")
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка удаления файла: {str(e)}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о файле"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            stat = os.stat(filepath)
            
            return {
                "filename": filename,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": filepath
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения информации о файле: {str(e)}")
            return None
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = ["data_dir"]
        
        for key in required_keys:
            if key not in self.config:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False
        
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["data_dir"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        try:
            files = self.get_available_files()
            total_size = 0
            
            for file in files:
                file_info = self.get_file_info(file)
                if file_info:
                    total_size += file_info["size"]
            
            return {
                "total_files": len(files),
                "total_size": total_size,
                "data_directory": self.data_dir,
                "available_formats": ["csv", "json"]
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики: {str(e)}")
            return {"error": str(e)} 