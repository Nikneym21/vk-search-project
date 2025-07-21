import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Any, Tuple
from src.plugins.base_plugin import BasePlugin
from datetime import datetime


class GoogleSheetsPlugin(BasePlugin):
    """Плагин для работы с Google Sheets"""
    
    def __init__(self):
        super().__init__("GoogleSheetsPlugin", "1.0.0")
        self.client = None
        self.spreadsheet = None
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация плагина"""
        try:
            self.logger.info("Инициализация GoogleSheetsPlugin")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации: {str(e)}")
            return False
    
    def initialize_connection(self, service_account_path: str = 'service_account.json') -> bool:
        """Инициализирует подключение к Google Sheets API"""
        try:
            if not os.path.exists(service_account_path):
                raise FileNotFoundError(f"Файл {service_account_path} не найден")
            
            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_path, scope)
            self.client = gspread.authorize(credentials)
            return True
        except Exception as e:
            print(f"Ошибка инициализации Google Sheets: {e}")
            return False
    
    def open_spreadsheet(self, spreadsheet_url: str) -> bool:
        """Открывает таблицу по URL"""
        try:
            if not self.client:
                raise Exception("Клиент Google Sheets не инициализирован")
            
            self.spreadsheet = self.client.open_by_url(spreadsheet_url)
            return True
        except Exception as e:
            print(f"Ошибка открытия таблицы: {e}")
            return False
    
    def get_sheets_list(self) -> List[str]:
        """Получает список всех листов в таблице"""
        try:
            if not self.spreadsheet:
                return []
            
            worksheets = self.spreadsheet.worksheets()
            return [worksheet.title for worksheet in worksheets]
        except Exception as e:
            print(f"Ошибка получения списка листов: {e}")
            return []
    
    def sort_sheets_by_date(self, sheet_names: List[str]) -> List[str]:
        """Сортирует листы по датам в названиях"""
        def parse_date(date_str):
            """Парсит дату из строки"""
            try:
                # Пытаемся найти дату в формате DD.MM.YYYY или DD-MM-YYYY
                import re
                date_pattern = r'(\d{1,2})[.-](\d{1,2})[.-](\d{4})'
                match = re.search(date_pattern, date_str)
                if match:
                    day, month, year = match.groups()
                    return datetime(int(year), int(month), int(day))
                return None
            except:
                return None
        
        # Сортируем листы по датам
        dated_sheets = []
        undated_sheets = []
        
        for sheet_name in sheet_names:
            date = parse_date(sheet_name)
            if date:
                dated_sheets.append((sheet_name, date))
            else:
                undated_sheets.append(sheet_name)
        
        # Сортируем листы с датами
        dated_sheets.sort(key=lambda x: x[1])
        sorted_sheets = [sheet[0] for sheet in dated_sheets]
        
        # Добавляем листы без дат в конец
        sorted_sheets.extend(undated_sheets)
        
        return sorted_sheets
    
    def load_data_from_sheets(self, sheet_from: str, sheet_to: str, cell_range: str) -> Tuple[List[str], List[str]]:
        """Загружает данные из указанного диапазона листов"""
        try:
            if not self.spreadsheet:
                raise Exception("Таблица не открыта")
            
            # Получаем список всех листов
            worksheets = self.spreadsheet.worksheets()
            sheet_names = [worksheet.title for worksheet in worksheets]
            
            # Сортируем листы по датам
            sorted_sheets = self.sort_sheets_by_date(sheet_names)
            
            # Находим индексы выбранных листов
            try:
                from_index = sorted_sheets.index(sheet_from)
                to_index = sorted_sheets.index(sheet_to)
            except ValueError as e:
                raise Exception(f"Лист '{sheet_from}' или '{sheet_to}' не найден в таблице")
            
            # Определяем диапазон листов для обработки
            if from_index <= to_index:
                sheets_to_process = sorted_sheets[from_index:to_index + 1]
            else:
                sheets_to_process = sorted_sheets[to_index:from_index + 1]
            
            all_texts = []
            processed_sheets = []
            
            # Обрабатываем каждый лист в диапазоне
            for sheet_name in sheets_to_process:
                try:
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                    
                    # Получаем данные из указанного диапазона
                    try:
                        data = worksheet.get(cell_range)
                    except Exception as e:
                        print(f"Ошибка получения данных из листа '{sheet_name}': {e}")
                        continue
                    
                    if not data:
                        continue
                    
                    # Создаем DataFrame
                    df = pd.DataFrame(data)
                    
                    # Если первая строка содержит заголовки, используем их
                    if len(df) > 0:
                        # Проверяем, есть ли заголовки (первая строка содержит текст)
                        first_row_has_text = any(str(cell).strip() for cell in df.iloc[0] if pd.notna(cell))
                        
                        if first_row_has_text:
                            # Используем первую строку как заголовки
                            df.columns = df.iloc[0]
                            df = df.iloc[1:]  # Удаляем первую строку
                        else:
                            # Создаем заголовки по умолчанию
                            df.columns = [f'Column_{i}' for i in range(len(df.columns))]
                    
                    # Удаляем пустые строки и столбцы
                    df = df.dropna(how='all')  # Удаляем строки, где все ячейки пустые
                    df = df.dropna(axis=1, how='all')  # Удаляем столбцы, где все ячейки пустые
                    
                    # Ищем колонки с текстом публикаций
                    text_columns = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(keyword in col_str for keyword in ['текст', 'содержание', 'описание', 'content', 'text', 'сообщение', 'пост']):
                            text_columns.append(col)
                    
                    # Если не найдены колонки с ключевыми словами, используем все колонки
                    if not text_columns:
                        text_columns = list(df.columns)
                    
                    # Очищаем эмодзи, коды эмодзи, хэштеги из найденных колонок и удаляем пустые ячейки
                    sheet_texts = []
                    for col in text_columns:
                        # Получаем значения из колонки, удаляем NaN и пустые строки
                        column_values = df[col].dropna()
                        column_values = column_values[column_values.astype(str).str.strip() != '']
                        
                        # Очищаем эмодзи, коды эмодзи, хэштеги и добавляем в список
                        for value in column_values:
                            cleaned_text = self.clean_text_completely(str(value))
                            if cleaned_text:  # Проверяем, что после очистки текст не пустой
                                sheet_texts.append(cleaned_text)
                    
                    if sheet_texts:
                        all_texts.extend(sheet_texts)
                        processed_sheets.append(sheet_name)
                    
                except Exception as e:
                    print(f"Ошибка обработки листа '{sheet_name}': {e}")
                    continue
            
            return all_texts, processed_sheets
            
        except Exception as e:
            print(f"Ошибка загрузки данных из Google Sheets: {e}")
            return [], []
    
    def clean_text_completely(self, text: str) -> str:
        """Полностью очищает текст от кодов эмодзи, хэштегов и лишних символов"""
        import re
        
        try:
            import emoji
            # Сначала удаляем эмодзи
            cleaned_text = emoji.demojize(text)
        except ImportError:
            cleaned_text = text
        
        # Удаляем коды эмодзи в формате :code:
        cleaned_text = re.sub(r':[a-zA-Z_]+:', '', cleaned_text)
        
        # Удаляем хэштеги (#слово)
        cleaned_text = re.sub(r'#\w+', '', cleaned_text)
        
        # Удаляем множественные пробелы
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # Удаляем пробелы в начале и конце
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Выполняет основную логику плагина"""
        try:
            spreadsheet_url = kwargs.get('spreadsheet_url')
            sheet_from = kwargs.get('sheet_from')
            sheet_to = kwargs.get('sheet_to')
            cell_range = kwargs.get('cell_range')
            
            if not all([spreadsheet_url, sheet_from, sheet_to, cell_range]):
                return {
                    'success': False,
                    'error': 'Не все параметры указаны'
                }
            
            # Проверяем типы
            if not isinstance(spreadsheet_url, str) or not isinstance(sheet_from, str) or not isinstance(sheet_to, str) or not isinstance(cell_range, str):
                return {
                    'success': False,
                    'error': 'Неверные типы параметров'
                }
            
            # Инициализируем подключение
            if not self.initialize_connection():
                return {
                    'success': False,
                    'error': 'Ошибка инициализации Google Sheets'
                }
            
            # Открываем таблицу
            if not self.open_spreadsheet(str(spreadsheet_url)):
                return {
                    'success': False,
                    'error': 'Ошибка открытия таблицы'
                }
            
            # Загружаем данные
            texts, processed_sheets = self.load_data_from_sheets(str(sheet_from), str(sheet_to), str(cell_range))
            
            return {
                'success': True,
                'texts': texts,
                'processed_sheets': processed_sheets,
                'total_texts': len(texts),
                'total_sheets': len(processed_sheets)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup(self):
        """Очищает ресурсы"""
        self.client = None
        self.spreadsheet = None 