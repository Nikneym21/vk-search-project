import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime

# Импортируем наши интерфейсы
from .link_comparator_interface import LinkComparatorInterface
from .vk_parser_interface import VKParserInterface
from .settings_adapter import SettingsAdapter

class MainInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Сравнитель ссылок и Парсер ВК")
        self.root.geometry("1200x800")
        
        # Инициализируем адаптер настроек
        self.settings_adapter = SettingsAdapter()
        self.settings_plugin = self.settings_adapter.create_settings_manager()
        
        # Подключаем плагин к адаптеру если он создался
        if self.settings_plugin:
            self.settings_adapter.set_settings_plugin(self.settings_plugin)
            print("Плагин настроек успешно подключен")
        else:
            print("Плагин настроек не подключен, используется fallback режим")
        
        # Загружаем сохраненные настройки размеров
        self.load_window_settings()
        
        # Настройка интерфейса
        self.setup_ui()
        self.setup_hotkeys()
        
        # Привязываем событие изменения размера окна
        self.root.bind("<Configure>", self.on_window_resize)
        
        # Привязываем событие закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_hotkeys(self):
        """Настройка горячих клавиш для macOS"""
        # Привязываем горячие клавиши к корневому окну
        self.root.bind('<Command-v>', self.paste_text)
        self.root.bind('<Command-c>', self.copy_text)
        self.root.bind('<Command-a>', self.select_all)
        self.root.bind('<Command-z>', self.undo_text)
        
        # Также привязываем к конкретным виджетам
        self.root.bind_all('<Command-v>', self.paste_text)
        self.root.bind_all('<Command-c>', self.copy_text)
        self.root.bind_all('<Command-a>', self.select_all)
        self.root.bind_all('<Command-z>', self.undo_text)
        
        # Альтернативные привязки для разных систем
        self.root.bind_all('<Control-v>', self.paste_text)
        self.root.bind_all('<Control-c>', self.copy_text)
        self.root.bind_all('<Control-a>', self.select_all)
        self.root.bind_all('<Control-z>', self.undo_text)
    
    def paste_text(self, event=None):
        """Вставка текста"""
        try:
            widget = self.root.focus_get()
            if widget:
                clipboard_text = self.root.clipboard_get()
                if hasattr(widget, 'insert') and hasattr(widget, 'delete'):
                    if hasattr(widget, 'selection_present') and widget.selection_present():
                        widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    else:
                        widget.delete(0, tk.END)
                    widget.insert(tk.INSERT, clipboard_text)
        except Exception as e:
            print(f"Ошибка вставки: {str(e)}")
    
    def copy_text(self, event=None):
        """Копирование текста"""
        try:
            widget = self.root.focus_get()
            if widget and hasattr(widget, 'selection_present') and widget.selection_present():
                selected_text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
        except Exception as e:
            print(f"Ошибка копирования: {str(e)}")
    
    def select_all(self, event=None):
        """Выделение всего текста"""
        try:
            widget = self.root.focus_get()
            if widget and hasattr(widget, 'select_range'):
                widget.select_range(0, tk.END)
                widget.icursor(tk.END)
        except Exception as e:
            print(f"Ошибка выделения: {str(e)}")
    
    def undo_text(self, event=None):
        """Отмена действия"""
        try:
            widget = self.root.focus_get()
            if widget and hasattr(widget, 'edit_undo'):
                widget.edit_undo()
        except Exception as e:
            print(f"Ошибка отмены: {str(e)}")
    
    def setup_ui(self):
        """Настройка главного интерфейса"""
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вкладка 1: Сравнитель ссылок
        self.link_comparator_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.link_comparator_frame, text="Сравнитель ссылок")
        self.link_comparator_interface = LinkComparatorInterface(self.link_comparator_frame)
        
        # Вкладка 2: Парсер ВК
        self.vk_parser_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.vk_parser_frame, text="Парсер ВК")
        self.vk_parser_interface = VKParserInterface(self.vk_parser_frame, self.settings_adapter)
    
    def on_window_resize(self, event):
        """Обработка изменения размера окна"""
        # Сохраняем размеры окна
        if event.widget == self.root:
            self.save_window_settings()
    
    def on_closing(self):
        """Обработка закрытия окна"""
        self.save_window_settings()
        self.root.destroy()
    
    def save_window_settings(self):
        """Сохранение настроек окна"""
        try:
            settings = {
                "window_width": self.root.winfo_width(),
                "window_height": self.root.winfo_height(),
                "window_x": self.root.winfo_x(),
                "window_y": self.root.winfo_y(),
                "last_saved": datetime.now().isoformat()
            }
            
            self.settings_adapter.save_window_settings(settings)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек окна: {str(e)}")
    
    def load_window_settings(self):
        """Загрузка настроек окна"""
        try:
            settings = self.settings_adapter.load_window_settings()
            
            # Применяем сохраненные размеры и позицию
            width = settings.get("window_width", 1200)
            height = settings.get("window_height", 800)
            x = settings.get("window_x", 100)
            y = settings.get("window_y", 100)
            
            # Устанавливаем размеры и позицию окна
            self.root.geometry(f"{width}x{height}+{x}+{y}")
                
        except Exception as e:
            print(f"Ошибка загрузки настроек окна: {str(e)}")
            # Используем значения по умолчанию
            self.root.geometry("1200x800+100+100")

def main():
    """Главная функция для запуска приложения"""
    root = tk.Tk()
    app = MainInterface(root)
    root.mainloop()

if __name__ == "__main__":
    main() 