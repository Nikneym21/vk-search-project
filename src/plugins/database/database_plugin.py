"""
Плагин для работы с базой данных и сохранения результатов
"""

import json
import csv
import os
import pandas as pd
import sqlite3
import hashlib
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
            "max_file_size": "100MB",
            "db_path": "data/parser_results.db"
        }
        
        self.data_dir = self.config["data_dir"]
        self.db_path = self.config["db_path"]
        self.connection = None
        self.filter_plugin = None
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Database")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        # Создаем директорию для данных
        self.ensure_data_directory()
        
        # Инициализируем базу данных
        self._init_database()
        
        self.log_info("Плагин Database инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def _init_database(self):
        """Инициализация базы данных"""
        try:
            # Создаем подключение к БД
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Для доступа по именам колонок
            
            # Создаем таблицы
            self._create_tables()
            
            self.log_info("База данных инициализирована")
            
        except Exception as e:
            self.log_error(f"Ошибка инициализации БД: {e}")
    
    def _create_tables(self):
        """Создание таблиц в базе данных"""
        cursor = self.connection.cursor()
        
        # Таблица задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT UNIQUE NOT NULL,
                keywords TEXT NOT NULL,  -- JSON массив ключевых слов
                start_date TEXT,
                end_date TEXT,
                exact_match BOOLEAN DEFAULT 1,
                minus_words TEXT,  -- JSON массив минус-слов
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'created',  -- created, running, completed, error
                total_posts INTEGER DEFAULT 0,
                total_likes INTEGER DEFAULT 0,
                total_comments INTEGER DEFAULT 0,
                total_reposts INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                total_SI INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица постов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                vk_id TEXT NOT NULL,  -- ID поста в VK (owner_id_post_id)
                link TEXT NOT NULL,  -- Полная ссылка на пост
                link_hash TEXT NOT NULL,  -- MD5 хеш ссылки для поиска дубликатов
                text TEXT NOT NULL,
                text_hash TEXT NOT NULL,  -- MD5 хеш текста для быстрого поиска дубликатов
                date INTEGER,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                reposts INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                keywords_matched TEXT,  -- JSON массив найденных ключевых слов
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                UNIQUE(task_id, link_hash)
            )
        ''')
        
        # Таблица метаданных задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                meta_key TEXT NOT NULL,
                meta_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                UNIQUE(task_id, meta_key)
            )
        ''')
        
        # Создаем индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_task_id ON posts(task_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_link_hash ON posts(link_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_text_hash ON posts(text_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)')
        
        self.connection.commit()
        self.log_info("Таблицы и индексы созданы успешно")
    
    def set_filter_plugin(self, filter_plugin):
        """Устанавливает связь с плагином фильтрации"""
        self.filter_plugin = filter_plugin
        self.log_info("FilterPlugin подключен к DatabasePlugin")
    
    def create_task(self, task_name: str, keywords: List[str], start_date: str = None, 
                   end_date: str = None, exact_match: bool = True, minus_words: List[str] = None) -> int:
        """Создание новой задачи"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO tasks (task_name, keywords, start_date, end_date, exact_match, minus_words)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task_name,
                json.dumps(keywords, ensure_ascii=False),
                start_date,
                end_date,
                exact_match,
                json.dumps(minus_words or [], ensure_ascii=False)
            ))
            
            task_id = cursor.lastrowid
            self.connection.commit()
            
            self.log_info(f"Создана задача {task_id}: {task_name}")
            return task_id
            
        except Exception as e:
            self.log_error(f"Ошибка создания задачи: {e}")
            return None
    
    def save_posts(self, task_id: int, posts: List[Dict]) -> int:
        """Сохранение постов в базу данных"""
        if not posts:
            return 0
        
        try:
            cursor = self.connection.cursor()
            saved_count = 0
            
            for post in posts:
                # Извлекаем данные из поста
                owner_id = post.get('owner_id', 0)
                post_id = post.get('id', 0)
                vk_id = f"{owner_id}_{post_id}"
                link = f"https://vk.com/wall{owner_id}_{post_id}"
                
                text = post.get('text', '')
                if not text:
                    continue
                
                # Создаем хеши
                link_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                
                # Извлекаем статистику
                likes = post.get('likes', {}).get('count', 0) if isinstance(post.get('likes'), dict) else post.get('likes', 0)
                comments = post.get('comments', {}).get('count', 0) if isinstance(post.get('comments'), dict) else post.get('comments', 0)
                reposts = post.get('reposts', {}).get('count', 0) if isinstance(post.get('reposts'), dict) else post.get('reposts', 0)
                views = post.get('views', {}).get('count', 0) if isinstance(post.get('views'), dict) else post.get('views', 0)
                
                # Ключевые слова, которые сработали
                keywords_matched = post.get('keywords_matched', [])
                
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO posts 
                        (task_id, vk_id, link, link_hash, text, text_hash, date, likes, comments, reposts, views, keywords_matched)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        task_id,
                        vk_id,
                        link,
                        link_hash,
                        text,
                        text_hash,
                        post.get('date', 0),
                        likes,
                        comments,
                        reposts,
                        views,
                        json.dumps(keywords_matched, ensure_ascii=False)
                    ))
                    
                    if cursor.rowcount > 0:
                        saved_count += 1
                        
                except sqlite3.IntegrityError:
                    # Пост уже существует, пропускаем
                    pass
            
            # Обновляем статистику задачи
            self._update_task_statistics(task_id)
            
            self.connection.commit()
            self.log_info(f"Сохранено {saved_count} новых постов для задачи {task_id}")
            return saved_count
            
        except Exception as e:
            self.log_error(f"Ошибка сохранения постов: {e}")
            return 0
    
    def _update_task_statistics(self, task_id: int):
        """Обновление статистики задачи"""
        try:
            cursor = self.connection.cursor()
            
            # Получаем статистику по постам
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_posts,
                    SUM(likes) as total_likes,
                    SUM(comments) as total_comments,
                    SUM(reposts) as total_reposts,
                    SUM(views) as total_views
                FROM posts 
                WHERE task_id = ?
            ''', (task_id,))
            
            stats = cursor.fetchone()
            
            if stats:
                total_SI = (stats['total_likes'] or 0) + (stats['total_comments'] or 0) + (stats['total_reposts'] or 0)
                
                cursor.execute('''
                    UPDATE tasks 
                    SET total_posts = ?, total_likes = ?, total_comments = ?, 
                        total_reposts = ?, total_views = ?, total_SI = ?
                    WHERE id = ?
                ''', (
                    stats['total_posts'] or 0,
                    stats['total_likes'] or 0,
                    stats['total_comments'] or 0,
                    stats['total_reposts'] or 0,
                    stats['total_views'] or 0,
                    total_SI,
                    task_id
                ))
                
                self.connection.commit()
                
        except Exception as e:
            self.log_error(f"Ошибка обновления статистики: {e}")
    
    def get_tasks(self, status: str = None) -> List[Dict]:
        """Получение списка задач"""
        try:
            cursor = self.connection.cursor()
            
            if status:
                cursor.execute('SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC', (status,))
            else:
                cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
            
            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                # Парсим JSON поля
                task['keywords'] = json.loads(task['keywords'])
                task['minus_words'] = json.loads(task['minus_words'])
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            self.log_error(f"Ошибка получения задач: {e}")
            return []
    
    def get_task_posts(self, task_id: int, limit: int = None) -> List[Dict]:
        """Получение постов задачи"""
        try:
            cursor = self.connection.cursor()
            
            if limit:
                cursor.execute('''
                    SELECT * FROM posts 
                    WHERE task_id = ? 
                    ORDER BY date DESC 
                    LIMIT ?
                ''', (task_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM posts 
                    WHERE task_id = ? 
                    ORDER BY date DESC
                ''', (task_id,))
            
            posts = []
            for row in cursor.fetchall():
                post = dict(row)
                # Парсим JSON поля
                post['keywords_matched'] = json.loads(post['keywords_matched'] or '[]')
                posts.append(post)
            
            return posts
            
        except Exception as e:
            self.log_error(f"Ошибка получения постов: {e}")
            return []
    
    def export_task_to_csv(self, task_id: int, output_path: str) -> bool:
        """Экспорт задачи в CSV"""
        try:
            # Получаем данные задачи
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            task = cursor.fetchone()
            
            if not task:
                self.log_error(f"Задача {task_id} не найдена")
                return False
            
            # Получаем посты
            posts = self.get_task_posts(task_id)
            
            if not posts:
                self.log_warning(f"Нет постов для задачи {task_id}")
                return False
            
            # Конвертируем в формат для CSV
            csv_data = []
            for post in posts:
                csv_row = {
                    'link': post['link'],
                    'text': post['text'],
                    'type': 'Пост',
                    'author': '',
                    'author_link': '',
                    'date': datetime.fromtimestamp(post['date']).strftime("%H:%M %d.%m.%Y") if post['date'] else '',
                    'likes': post['likes'],
                    'comments': post['comments'],
                    'reposts': post['reposts'],
                    'views': post['views'],
                    'keywords_matched': ', '.join(post['keywords_matched'])
                }
                csv_data.append(csv_row)
            
            # Сохраняем в CSV
            df = pd.DataFrame(csv_data)
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            self.log_info(f"Экспортировано {len(csv_data)} постов в {output_path}")
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка экспорта в CSV: {e}")
            return False
    
    def get_task_statistics(self, task_id: int) -> Dict:
        """Получение статистики задачи"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            task = cursor.fetchone()
            
            if not task:
                return {}
            
            return {
                'task_id': task['id'],
                'task_name': task['task_name'],
                'status': task['status'],
                'total_posts': task['total_posts'],
                'total_likes': task['total_likes'],
                'total_comments': task['total_comments'],
                'total_reposts': task['total_reposts'],
                'total_views': task['total_views'],
                'total_SI': task['total_SI'],
                'created_at': task['created_at']
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики: {e}")
            return {}
    
    def update_task_status(self, task_id: int, status: str):
        """Обновление статуса задачи"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
            self.connection.commit()
            
            self.log_info(f"Статус задачи {task_id} обновлен на '{status}'")
            
        except Exception as e:
            self.log_error(f"Ошибка обновления статуса: {e}")
    
    def find_duplicates(self, task_id: int = None) -> List[List[Dict]]:
        """Поиск дубликатов в постах"""
        try:
            cursor = self.connection.cursor()
            
            if task_id:
                cursor.execute('''
                    SELECT link_hash, COUNT(*) as count, GROUP_CONCAT(id) as post_ids
                    FROM posts 
                    WHERE task_id = ? 
                    GROUP BY link_hash 
                    HAVING COUNT(*) > 1
                ''', (task_id,))
            else:
                cursor.execute('''
                    SELECT link_hash, COUNT(*) as count, GROUP_CONCAT(id) as post_ids
                    FROM posts 
                    GROUP BY link_hash 
                    HAVING COUNT(*) > 1
                ''')
            
            duplicates = []
            for row in cursor.fetchall():
                post_ids = [int(pid) for pid in row['post_ids'].split(',')]
                duplicate_posts = []
                
                for post_id in post_ids:
                    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
                    post = cursor.fetchone()
                    if post:
                        duplicate_posts.append(dict(post))
                
                duplicates.append(duplicate_posts)
            
            return duplicates
            
        except Exception as e:
            self.log_error(f"Ошибка поиска дубликатов: {e}")
            return []
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Database")
        
        if self.connection:
            self.connection.close()
        
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
            
            self.log_info(f"Загружено {len(results)} записей из CSV: {filepath}")
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
            
            self.log_info(f"Загружено {len(results)} записей из JSON: {filepath}")
            return results
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки из JSON: {str(e)}")
            raise
    
    def get_available_files(self, extension: str = None) -> List[str]:
        """Получает список доступных файлов"""
        try:
            files = []
            for file in os.listdir(self.data_dir):
                if extension:
                    if file.endswith(extension):
                        files.append(file)
                else:
                    files.append(file)
            
            return sorted(files)
            
        except Exception as e:
            self.log_error(f"Ошибка получения списка файлов: {str(e)}")
            return []
    
    def delete_file(self, filename: str) -> bool:
        """Удаляет файл"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                self.log_info(f"Файл удален: {filepath}")
                return True
            else:
                self.log_warning(f"Файл не найден: {filepath}")
                return False
                
        except Exception as e:
            self.log_error(f"Ошибка удаления файла: {str(e)}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о файле"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            stat = os.stat(filepath)
            
            return {
                "filename": filename,
                "filepath": filepath,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime)
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения информации о файле: {str(e)}")
            return None
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = self.get_required_config_keys()
        
        for key in required_keys:
            if key not in self.config:
                self.log_error(f"Отсутствует обязательный ключ конфигурации: {key}")
                return False
        
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["data_dir", "db_path"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику плагина"""
        try:
            files = self.get_available_files()
            
            total_size = 0
            for filename in files:
                file_info = self.get_file_info(filename)
                if file_info:
                    total_size += file_info["size"]
            
            return {
                "total_files": len(files),
                "total_size": total_size,
                "data_directory": self.data_dir,
                "database_path": self.db_path
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики: {str(e)}")
            return {} 