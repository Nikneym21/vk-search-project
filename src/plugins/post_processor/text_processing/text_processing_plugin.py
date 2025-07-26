"""
Плагин для обработки текста
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin


class TextProcessingPlugin(BasePlugin):
    """Плагин для обработки текста"""
    
    def __init__(self):
        super().__init__()
        self.name = "TextProcessingPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для обработки и очистки текста"
        
        # Конфигурация по умолчанию
        self.config = {
            "remove_emojis": True,
            "remove_hashtags": True,
            "remove_urls": False,
            "remove_mentions": True,
            "normalize_whitespace": True,
            "min_text_length": 3,
            "max_text_length": 10000
        }
    
    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Text Processing")
        
        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return
        
        self.log_info("Плагин Text Processing инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})
    
    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Text Processing")
        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Text Processing завершен")
    
    def clean_text_completely(self, text: str) -> str:
        """Полностью очищает текст от кодов эмодзи, хэштегов и лишних символов"""
        try:
            if not text:
                return ""
            
            cleaned_text = text
            
            # Удаляем эмодзи
            if self.config["remove_emojis"]:
                try:
                    import emoji
                    cleaned_text = emoji.demojize(cleaned_text)
                except ImportError:
                    self.log_warning("Модуль emoji не установлен, эмодзи не будут удалены")
                
                # Удаляем коды эмодзи в формате :code:
                cleaned_text = re.sub(r':[a-zA-Z_]+:', '', cleaned_text)
            
            # Удаляем хэштеги
            if self.config["remove_hashtags"]:
                cleaned_text = re.sub(r'#\w+', '', cleaned_text)
            
            # Удаляем упоминания
            if self.config["remove_mentions"]:
                cleaned_text = re.sub(r'@\w+', '', cleaned_text)
            
            # Удаляем URL
            if self.config["remove_urls"]:
                cleaned_text = re.sub(r'https?://[^\s]+', '', cleaned_text)
                cleaned_text = re.sub(r'www\.[^\s]+', '', cleaned_text)
            
            # Нормализуем пробелы
            if self.config["normalize_whitespace"]:
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                cleaned_text = cleaned_text.strip()
            
            return cleaned_text
            
        except Exception as e:
            self.log_error(f"Ошибка очистки текста: {e}")
            return text
    
    def clean_emojis_from_text(self, text: str) -> str:
        """Очищает эмодзи, коды эмодзи и хэштеги из текста"""
        return self.clean_text_completely(text)
    
    def clean_multiple_texts(self, texts: List[str]) -> List[str]:
        """Очищает список текстов от эмодзи, кодов эмодзи и хэштегов"""
        try:
            cleaned_texts = []
            for text in texts:
                cleaned_text = self.clean_text_completely(text)
                if cleaned_text and len(cleaned_text) >= self.config["min_text_length"]:
                    cleaned_texts.append(cleaned_text)
            
            self.log_info(f"Очищено {len(cleaned_texts)} из {len(texts)} текстов")
            return cleaned_texts
            
        except Exception as e:
            self.log_error(f"Ошибка очистки множественных текстов: {e}")
            return []
    
    def extract_links_from_text(self, text: str) -> List[str]:
        """Извлекает ссылки из текста"""
        try:
            if not text:
                return []
            
            # Паттерны для поиска ссылок
            url_patterns = [
                r'https?://[^\s<>"]+',
                r'www\.[^\s<>"]+',
                r'vk\.com/[^\s<>"]+',
                r't\.me/[^\s<>"]+',
                r'instagram\.com/[^\s<>"]+'
            ]
            
            links = []
            for pattern in url_patterns:
                found_links = re.findall(pattern, text, re.IGNORECASE)
                links.extend(found_links)
            
            # Удаляем дубликаты
            links = list(set(links))
            
            return links
            
        except Exception as e:
            self.log_error(f"Ошибка извлечения ссылок: {e}")
            return []
    
    def extract_hashtags_from_text(self, text: str) -> List[str]:
        """Извлекает хэштеги из текста"""
        try:
            if not text:
                return []
            
            hashtags = re.findall(r'#(\w+)', text)
            return list(set(hashtags))
            
        except Exception as e:
            self.log_error(f"Ошибка извлечения хэштегов: {e}")
            return []
    
    def extract_mentions_from_text(self, text: str) -> List[str]:
        """Извлекает упоминания из текста"""
        try:
            if not text:
                return []
            
            mentions = re.findall(r'@(\w+)', text)
            return list(set(mentions))
            
        except Exception as e:
            self.log_error(f"Ошибка извлечения упоминаний: {e}")
            return []
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Анализирует текст и возвращает статистику"""
        try:
            if not text:
                return {"error": "Пустой текст"}
            
            analysis = {
                "original_length": len(text),
                "cleaned_text": self.clean_text_completely(text),
                "cleaned_length": len(self.clean_text_completely(text)),
                "links": self.extract_links_from_text(text),
                "hashtags": self.extract_hashtags_from_text(text),
                "mentions": self.extract_mentions_from_text(text),
                "word_count": len(text.split()),
                "char_count": len(text),
                "line_count": len(text.split('\n'))
            }
            
            # Подсчитываем эмодзи
            try:
                import emoji
                emoji_count = len(emoji.emoji_list(text))
                analysis["emoji_count"] = emoji_count
            except ImportError:
                analysis["emoji_count"] = 0
            
            return analysis
            
        except Exception as e:
            self.log_error(f"Ошибка анализа текста: {e}")
            return {"error": str(e)}
    
    def process_text_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Обрабатывает пакет текстов"""
        try:
            results = []
            for i, text in enumerate(texts):
                try:
                    analysis = self.analyze_text(text)
                    analysis["index"] = i
                    results.append(analysis)
                except Exception as e:
                    self.log_error(f"Ошибка обработки текста {i}: {e}")
                    results.append({"error": str(e), "index": i})
            
            self.log_info(f"Обработано {len(results)} текстов")
            self.emit_event(EventType.DATA_UPDATED, {
                "operation": "text_processing",
                "processed_count": len(results),
                "total_texts": len(texts)
            })
            
            return results
            
        except Exception as e:
            self.log_error(f"Ошибка пакетной обработки текстов: {e}")
            return []
    
    def validate_text_length(self, text: str) -> bool:
        """Проверяет длину текста"""
        if not text:
            return False
        
        length = len(text)
        return self.config["min_text_length"] <= length <= self.config["max_text_length"]
    
    def get_text_statistics(self, texts: List[str]) -> Dict[str, Any]:
        """Возвращает статистику по текстам"""
        try:
            if not texts:
                return {"error": "Нет текстов для анализа"}
            
            total_length = sum(len(text) for text in texts)
            avg_length = total_length / len(texts) if texts else 0
            
            all_links = []
            all_hashtags = []
            all_mentions = []
            
            for text in texts:
                all_links.extend(self.extract_links_from_text(text))
                all_hashtags.extend(self.extract_hashtags_from_text(text))
                all_mentions.extend(self.extract_mentions_from_text(text))
            
            return {
                "total_texts": len(texts),
                "total_length": total_length,
                "average_length": avg_length,
                "unique_links": len(set(all_links)),
                "unique_hashtags": len(set(all_hashtags)),
                "unique_mentions": len(set(all_mentions)),
                "links_list": list(set(all_links)),
                "hashtags_list": list(set(all_hashtags)),
                "mentions_list": list(set(all_mentions))
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики текстов: {e}")
            return {"error": str(e)}
    
    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = ["min_text_length", "max_text_length"]
        
        for key in required_keys:
            if key not in self.config:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False
        
        # Проверяем логичность параметров
        if self.config["min_text_length"] > self.config["max_text_length"]:
            self.log_error("min_text_length не может быть больше max_text_length")
            return False
        
        return True
    
    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["min_text_length", "max_text_length"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        try:
            return {
                "config": self.config,
                "features": [
                    "text_cleaning",
                    "link_extraction",
                    "hashtag_extraction",
                    "mention_extraction",
                    "text_analysis",
                    "batch_processing"
                ]
            }
            
        except Exception as e:
            self.log_error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)} 