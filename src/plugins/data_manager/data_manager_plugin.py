"""
Плагин для управления данными и экспорта
"""

import sqlite3
import csv
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...core.event_system import EventType
from ..base_plugin import BasePlugin


class DataManagerPlugin(BasePlugin):
    """Плагин для управления данными и экспорта"""
    
    def __init__(self):
        super().__init__()
        self.name = "DataManagerPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для управления данными и экспорта результатов"
        
        # Конфигурация по умолчанию
        self.config = {
            "database_path": "data/vk_search.db",
            "export_path": "data/results",
            "auto_backup": True,
            "backup_interval": 24  # часы
        }
        
        self.db_connection: Optional[sqlite3.Connection] = None
        
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Data Manager")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        # Создаем директории если не существуют
        Path(self.config["export_path"]).mkdir(parents=True, exist_ok=True)
        Path(self.config["database_path"]).parent.mkdir(parents=True, exist_ok=True)
        
        # Инициализируем базу данных
        self._init_database()
        
        self.log_info("Плагин Data Manager инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Data Manager")
        
        if self.db_connection:
            self.db_connection.close()
        
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Data Manager завершен")
    
    def _init_database(self) -> None:
        """Инициализация базы данных"""
        try:
            self.db_connection = sqlite3.connect(self.config["database_path"])
            self.db_connection.row_factory = sqlite3.Row
            
            # Создаем таблицы если не существуют
            self._create_tables()
            
            self.log_info("База данных инициализирована")
        except Exception as e:
            self.log_error(f"Ошибка инициализации базы данных: {e}")
    
    def _create_tables(self) -> None:
        """Создает необходимые таблицы"""
        cursor = self.db_connection.cursor()
        
        # Таблица для результатов поиска
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result_type TEXT NOT NULL,
                vk_id INTEGER,
                title TEXT,
                content TEXT,
                author_id INTEGER,
                author_name TEXT,
                likes_count INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                shares_count INTEGER DEFAULT 0,
                created_date INTEGER,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица для метаданных поиска
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                search_type TEXT NOT NULL,
                results_count INTEGER DEFAULT 0,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'running'
            )
        """)
        
        # Таблица для экспортов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                export_type TEXT NOT NULL,
                records_count INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db_connection.commit()
    
    def save_search_results(self, query: str, results: List[Dict[str, Any]], 
                          search_type: str = "posts") -> bool:
        """Сохраняет результаты поиска в базу данных"""
        if not self.db_connection:
            self.log_error("База данных не инициализирована")
            return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # Создаем сессию поиска
            cursor.execute("""
                INSERT INTO search_sessions (query, search_type, results_count)
                VALUES (?, ?, ?)
            """, (query, search_type, len(results)))
            
            session_id = cursor.lastrowid
            
            # Сохраняем результаты
            for result in results:
                cursor.execute("""
                    INSERT INTO search_results (
                        query, result_type, vk_id, title, content, 
                        author_id, author_name, likes_count, comments_count,
                        shares_count, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    query,
                    search_type,
                    result.get("id"),
                    result.get("title", ""),
                    result.get("text", "")[:1000],  # Ограничиваем длину
                    result.get("from_id"),
                    result.get("author_name", ""),
                    result.get("likes", {}).get("count", 0),
                    result.get("comments", {}).get("count", 0),
                    result.get("reposts", {}).get("count", 0),
                    result.get("date")
                ))
            
            # Обновляем статус сессии
            cursor.execute("""
                UPDATE search_sessions 
                SET end_time = CURRENT_TIMESTAMP, status = 'completed'
                WHERE id = ?
            """, (session_id,))
            
            self.db_connection.commit()
            
            self.log_info(f"Сохранено {len(results)} результатов поиска")
            self.emit_event(EventType.DATA_UPDATED, {
                "query": query,
                "results_count": len(results)
            })
            
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка сохранения результатов: {e}")
            return False
    
    def get_search_results(self, query: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает результаты поиска из базы данных"""
        if not self.db_connection:
            return []
        
        try:
            cursor = self.db_connection.cursor()
            
            if query:
                cursor.execute("""
                    SELECT * FROM search_results 
                    WHERE query LIKE ? 
                    ORDER BY search_date DESC 
                    LIMIT ?
                """, (f"%{query}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM search_results 
                    ORDER BY search_date DESC 
                    LIMIT ?
                """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self.log_error(f"Ошибка получения результатов: {e}")
            return []
    
    def export_to_csv(self, query: str = None, filename: str = None) -> Optional[str]:
        """Экспортирует результаты в CSV файл"""
        results = self.get_search_results(query)
        
        if not results:
            self.log_warning("Нет данных для экспорта")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_suffix = f"_{query.replace(' ', '_')}" if query else ""
            filename = f"vk_search_results{query_suffix}_{timestamp}.csv"
        
        filepath = Path(self.config["export_path"]) / filename
        
        try:
            df = pd.DataFrame(results)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            # Записываем информацию об экспорте
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO exports (filename, export_type, records_count)
                VALUES (?, ?, ?)
            """, (filename, "csv", len(results)))
            self.db_connection.commit()
            
            self.log_info(f"Экспорт завершен: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.log_error(f"Ошибка экспорта в CSV: {e}")
            return None
    
    def export_to_json(self, query: str = None, filename: str = None) -> Optional[str]:
        """Экспортирует результаты в JSON файл"""
        results = self.get_search_results(query)
        
        if not results:
            self.log_warning("Нет данных для экспорта")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_suffix = f"_{query.replace(' ', '_')}" if query else ""
            filename = f"vk_search_results{query_suffix}_{timestamp}.json"
        
        filepath = Path(self.config["export_path"]) / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # Записываем информацию об экспорте
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO exports (filename, export_type, records_count)
                VALUES (?, ?, ?)
            """, (filename, "json", len(results)))
            self.db_connection.commit()
            
            self.log_info(f"Экспорт завершен: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.log_error(f"Ошибка экспорта в JSON: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        if not self.db_connection:
            return {"error": "База данных не инициализирована"}
        
        try:
            cursor = self.db_connection.cursor()
            
            # Общее количество результатов
            cursor.execute("SELECT COUNT(*) FROM search_results")
            total_results = cursor.fetchone()[0]
            
            # Количество уникальных запросов
            cursor.execute("SELECT COUNT(DISTINCT query) FROM search_results")
            unique_queries = cursor.fetchone()[0]
            
            # Последние экспорты
            cursor.execute("""
                SELECT filename, export_type, records_count, created_date 
                FROM exports 
                ORDER BY created_date DESC 
                LIMIT 5
            """)
            recent_exports = [dict(row) for row in cursor.fetchall()]
            
            return {
                "total_results": total_results,
                "unique_queries": unique_queries,
                "recent_exports": recent_exports,
                "database_path": self.config["database_path"],
                "export_path": self.config["export_path"]
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)}
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = ["database_path", "export_path"]
        
        for key in required_keys:
            if key not in self.config:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False
        
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["database_path", "export_path"] 

    def save_results_to_csv(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Сохраняет переданные результаты в CSV и возвращает путь к файлу"""
        if not results:
            raise ValueError("Нет данных для сохранения")
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}.csv"
        filepath = Path(self.config["export_path"]) / filename
        # Определяем все возможные ключи
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        fieldnames = sorted(list(all_keys))
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        except Exception as e:
            self.log_error(f"Ошибка сохранения в CSV: {e}")
            print("Ошибка при экспорте:", e)
            print("Пример данных:", results[0] if results else "Нет данных")
            raise
        self.log_info(f"Результаты сохранены в CSV: {filepath}")
        self.emit_event(EventType.DATA_UPDATED, {
            "filepath": str(filepath),
            "records_count": len(results),
            "format": "csv"
        })
        return str(filepath) 

    def save_task_meta(self, meta: dict, filepath: str) -> None:
        """Сохраняет meta.json для задачи по указанному пути (filepath — путь к .csv)"""
        meta_path = str(filepath).replace('.csv', '.meta.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def load_task_meta(self, filepath: str) -> dict:
        """Загружает meta.json для задачи по указанному пути (filepath — путь к .csv)"""
        meta_path = str(filepath).replace('.csv', '.meta.json')
        if not Path(meta_path).exists():
            return {}
        with open(meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_all_tasks(self) -> list:
        """Возвращает список всех задач (по всем meta.json в export_path)"""
        tasks = []
        export_path = Path(self.config.get('export_path', 'data/results'))
        meta_files = list(export_path.glob('*.meta.json'))
        print(f"[DataManagerPlugin][DEBUG] Найдено meta.json: {len(meta_files)}")
        for meta_file in meta_files:
            print(f"[DataManagerPlugin][DEBUG] meta.json файл: {meta_file}")
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    meta['meta_path'] = str(meta_file)
                    tasks.append(meta)
            except Exception as e:
                print(f"[DataManagerPlugin][DEBUG] Ошибка чтения meta.json: {meta_file}: {e}")
        print(f"[DataManagerPlugin][DEBUG] Всего задач: {len(tasks)}")
        if tasks:
            print(f"[DataManagerPlugin][DEBUG] Первая задача: {tasks[0]}")
        return tasks 

    def save_task_meta_full(self, *, keywords, start_date, end_date, exact_match, minus_words, filepath, filtered, status=None, exception=None):
        """Формирует и сохраняет meta.json для задачи по всем параметрам и результату."""
        from src.plugins.stats_plugin import StatsPlugin
        meta = {
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'keywords': keywords,
            'start_date': start_date,
            'end_date': end_date,
            'exact_match': exact_match,
            'minus_words': minus_words,
            'filepath': filepath,
            'count': len(filtered) if filtered else 0,
            'stats': StatsPlugin.calculate_stats(filtered) if filtered else {},
            'status': status or ('Готово' if filtered else 'Пусто')
        }
        if exception:
            meta['status'] = f'Ошибка: {exception}'
        print(f"[DataManagerPlugin][DEBUG] save_task_meta_full: {filepath} -> {meta}")
        self.save_task_meta(meta, filepath) 