"""
Плагин для сравнения ссылок между двумя таблицами
"""

import pandas as pd
import re
import os
from typing import Set, List, Dict, Any, Optional
from pathlib import Path

from ...core.event_system import EventType
from ..base_plugin import BasePlugin


class LinkComparatorPlugin(BasePlugin):
    """Плагин для сравнения ссылок между двумя таблицами"""
    
    def __init__(self):
        super().__init__()
        self.name = "LinkComparatorPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для сравнения ссылок между таблицами"
        
        # Конфигурация по умолчанию
        self.config = {
            "output_dir": "data/results",
            "link_patterns": [
                r'https?://[^\s<>"]+',
                r'www\.[^\s<>"]+',
                r'vk\.com/[^\s<>"]+'
            ],
            "case_sensitive": False,
            "ignore_duplicates": True
        }
        
        self.table1_data = None
        self.table2_data = None
        self.table1_path = None
        self.table2_path = None
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Link Comparator")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        # Создаем директорию для результатов
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
        
        self.log_info("Плагин Link Comparator инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Link Comparator")
        
        # Очищаем данные
        self.table1_data = None
        self.table2_data = None
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Link Comparator завершен")
    
    def load_table1(self, file_path: str) -> bool:
        """Загружает первую таблицу"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Определяем формат файла по расширению
            if file_path.endswith('.csv'):
                self.table1_data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                self.table1_data = pd.read_excel(file_path)
            else:
                raise ValueError("Неподдерживаемый формат файла")
            
            self.table1_path = file_path
            self.log_info(f"Таблица 1 загружена: {file_path} ({len(self.table1_data)} строк)")
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки таблицы 1: {e}")
            return False
    
    def load_table2(self, file_path: str) -> bool:
        """Загружает вторую таблицу"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Определяем формат файла по расширению
            if file_path.endswith('.csv'):
                self.table2_data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                self.table2_data = pd.read_excel(file_path)
            else:
                raise ValueError("Неподдерживаемый формат файла")
            
            self.table2_path = file_path
            self.log_info(f"Таблица 2 загружена: {file_path} ({len(self.table2_data)} строк)")
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки таблицы 2: {e}")
            return False
    
    def get_table_columns(self, table_num: int) -> List[str]:
        """Возвращает список колонок для указанной таблицы"""
        try:
            if table_num == 1 and self.table1_data is not None:
                return list(self.table1_data.columns)
            elif table_num == 2 and self.table2_data is not None:
                return list(self.table2_data.columns)
            else:
                return []
                
        except Exception as e:
            self.log_error(f"Ошибка получения колонок таблицы {table_num}: {e}")
            return []
    
    def extract_links_from_column(self, data: pd.DataFrame, column: str) -> Set[str]:
        """Извлекает ссылки из указанной колонки"""
        try:
            if column not in data.columns:
                raise ValueError(f"Колонка '{column}' не найдена в таблице")
            
            links = set()
            patterns = self.config["link_patterns"]
            
            for value in data[column].dropna():
                value_str = str(value)
                for pattern in patterns:
                    found_links = re.findall(pattern, value_str, re.IGNORECASE if not self.config["case_sensitive"] else 0)
                    links.update(found_links)
            
            return links
            
        except Exception as e:
            self.log_error(f"Ошибка извлечения ссылок из колонки '{column}': {e}")
            return set()
    
    def compare_links(self, column1: str, column2: str) -> Dict[str, Any]:
        """Сравнивает ссылки между двумя колонками"""
        try:
            if self.table1_data is None or self.table2_data is None:
                raise ValueError("Обе таблицы должны быть загружены")
            
            # Извлекаем ссылки
            links1 = self.extract_links_from_column(self.table1_data, column1)
            links2 = self.extract_links_from_column(self.table2_data, column2)
            
            # Выполняем сравнение
            common_links = links1.intersection(links2)
            only_in_table1 = links1 - links2
            only_in_table2 = links2 - links1
            
            result = {
                "common_links": list(common_links),
                "only_in_table1": list(only_in_table1),
                "only_in_table2": list(only_in_table2),
                "total_table1": len(links1),
                "total_table2": len(links2),
                "common_count": len(common_links)
            }
            
            self.log_info(f"Сравнение завершено: {len(common_links)} общих ссылок")
            self.emit_event(EventType.DATA_UPDATED, {
                "operation": "link_comparison",
                "common_count": len(common_links),
                "total_table1": len(links1),
                "total_table2": len(links2)
            })
            
            return result
            
        except Exception as e:
            self.log_error(f"Ошибка сравнения ссылок: {e}")
            return {"error": str(e)}
    
    def save_comparison_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Сохраняет результаты сравнения"""
        try:
            if filename is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"link_comparison_{timestamp}.json"
            
            filepath = os.path.join(self.config["output_dir"], filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                import json
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.log_info(f"Результаты сравнения сохранены: {filepath}")
            return filepath
            
        except Exception as e:
            self.log_error(f"Ошибка сохранения результатов: {e}")
            raise
    
    def get_table_info(self, table_num: int) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о таблице"""
        try:
            if table_num == 1 and self.table1_data is not None:
                return {
                    "path": self.table1_path,
                    "rows": len(self.table1_data),
                    "columns": len(self.table1_data.columns),
                    "columns_list": list(self.table1_data.columns)
                }
            elif table_num == 2 and self.table2_data is not None:
                return {
                    "path": self.table2_path,
                    "rows": len(self.table2_data),
                    "columns": len(self.table2_data.columns),
                    "columns_list": list(self.table2_data.columns)
                }
            else:
                return None
                
        except Exception as e:
            self.log_error(f"Ошибка получения информации о таблице {table_num}: {e}")
            return None
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = ["output_dir", "link_patterns"]
        
        for key in required_keys:
            if key not in self.config:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False
        
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["output_dir", "link_patterns"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        try:
            stats = {
                "table1_loaded": self.table1_data is not None,
                "table2_loaded": self.table2_data is not None,
                "output_directory": self.config["output_dir"]
            }
            
            if self.table1_data is not None:
                stats["table1_info"] = self.get_table_info(1)
            
            if self.table2_data is not None:
                stats["table2_info"] = self.get_table_info(2)
            
            return stats
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)} 