#!/usr/bin/env python3
"""
Юнит-тест для FilterPlugin
Проверяет функциональность плагина локальной фильтрации по ключевым фразам
"""

import unittest
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.plugins.post_processor.filter.filter_plugin import FilterPlugin

class TestFilterPlugin(unittest.TestCase):
    """Тесты для FilterPlugin"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.plugin = FilterPlugin()
        self.plugin.initialize()
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.plugin.shutdown()
    
    def test_plugin_initialization(self):
        """Тест инициализации плагина"""
        self.assertEqual(self.plugin.name, "FilterPlugin")
        self.assertTrue(self.plugin.is_enabled())
    
    def test_filter_unique_posts(self):
        """Тест фильтрации уникальных постов"""
        # Создаем тестовые посты с дубликатами
        posts = [
            {"owner_id": 1, "id": 100, "text": "post 1"},
            {"owner_id": 1, "id": 100, "text": "post 1 duplicate"},  # Дубликат
            {"owner_id": 2, "id": 200, "text": "post 2"},
            {"owner_id": 1, "id": 101, "text": "post 3"},
        ]
        
        unique_posts = self.plugin.filter_unique_posts(posts)
        
        # Должно остаться 3 уникальных поста (убрать дубликат)
        self.assertEqual(len(unique_posts), 3)
        
        # Проверяем, что дубликат убран
        owner_ids = [post["owner_id"] for post in unique_posts]
        post_ids = [post["id"] for post in unique_posts]
        
        # Проверяем, что комбинация (owner_id, id) уникальна
        unique_keys = set(zip(owner_ids, post_ids))
        self.assertEqual(len(unique_keys), 3)
    
    def test_filter_by_keyword(self):
        """Тест фильтрации по ключевому слову"""
        posts = [
            {'text': 'Тестовый пост с ключевым словом'},
            {'text': 'Обычный пост без ключевого слова'},
            {'text': 'Еще один пост с ключевым словом'}
        ]
        
        keywords = ['ключевым']
        result = self.plugin.filter_posts_by_keyword(posts, 'ключевым', exact_match=True)
        
        self.assertEqual(len(result), 2)
        self.assertIn('ключевым', result[0]['text'])
        self.assertIn('ключевым', result[1]['text'])
    
    def test_filter_posts_by_keyword_with_text_cleaning(self):
        """Тест фильтрации с очисткой текста"""
        posts = [
            {"text": "Даже в боевых условиях человек остаётся человеком. 🎯 #война", "owner_id": 1, "id": 100},
            {"text": "Лис передает всем доброе утро! ☀️ #утро", "owner_id": 2, "id": 200},
            {"text": "Привет родной Бурятии от штурмовиков танковой бригады с Южно-Донецкого направления 🇷🇺", "owner_id": 3, "id": 300},
            {"text": "Обычный пост без ключевых слов", "owner_id": 4, "id": 400},
        ]
        
        # Фильтрация по первому ключу с очисткой
        filtered = self.plugin.filter_posts_by_keyword_with_text_cleaning(
            posts, "Даже в боевых условиях человек остаётся человеком", exact_match=True
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["owner_id"], 1)
        
        # Фильтрация по второму ключу с очисткой
        filtered = self.plugin.filter_posts_by_keyword_with_text_cleaning(
            posts, "Лис передает всем доброе утро", exact_match=True
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["owner_id"], 2)
        
        # Фильтрация по третьему ключу с очисткой
        filtered = self.plugin.filter_posts_by_keyword_with_text_cleaning(
            posts, "Привет родной Бурятии от штурмовиков танковой бригады с Южно-Донецкого направления", exact_match=True
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["owner_id"], 3)
    
    def test_filter_posts_by_multiple_keywords(self):
        """Тест фильтрации по нескольким ключевым словам"""
        posts = [
            {"text": "Даже в боевых условиях человек остаётся человеком", "owner_id": 1, "id": 100},
            {"text": "Лис передает всем доброе утро", "owner_id": 2, "id": 200},
            {"text": "Привет родной Бурятии", "owner_id": 3, "id": 300},
            {"text": "Обычный пост без ключевых слов", "owner_id": 4, "id": 400},
        ]
        
        keywords = ["Даже в боевых условиях", "Лис передает", "Привет родной"]
        
        # Фильтрация по нескольким ключам
        filtered = self.plugin.filter_posts_by_multiple_keywords(posts, keywords, exact_match=True, use_text_cleaning=True)
        self.assertEqual(len(filtered), 3)
        
        # Проверяем, что найдены все посты с ключевыми словами
        owner_ids = [post["owner_id"] for post in filtered]
        self.assertIn(1, owner_ids)
        self.assertIn(2, owner_ids)
        self.assertIn(3, owner_ids)
        self.assertNotIn(4, owner_ids)  # Пост без ключевых слов не должен быть включен
    
    def test_filter_posts_comprehensive(self):
        """Тест комплексной фильтрации по ключевым фразам"""
        posts = [
            {"text": "Даже в боевых условиях человек остаётся человеком", "owner_id": 1, "id": 100},
            {"text": "Даже в боевых условиях человек остаётся человеком", "owner_id": 1, "id": 100},  # Дубликат
            {"text": "Лис передает всем доброе утро", "owner_id": 2, "id": 200},
            {"text": "Привет родной Бурятии", "owner_id": 3, "id": 300},
            {"text": "Обычный пост без ключевых слов", "owner_id": 4, "id": 400},
        ]
        
        keywords = ["Даже в боевых условиях", "Лис передает"]
        
        # Комплексная фильтрация
        filtered = self.plugin.filter_posts_comprehensive(
            posts=posts,
            keywords=keywords,
            exact_match=True,
            use_text_cleaning=True,
            remove_duplicates=True
        )
        
        # Должно найти 2 поста (с учетом удаления дубликатов)
        self.assertEqual(len(filtered), 2)
        
        # Проверяем, что дубликаты удалены
        owner_ids = [post["owner_id"] for post in filtered]
        self.assertIn(1, owner_ids)
        self.assertIn(2, owner_ids)
        self.assertNotIn(3, owner_ids)  # Не содержит ключевых слов
        self.assertNotIn(4, owner_ids)  # Не содержит ключевых слов
    
    def test_filter_without_keywords(self):
        """Тест фильтрации без ключевых слов (только удаление дубликатов)"""
        posts = [
            {"text": "Пост 1", "owner_id": 1, "id": 100},
            {"text": "Пост 1", "owner_id": 1, "id": 100},  # Дубликат
            {"text": "Пост 2", "owner_id": 2, "id": 200},
        ]
        
        filtered = self.plugin.filter_posts_comprehensive(
            posts=posts,
            keywords=None,  # Без ключевых слов
            remove_duplicates=True
        )
        
        # Должно остаться 2 поста (убрать дубликат)
        self.assertEqual(len(filtered), 2)
    
    def test_filter_without_text_cleaning(self):
        """Тест фильтрации без очистки текста"""
        posts = [
            {"text": "Даже в боевых условиях человек остаётся человеком. 🎯 #война", "owner_id": 1, "id": 100},
            {"text": "Лис передает всем доброе утро! ☀️ #утро", "owner_id": 2, "id": 200},
        ]
        
        keywords = ["Даже в боевых условиях человек остаётся человеком"]
        
        # Фильтрация без очистки текста
        filtered = self.plugin.filter_posts_comprehensive(
            posts=posts,
            keywords=keywords,
            exact_match=True,
            use_text_cleaning=False,
            remove_duplicates=True
        )
        
        # Должен найти 1 пост (без очистки текста эмодзи и хештеги остаются)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["owner_id"], 1)


if __name__ == "__main__":
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFilterPlugin)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Выводим результат
    if result.wasSuccessful():
        print("\n✅ Все тесты прошли успешно!")
    else:
        print(f"\n❌ Тесты завершились с ошибками: {len(result.failures)} failures, {len(result.errors)} errors")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(f"  {failure[1]}")
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(f"  {error[1]}")
    
    sys.exit(0 if result.wasSuccessful() else 1) 