"""
Плагин для работы с Google Sheets
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin


class GoogleSheetsPlugin(BasePlugin):
    """Плагин для работы с Google Sheets"""

    def __init__(self):
        super().__init__()
        self.name = "GoogleSheetsPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для интеграции с Google Sheets"

        # Конфигурация по умолчанию
        self.config = {
            "service_account_path": "config/service_account.json",
            "scopes": ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
            "auto_backup": True,
            "max_rows_per_request": 1000,
        }

        self.client = None
        self.spreadsheet = None

    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Google Sheets")

        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return

        # Проверяем наличие файла сервисного аккаунта
        if not os.path.exists(self.config["service_account_path"]):
            self.log_warning(f"Файл сервисного аккаунта не найден: {self.config['service_account_path']}")
            self.log_info("Плагин будет работать в режиме ограниченной функциональности")

        self.log_info("Плагин Google Sheets инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})

    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Google Sheets")

        if self.client:
            self.client = None

        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Google Sheets завершен")

    def initialize_connection(self, service_account_path: str = None) -> bool:
        """Инициализирует подключение к Google Sheets API"""
        try:
            if service_account_path is None:
                service_account_path = self.config["service_account_path"]

            if not os.path.exists(service_account_path):
                raise FileNotFoundError(f"Файл {service_account_path} не найден")

            scope = self.config["scopes"]
            credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_path, scope)
            self.client = gspread.authorize(credentials)

            self.log_info("Подключение к Google Sheets API установлено")
            return True

        except Exception as e:
            self.log_error(f"Ошибка инициализации Google Sheets: {e}")
            return False

    def open_spreadsheet(self, spreadsheet_url: str) -> bool:
        """Открывает таблицу по URL"""
        try:
            if not self.client:
                if not self.initialize_connection():
                    return False

            self.spreadsheet = self.client.open_by_url(spreadsheet_url)
            self.log_info(f"Таблица открыта: {self.spreadsheet.title}")
            return True

        except Exception as e:
            self.log_error(f"Ошибка открытия таблицы: {e}")
            return False

    def create_spreadsheet(self, title: str) -> Optional[str]:
        """Создает новую таблицу"""
        try:
            if not self.client:
                if not self.initialize_connection():
                    return None

            spreadsheet = self.client.create(title)
            self.spreadsheet = spreadsheet

            self.log_info(f"Создана новая таблица: {title}")
            return spreadsheet.url

        except Exception as e:
            self.log_error(f"Ошибка создания таблицы: {e}")
            return None

    def upload_data(self, data: List[Dict[str, Any]], worksheet_name: str = "Sheet1") -> bool:
        """Загружает данные в таблицу"""
        try:
            if not self.spreadsheet:
                raise Exception("Таблица не открыта")

            # Получаем или создаем лист
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=26)

            # Подготавливаем данные
            if not data:
                self.log_warning("Нет данных для загрузки")
                return False

            # Получаем заголовки
            headers = list(data[0].keys())

            # Подготавливаем строки данных
            rows = [headers]
            for item in data:
                row = [str(item.get(header, "")) for header in headers]
                rows.append(row)

            # Загружаем данные
            worksheet.clear()
            worksheet.update("A1", rows)

            self.log_info(f"Данные загружены в лист '{worksheet_name}': {len(data)} записей")
            self.emit_event(
                EventType.DATA_UPDATED,
                {"worksheet": worksheet_name, "records_count": len(data), "spreadsheet": self.spreadsheet.title},
            )

            return True

        except Exception as e:
            self.log_error(f"Ошибка загрузки данных: {e}")
            return False

    def download_data(self, worksheet_name: str = "Sheet1") -> List[Dict[str, Any]]:
        """Загружает данные из таблицы"""
        try:
            if not self.spreadsheet:
                raise Exception("Таблица не открыта")

            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()

            if not all_values:
                return []

            # Первая строка - заголовки
            headers = all_values[0]
            data = []

            # Остальные строки - данные
            for row in all_values[1:]:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = value
                data.append(row_dict)

            self.log_info(f"Данные загружены из листа '{worksheet_name}': {len(data)} записей")
            return data

        except Exception as e:
            self.log_error(f"Ошибка загрузки данных: {e}")
            return []

    def append_data(self, data: List[Dict[str, Any]], worksheet_name: str = "Sheet1") -> bool:
        """Добавляет данные в конец таблицы"""
        try:
            if not self.spreadsheet:
                raise Exception("Таблица не открыта")

            worksheet = self.spreadsheet.worksheet(worksheet_name)

            if not data:
                self.log_warning("Нет данных для добавления")
                return False

            # Получаем заголовки из первой записи
            headers = list(data[0].keys())

            # Подготавливаем строки данных
            rows = []
            for item in data:
                row = [str(item.get(header, "")) for header in headers]
                rows.append(row)

            # Добавляем данные
            worksheet.append_rows(rows)

            self.log_info(f"Данные добавлены в лист '{worksheet_name}': {len(data)} записей")
            return True

        except Exception as e:
            self.log_error(f"Ошибка добавления данных: {e}")
            return False

    def get_worksheet_info(self, worksheet_name: str = "Sheet1") -> Optional[Dict[str, Any]]:
        """Возвращает информацию о листе"""
        try:
            if not self.spreadsheet:
                return None

            worksheet = self.spreadsheet.worksheet(worksheet_name)

            return {
                "title": worksheet.title,
                "row_count": worksheet.row_count,
                "col_count": worksheet.col_count,
                "updated": worksheet.updated,
            }

        except Exception as e:
            self.log_error(f"Ошибка получения информации о листе: {e}")
            return None

    def list_worksheets(self) -> List[str]:
        """Возвращает список листов в таблице"""
        try:
            if not self.spreadsheet:
                return []

            worksheets = self.spreadsheet.worksheets()
            return [ws.title for ws in worksheets]

        except Exception as e:
            self.log_error(f"Ошибка получения списка листов: {e}")
            return []

    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = ["service_account_path", "scopes"]

        for key in required_keys:
            if key not in self.config:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False

        return True

    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["service_account_path", "scopes"]

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        try:
            stats = {
                "connected": self.client is not None,
                "spreadsheet_open": self.spreadsheet is not None,
                "service_account_path": self.config["service_account_path"],
            }

            if self.spreadsheet:
                stats["spreadsheet_title"] = self.spreadsheet.title
                stats["worksheets"] = self.list_worksheets()

            return stats

        except Exception as e:
            self.log_error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)}

    def _parse_sheet_date(self, sheet_name: str) -> Optional[datetime]:
        """Парсит дату из названия листа"""
        import re

        date_pattern = r"(\d{1,2})[.-](\d{1,2})[.-](\d{4})"
        match = re.search(date_pattern, sheet_name)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None
        return None

    def _sort_sheets_by_date(self, sheet_names: list) -> list:
        """Сортирует листы по датам в названиях"""
        dated_sheets = []
        undated_sheets = []

        for name in sheet_names:
            date_obj = self._parse_sheet_date(name)
            if date_obj:
                dated_sheets.append((name, date_obj))
            else:
                undated_sheets.append(name)

        dated_sheets.sort(key=lambda x: x[1])
        return [s[0] for s in dated_sheets] + undated_sheets

    def _get_sheets_range(self, sorted_sheets: list, sheet_from: str, sheet_to: str) -> list:
        """Определяет диапазон листов для обработки"""
        try:
            from_idx = sorted_sheets.index(sheet_from)
            to_idx = sorted_sheets.index(sheet_to)
        except ValueError:
            raise Exception(f"Лист '{sheet_from}' или '{sheet_to}' не найден в таблице")

        if from_idx <= to_idx:
            return sorted_sheets[from_idx : to_idx + 1]
        else:
            return sorted_sheets[to_idx : from_idx + 1]

    def _setup_dataframe_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Настраивает колонки DataFrame"""
        if len(df) == 0:
            return df

        first_row_has_text = any(str(cell).strip() for cell in df.iloc[0] if pd.notna(cell))
        if first_row_has_text:
            df.columns = df.iloc[0]
            df = df.iloc[1:]
        else:
            df.columns = [f"Column_{i}" for i in range(len(df.columns))]

        return df

    def _find_text_columns(self, df: pd.DataFrame) -> list:
        """Находит колонки с текстовым содержимым"""
        text_keywords = ["текст", "content", "описание", "text", "сообщение", "пост"]
        text_columns = []

        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in text_keywords):
                text_columns.append(col)

        return text_columns if text_columns else list(df.columns)

    def _extract_text_from_columns(self, df: pd.DataFrame, text_columns: list) -> list:
        """Извлекает текст из указанных колонок"""
        sheet_texts = []

        for col in text_columns:
            column_values = df[col].dropna()
            column_values = column_values[column_values.astype(str).str.strip() != ""]

            for value in column_values:
                val = str(value).strip()
                if val:
                    sheet_texts.append(val)

        return sheet_texts

    def _extract_text_from_sheet(self, sheet_name: str, cell_range: str) -> list:
        """Извлекает текстовые данные из одного листа"""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            data = worksheet.get(cell_range)
            if not data:
                return []

            df = pd.DataFrame(data)
            if len(df) == 0:
                return []

            # Настройка колонок и очистка данных
            df = self._setup_dataframe_columns(df)
            df = df.dropna(how="all").dropna(axis=1, how="all")

            # Поиск и извлечение текста
            text_columns = self._find_text_columns(df)
            return self._extract_text_from_columns(df, text_columns)

        except Exception as e:
            self.log_error(f"Ошибка обработки листа '{sheet_name}': {e}")
            return []

    def load_data_from_sheets(self, sheet_from: str, sheet_to: str, cell_range: str) -> Tuple[list, list]:
        """Загружает данные из указанного диапазона листов и ячеек"""
        try:
            if not self.spreadsheet:
                raise Exception("Таблица не открыта")

            # Получение и сортировка листов
            worksheets = self.spreadsheet.worksheets()
            sheet_names = [ws.title for ws in worksheets]
            sorted_sheets = self._sort_sheets_by_date(sheet_names)

            # Определение диапазона листов
            sheets_to_process = self._get_sheets_range(sorted_sheets, sheet_from, sheet_to)

            # Обработка каждого листа
            all_texts = []
            processed_sheets = []

            for sheet_name in sheets_to_process:
                sheet_texts = self._extract_text_from_sheet(sheet_name, cell_range)
                if sheet_texts:
                    all_texts.extend(sheet_texts)
                    processed_sheets.append(sheet_name)

            return all_texts, processed_sheets

        except Exception as e:
            self.log_error(f"Ошибка загрузки данных из Google Sheets: {e}")
            return [], []
