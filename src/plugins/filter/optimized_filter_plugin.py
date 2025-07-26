#!/usr/bin/env python3
"""
Оптимизированный плагин фильтрации для работы с большими объемами данных
"""

import hashlib
import json
import gzip
import sqlite3
from typing import List, Dict, Set, Tuple
from datetime import datetime
import pandas as pd
from src.plugins.base_plugin import BasePlugin

class OptimizedFilterPlugin(BasePlugin):
    """Оптимизированный плагин фильтрации с поддержкой больших объемов данных"""
    
    def __init__(self):
        super().__init__()
        self.name = "OptimizedFilterPlugin"
        self.db_path = "data/filter_cache.db"
        self.cache = {}
        self.text_hashes = set()
        
    def initialize(self):
        """Инициализация плагина"""
        self.log_info("Инициализация оптимизированного плагина фильтрации")
        
        # Создаем базу данных для кэширования
        self._init_database()
        
        # Инициализируем кэш
        self._load_cache()
        
        self.log_info("Оптимизированный плагин фильтрации инициализирован")
        return True
    
    def _init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица постов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                text_hash TEXT,
                text TEXT,
                date INTEGER,
                likes INTEGER,
                comments INTEGER,
                reposts INTEGER,
                views INTEGER,
                keywords_matched TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица ключевых слов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                post_id TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        ''')
        
        # Индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_text_hash ON posts(text_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords ON keywords(keyword)')
        
        conn.commit()
        conn.close()
    
    def _load_cache(self):
        """Загрузка кэша из базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Загружаем хеши текстов
            cursor.execute('SELECT text_hash FROM posts')
            self.text_hashes = {row[0] for row in cursor.fetchall()}
            
            conn.close()
            self.log_info(f"Загружено {len(self.text_hashes)} хешей в кэш")
            
        except Exception as e:
            self.log_warning(f"Ошибка загрузки кэша: {e}")
    
    def _get_text_hash(self, text: str) -> str:
        """Получение хеша текста"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _is_duplicate_text(self, text: str) -> bool:
        """Быстрая проверка дубликата текста"""
        text_hash = self._get_text_hash(text)
        return text_hash in self.text_hashes
    
    def filter_unique_posts_fast(self, posts: List[Dict]) -> List[Dict]:
        """Быстрая фильтрация уникальных постов"""
        if not posts:
            return []
        
        unique_posts = []
        seen_hashes = set()
        
        for post in posts:
            text = post.get('text', '')
            if not text:
                continue
                
            text_hash = self._get_text_hash(text)
            
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_posts.append(post)
        
        self.log_info(f"Быстрая фильтрация: {len(posts)} -> {len(unique_posts)}")
        return unique_posts
    
    def filter_posts_by_keywords_fast(self, posts: List[Dict], keywords: List[str], 
                                    exact_match: bool = False) -> List[Dict]:
        """Быстрая фильтрация по ключевым словам"""
        if not posts or not keywords:
            return posts
        
        filtered_posts = []
        
        for post in posts:
            text = post.get('text', '').lower()
            if not text:
                continue
            
            # Проверяем соответствие хотя бы одному ключевому слову
            matched = False
            matched_keywords = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                if exact_match:
                    # Точное совпадение
                    if f' {keyword_lower} ' in f' {text} ':
                        matched = True
                        matched_keywords.append(keyword)
                else:
                    # Частичное совпадение
                    if keyword_lower in text:
                        matched = True
                        matched_keywords.append(keyword)
            
            if matched:
                # Добавляем информацию о найденных ключевых словах
                post['keywords_matched'] = matched_keywords
                filtered_posts.append(post)
        
        self.log_info(f"Фильтрация по ключам: {len(posts)} -> {len(filtered_posts)}")
        return filtered_posts
    
    def save_lightweight_results(self, posts: List[Dict], filename: str):
        """Сохранение результатов в легком формате"""
        lightweight_posts = []
        
        for post in posts:
            lightweight_post = {
                'id': f"wall{post.get('owner_id', 0)}_{post.get('id', 0)}",
                'text': post.get('text', '')[:200] + '...' if len(post.get('text', '')) > 200 else post.get('text', ''),
                'date': post.get('date', 0),
                'stats': {
                    'likes': post.get('likes', {}).get('count', 0) if isinstance(post.get('likes'), dict) else post.get('likes', 0),
                    'comments': post.get('comments', {}).get('count', 0) if isinstance(post.get('comments'), dict) else post.get('comments', 0),
                    'reposts': post.get('reposts', {}).get('count', 0) if isinstance(post.get('reposts'), dict) else post.get('reposts', 0),
                    'views': post.get('views', {}).get('count', 0) if isinstance(post.get('views'), dict) else post.get('views', 0)
                },
                'keywords_matched': post.get('keywords_matched', [])
            }
            lightweight_posts.append(lightweight_post)
        
        # Сохраняем в сжатом JSON
        output_path = f"data/results/{filename}.json.gz"
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            json.dump(lightweight_posts, f, ensure_ascii=False, indent=2)
        
        self.log_info(f"Сохранено {len(lightweight_posts)} постов в {output_path}")
        return output_path
    
    def export_to_full_csv(self, lightweight_file: str, output_csv: str):
        """Экспорт легких результатов в полный CSV"""
        try:
            # Загружаем легкие данные
            with gzip.open(lightweight_file, 'rt', encoding='utf-8') as f:
                lightweight_posts = json.load(f)
            
            # Конвертируем в полный формат
            full_data = []
            for post in lightweight_posts:
                full_row = {
                    'link': f"https://vk.com/{post['id']}",
                    'text': post['text'],
                    'type': 'Пост',
                    'author': '',
                    'author_link': '',
                    'date': datetime.fromtimestamp(post['date']).strftime("%H:%M %d.%m.%Y") if post['date'] else '',
                    'likes': post['stats']['likes'],
                    'comments': post['stats']['comments'],
                    'reposts': post['stats']['reposts'],
                    'views': post['stats']['views'],
                    'keywords_matched': ', '.join(post['keywords_matched'])
                }
                full_data.append(full_row)
            
            # Сохраняем в CSV
            df = pd.DataFrame(full_data)
            df.to_csv(output_csv, index=False, encoding='utf-8')
            
            self.log_info(f"Экспортировано {len(full_data)} записей в {output_csv}")
            return output_csv
            
        except Exception as e:
            self.log_error(f"Ошибка экспорта в CSV: {e}")
            return None
    
    def get_statistics(self, posts: List[Dict]) -> Dict:
        """Получение статистики по постам"""
        if not posts:
            return {
                'total_posts': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_reposts': 0,
                'total_views': 0,
                'total_SI': 0
            }
        
        total_likes = sum(
            post.get('likes', {}).get('count', 0) if isinstance(post.get('likes'), dict) 
            else post.get('likes', 0) for post in posts
        )
        total_comments = sum(
            post.get('comments', {}).get('count', 0) if isinstance(post.get('comments'), dict) 
            else post.get('comments', 0) for post in posts
        )
        total_reposts = sum(
            post.get('reposts', {}).get('count', 0) if isinstance(post.get('reposts'), dict) 
            else post.get('reposts', 0) for post in posts
        )
        total_views = sum(
            post.get('views', {}).get('count', 0) if isinstance(post.get('views'), dict) 
            else post.get('views', 0) for post in posts
        )
        
        return {
            'total_posts': len(posts),
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_reposts': total_reposts,
            'total_views': total_views,
            'total_SI': total_likes + total_comments + total_reposts
        }
    
    def find_duplicates(self, posts: List[Dict]) -> List[List[Dict]]:
        """Поиск дубликатов в постах"""
        if not posts:
            return []
        
        # Группируем по хешу текста
        text_groups = {}
        
        for post in posts:
            text = post.get('text', '')
            if not text:
                continue
                
            text_hash = self._get_text_hash(text)
            
            if text_hash not in text_groups:
                text_groups[text_hash] = []
            text_groups[text_hash].append(post)
        
        # Возвращаем только группы с дубликатами
        duplicates = [group for group in text_groups.values() if len(group) > 1]
        
        self.log_info(f"Найдено {len(duplicates)} групп дубликатов")
        return duplicates
    
    def shutdown(self):
        """Завершение работы плагина"""
        self.log_info("Завершение работы оптимизированного плагина фильтрации")
        # Очищаем кэш
        self.cache.clear()
        self.text_hashes.clear() 