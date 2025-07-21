import json
import csv
import os
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.plugins.base_plugin import BasePlugin


class DatabasePlugin(BasePlugin):
    """Плагин для работы с базой данных и сохранения результатов"""
    
    def __init__(self, data_dir: str = 'data'):
        super().__init__("DatabasePlugin", "1.0.0")
        self.data_dir = data_dir
        self.ensure_data_directory()
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация плагина"""
        try:
            self.logger.info("Инициализация DatabasePlugin")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации: {str(e)}")
            return False
    
    def ensure_data_directory(self):
        """Создает директорию для данных, если она не существует"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
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
            
            return filepath
            
        except Exception as e:
            print(f"Ошибка сохранения в CSV: {e}")
            return ""
    
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
            
            return filepath
            
        except Exception as e:
            print(f"Ошибка сохранения в JSON: {e}")
            return ""
    
    def save_results_to_excel(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Сохраняет результаты в Excel файл"""
        try:
            if not results:
                raise ValueError("Нет данных для сохранения")
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"results_{timestamp}.xlsx"
            
            filepath = os.path.join(self.data_dir, filename)
            
            # Создаем DataFrame
            df = pd.DataFrame(results)
            
            # Сохраняем в Excel
            df.to_excel(filepath, index=False)
            
            return filepath
            
        except Exception as e:
            print(f"Ошибка сохранения в Excel: {e}")
            return ""
    
    def load_results_from_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """Загружает результаты из CSV файла"""
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Файл {filepath} не найден")
            
            results = []
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    results.append(row)
            
            return results
            
        except Exception as e:
            print(f"Ошибка загрузки из CSV: {e}")
            return []
    
    def load_results_from_json(self, filepath: str) -> List[Dict[str, Any]]:
        """Загружает результаты из JSON файла"""
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Файл {filepath} не найден")
            
            with open(filepath, 'r', encoding='utf-8') as jsonfile:
                results = json.load(jsonfile)
            
            return results if isinstance(results, list) else []
            
        except Exception as e:
            print(f"Ошибка загрузки из JSON: {e}")
            return []
    
    def load_results_from_excel(self, filepath: str) -> List[Dict[str, Any]]:
        """Загружает результаты из Excel файла"""
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Файл {filepath} не найден")
            
            # Читаем Excel файл
            df = pd.read_excel(filepath)
            
            # Конвертируем в список словарей
            results = df.to_dict('records')
            
            return results
            
        except Exception as e:
            print(f"Ошибка загрузки из Excel: {e}")
            return []
    
    def save_search_history(self, search_data: Dict[str, Any], filename: str = 'search_history.json') -> bool:
        """Сохраняет историю поиска"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            # Загружаем существующую историю
            history = []
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except:
                    history = []
            
            # Добавляем новую запись
            search_data['timestamp'] = datetime.now().isoformat()
            history.append(search_data)
            
            # Сохраняем обновленную историю
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения истории поиска: {e}")
            return False
    
    def load_search_history(self, filename: str = 'search_history.json') -> List[Dict[str, Any]]:
        """Загружает историю поиска"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            return history if isinstance(history, list) else []
            
        except Exception as e:
            print(f"Ошибка загрузки истории поиска: {e}")
            return []
    
    def save_settings(self, settings: Dict[str, Any], filename: str = 'settings.json') -> bool:
        """Сохраняет настройки"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False
    
    def load_settings(self, filename: str = 'settings.json') -> Dict[str, Any]:
        """Загружает настройки"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(filepath):
                return {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            return settings if isinstance(settings, dict) else {}
            
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            return {}
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """Получает информацию о файле"""
        try:
            if not os.path.exists(filepath):
                return {}
            
            stat = os.stat(filepath)
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            return {
                'size': size,
                'modified': modified.isoformat(),
                'size_mb': round(size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            print(f"Ошибка получения информации о файле: {e}")
            return {}
    
    def list_result_files(self) -> List[Dict[str, Any]]:
        """Список файлов с результатами"""
        try:
            files = []
            for filename in os.listdir(self.data_dir):
                if filename.endswith(('.csv', '.json', '.xlsx', '.xls')):
                    filepath = os.path.join(self.data_dir, filename)
                    info = self.get_file_info(filepath)
                    files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': info.get('size', 0),
                        'size_mb': info.get('size_mb', 0),
                        'modified': info.get('modified', '')
                    })
            
            # Сортируем по дате изменения (новые сначала)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            return files
            
        except Exception as e:
            print(f"Ошибка получения списка файлов: {e}")
            return []
    
    def delete_file(self, filepath: str) -> bool:
        """Удаляет файл"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления файла: {e}")
            return False
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Выполняет основную логику плагина"""
        try:
            operation = kwargs.get('operation')
            
            if operation == 'save_csv':
                results = kwargs.get('results', [])
                filename = kwargs.get('filename')
                filepath = self.save_results_to_csv(results, filename)
                return {
                    'success': bool(filepath),
                    'filepath': filepath
                }
            
            elif operation == 'save_json':
                results = kwargs.get('results', [])
                filename = kwargs.get('filename')
                filepath = self.save_results_to_json(results, filename)
                return {
                    'success': bool(filepath),
                    'filepath': filepath
                }
            
            elif operation == 'save_excel':
                results = kwargs.get('results', [])
                filename = kwargs.get('filename')
                filepath = self.save_results_to_excel(results, filename)
                return {
                    'success': bool(filepath),
                    'filepath': filepath
                }
            
            elif operation == 'load_csv':
                filepath = kwargs.get('filepath')
                results = self.load_results_from_csv(filepath)
                return {
                    'success': True,
                    'results': results,
                    'count': len(results)
                }
            
            elif operation == 'load_json':
                filepath = kwargs.get('filepath')
                results = self.load_results_from_json(filepath)
                return {
                    'success': True,
                    'results': results,
                    'count': len(results)
                }
            
            elif operation == 'load_excel':
                filepath = kwargs.get('filepath')
                results = self.load_results_from_excel(filepath)
                return {
                    'success': True,
                    'results': results,
                    'count': len(results)
                }
            
            elif operation == 'save_history':
                search_data = kwargs.get('search_data', {})
                filename = kwargs.get('filename', 'search_history.json')
                success = self.save_search_history(search_data, filename)
                return {
                    'success': success
                }
            
            elif operation == 'load_history':
                filename = kwargs.get('filename', 'search_history.json')
                history = self.load_search_history(filename)
                return {
                    'success': True,
                    'history': history,
                    'count': len(history)
                }
            
            elif operation == 'save_settings':
                settings = kwargs.get('settings', {})
                filename = kwargs.get('filename', 'settings.json')
                success = self.save_settings(settings, filename)
                return {
                    'success': success
                }
            
            elif operation == 'load_settings':
                filename = kwargs.get('filename', 'settings.json')
                settings = self.load_settings(filename)
                return {
                    'success': True,
                    'settings': settings
                }
            
            elif operation == 'list_files':
                files = self.list_result_files()
                return {
                    'success': True,
                    'files': files,
                    'count': len(files)
                }
            
            elif operation == 'delete_file':
                filepath = kwargs.get('filepath')
                success = self.delete_file(filepath)
                return {
                    'success': success
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Неизвестная операция: {operation}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup(self):
        """Очищает ресурсы"""
        pass 