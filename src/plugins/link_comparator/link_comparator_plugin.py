import pandas as pd
import re
import os
from typing import Set, List, Dict, Any
from src.plugins.base_plugin import BasePlugin


class LinkComparatorPlugin(BasePlugin):
    """Плагин для сравнения ссылок между двумя таблицами"""
    
    def __init__(self):
        super().__init__("LinkComparatorPlugin", "1.0.0")
        self.table1_data = None
        self.table2_data = None
        self.table1_path = None
        self.table2_path = None
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация плагина"""
        try:
            self.logger.info("Инициализация LinkComparatorPlugin")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации: {str(e)}")
            return False
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение основной логики плагина"""
        try:
            operation = data.get('operation', '')
            
            if operation == 'load_table1':
                file_path = data.get('file_path')
                if file_path is None:
                    return {'success': False, 'error': 'file_path не указан'}
                success = self.load_table1(str(file_path))
                return {'success': success}
                
            elif operation == 'load_table2':
                file_path = data.get('file_path')
                if file_path is None:
                    return {'success': False, 'error': 'file_path не указан'}
                success = self.load_table2(str(file_path))
                return {'success': success}
                
            elif operation == 'get_columns':
                table_num = data.get('table_num', 1)
                columns = self.get_table_columns(table_num)
                return {'columns': columns}
                
            elif operation == 'compare_links':
                table1_column = data.get('table1_column', '')
                table2_column = data.get('table2_column', '')
                result = self.compare_links(table1_column, table2_column)
                return result
                
            elif operation == 'save_results':
                missing_links = data.get('missing_links', [])
                file_path = data.get('file_path', '')
                success = self.save_results_to_file(missing_links, file_path)
                return {'success': success}
                
            elif operation == 'get_table_info':
                table_num = data.get('table_num', 1)
                info = self.get_table_info(table_num)
                return info
                
            else:
                return {'success': False, 'error': f'Неизвестная операция: {operation}'}
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def load_file(self, file_path: str) -> pd.DataFrame:
        """Загружает файл Excel или CSV"""
        if file_path.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        else:
            raise ValueError("Неподдерживаемый формат файла")
    
    def load_table1(self, file_path: str) -> bool:
        """Загружает первую таблицу"""
        try:
            self.table1_data = self.load_file(file_path)
            self.table1_path = file_path
            return True
        except Exception as e:
            print(f"Ошибка загрузки файла: {str(e)}")
            return False
    
    def load_table2(self, file_path: str) -> bool:
        """Загружает вторую таблицу"""
        try:
            self.table2_data = self.load_file(file_path)
            self.table2_path = file_path
            return True
        except Exception as e:
            print(f"Ошибка загрузки файла: {str(e)}")
            return False
    
    def get_table_columns(self, table_num: int) -> List[str]:
        """Возвращает список столбцов для таблицы"""
        if table_num == 1 and self.table1_data is not None:
            return ["Все столбцы"] + list(self.table1_data.columns)
        elif table_num == 2 and self.table2_data is not None:
            return ["Все столбцы"] + list(self.table2_data.columns)
        return []
    
    def is_ready(self) -> bool:
        """Проверяет, готовы ли обе таблицы для сравнения"""
        return self.table1_data is not None and self.table2_data is not None
    
    def compare_links(self, table1_column: str, table2_column: str) -> Dict[str, Any]:
        """Сравнивает ссылки между двумя таблицами"""
        if not self.is_ready():
            return {
                "success": False,
                "error": "Пожалуйста, загрузите обе таблицы",
                "missing_links": [],
                "stats": "Ошибка: таблицы не загружены"
            }
        
        # Проверяем, что данные не None
        if self.table1_data is None or self.table2_data is None:
            return {
                "success": False,
                "error": "Данные таблиц не загружены",
                "missing_links": [],
                "stats": "Ошибка: данные таблиц не загружены"
            }
        
        # Получаем ссылки из обеих таблиц
        links1 = self.extract_links(self.table1_data, table1_column)
        links2 = self.extract_links(self.table2_data, table2_column)
        
        # Находим ссылки из таблицы 2, которых нет в таблице 1
        missing_links = links2 - links1
        
        # Формируем статистику
        stats_text = f"Найдено {len(missing_links)} ссылок из таблицы 2, которых нет в таблице 1"
        
        return {
            "success": True,
            "missing_links": sorted(list(missing_links)),
            "stats": stats_text,
            "total_links1": len(links1),
            "total_links2": len(links2),
            "missing_count": len(missing_links)
        }
    
    def extract_links(self, df: pd.DataFrame, selected_column: str) -> Set[str]:
        """Извлекает ссылки из DataFrame с учетом выбранного столбца"""
        links = set()
        
        if selected_column == "Все столбцы":
            # Проходим по всем столбцам
            for column in df.columns:
                for value in df[column].dropna():
                    value_str = str(value).strip()
                    found_links = self.find_links_in_text(value_str)
                    links.update(found_links)
        else:
            # Проходим только по выбранному столбцу
            if selected_column in df.columns:
                for value in df[selected_column].dropna():
                    value_str = str(value).strip()
                    found_links = self.find_links_in_text(value_str)
                    links.update(found_links)
        
        return links
    
    def find_links_in_text(self, text: str) -> Set[str]:
        """Находит все ссылки в тексте"""
        links = set()
        
        # Паттерны для поиска ссылок
        patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',  # http:// или https:// ссылки
            r'www\.[^\s<>"{}|\\^`\[\]]+',      # www. ссылки
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # email адреса
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Очищаем ссылку от лишних символов
                clean_link = match.strip('.,;:!?()[]{}"\'').rstrip('/')
                if self.is_valid_link(clean_link):
                    links.add(clean_link)
        
        return links
    
    def is_valid_link(self, text: str) -> bool:
        """Проверяет, является ли текст валидной ссылкой"""
        text_lower = text.lower()
        
        # Проверяем различные типы ссылок
        if (text_lower.startswith('http://') or 
            text_lower.startswith('https://') or 
            text_lower.startswith('www.')):
            return True
        
        # Проверяем email адреса
        if '@' in text and '.' in text.split('@')[1]:
            return True
        
        # Проверяем домены
        if any(domain in text_lower for domain in ['.com', '.ru', '.org', '.net', '.edu', '.gov']):
            return True
        
        return False
    
    def is_link(self, text: str) -> bool:
        """Проверяет, является ли текст ссылкой (устаревший метод)"""
        text = text.lower()
        return (text.startswith('http://') or 
                text.startswith('https://') or 
                text.startswith('www.') or
                '.com' in text or
                '.ru' in text or
                '.org' in text or
                '.net' in text)
    
    def save_results_to_file(self, missing_links: List[str], file_path: str) -> bool:
        """Сохраняет результаты в файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Ссылки из таблицы 2, которых нет в таблице 1:\n")
                f.write("=" * 50 + "\n\n")
                
                for link in missing_links:
                    f.write(f"{link}\n")
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения файла: {str(e)}")
            return False
    
    def get_table_info(self, table_num: int) -> Dict[str, Any]:
        """Возвращает информацию о загруженной таблице"""
        if table_num == 1 and self.table1_data is not None:
            return {
                "loaded": True,
                "filename": os.path.basename(self.table1_path) if self.table1_path else "Неизвестно",
                "rows": len(self.table1_data),
                "columns": len(self.table1_data.columns),
                "columns_list": list(self.table1_data.columns)
            }
        elif table_num == 2 and self.table2_data is not None:
            return {
                "loaded": True,
                "filename": os.path.basename(self.table2_path) if self.table2_path else "Неизвестно",
                "rows": len(self.table2_data),
                "columns": len(self.table2_data.columns),
                "columns_list": list(self.table2_data.columns)
            }
        else:
            return {
                "loaded": False,
                "filename": "Не загружено",
                "rows": 0,
                "columns": 0,
                "columns_list": []
            }
    
    def clear_data(self):
        """Очищает загруженные данные"""
        self.table1_data = None
        self.table2_data = None
        self.table1_path = None
        self.table2_path = None 