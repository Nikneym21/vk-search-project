#!/usr/bin/env python3
"""
Обновленный главный интерфейс с интеграцией базы данных
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.gui.vk_parser_interface import VKParserInterface
from src.gui.link_comparator_interface import LinkComparatorInterface
from src.gui.database_interface import DatabaseInterface

class MainInterface:
    """Главный интерфейс приложения с поддержкой базы данных"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Сравнитель ссылок и Парсер ВК - База данных")
        self.root.geometry("1400x900")
        
        # Инициализируем плагины через PluginManager
        self.init_plugins()
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Загружаем настройки окна
        self.load_window_settings()
        
        # Привязываем события
        self.bind_events()
    
    def init_plugins(self):
        """Инициализация плагинов через PluginManager"""
        try:
            from src.core.plugin_manager import PluginManager
            
            # Создаем центральный PluginManager
            self.plugin_manager = PluginManager()
            
            # Загружаем все плагины
            self.plugin_manager.load_plugins()
            
            # Инициализируем плагины (включая установку зависимостей)
            self.plugin_manager.initialize_plugins()
            
            # Получаем нужные плагины
            self.database_plugin = self.plugin_manager.get_plugin('database')
            self.filter_plugin = self.plugin_manager.get_plugin('filter')
            self.vk_search_plugin = self.plugin_manager.get_plugin('vk_search')
            self.token_manager = self.plugin_manager.get_plugin('token_manager')
            
            # Проверяем статус плагинов
            plugin_status = self.plugin_manager.get_plugin_status()
            print("📊 Статус плагинов:")
            for plugin_name, status in plugin_status.items():
                print(f"   {plugin_name}: {status}")
            
            # Проверяем зависимости
            dependencies = self.plugin_manager.validate_plugin_dependencies()
            print("🔗 Проверка зависимостей:")
            for plugin_name, deps in dependencies.items():
                for dep in deps:
                    print(f"   {plugin_name}: {dep}")
            
            if not self.database_plugin:
                messagebox.showwarning("Внимание", "Плагин базы данных не найден")
            
            print("✅ Все плагины инициализированы через PluginManager")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации плагинов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось инициализировать плагины:\n{str(e)}")
            self.database_plugin = None
            self.filter_plugin = None
            self.vk_search_plugin = None
            self.token_manager = None
    
    def setup_ui(self):
        """Создание интерфейса"""
        # Создаем меню
        self.create_menu()
        
        # Создаем панель вкладок
        self.create_notebook()
        
        # Создаем статусную строку
        self.create_status_bar()
    
    def create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="База данных", command=self.show_database_interface)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Статистика БД", command=self.show_database_stats)
        tools_menu.add_command(label="Статус плагинов", command=self.show_plugin_status)
        tools_menu.add_command(label="Очистить БД", command=self.clear_database)
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def create_notebook(self):
        """Создание панели вкладок"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Вкладка Парсер ВК
        self.vk_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.vk_frame, text="Парсер ВК")
        
        # Вкладка Сравнитель ссылок
        self.link_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.link_frame, text="Сравнитель ссылок")
        
        # Вкладка База данных
        self.db_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.db_frame, text="База данных")
        
        # Инициализируем интерфейсы
        self.init_interfaces()
    
    def init_interfaces(self):
        """Инициализация интерфейсов"""
        try:
            # Интерфейс парсера ВК с передачей PluginManager
            self.vk_interface = VKParserInterface(self.vk_frame, self.plugin_manager)
            
            # Интерфейс сравнителя ссылок
            self.link_interface = LinkComparatorInterface(self.link_frame)
            
            # Интерфейс базы данных
            if self.database_plugin:
                self.db_interface = DatabaseInterface(self.db_frame, self.database_plugin)
            else:
                # Заглушка если БД недоступна
                self.create_db_placeholder()
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось инициализировать интерфейсы: {e}")
    
    def create_db_placeholder(self):
        """Создание заглушки для базы данных"""
        placeholder_frame = ttk.Frame(self.db_frame)
        placeholder_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ttk.Label(placeholder_frame, text="База данных недоступна", 
                 font=("Arial", 16, "bold")).pack(pady=(50, 20))
        
        ttk.Label(placeholder_frame, text="Проверьте настройки и попробуйте снова", 
                 font=("Arial", 12)).pack(pady=(0, 30))
        
        ttk.Button(placeholder_frame, text="Повторить инициализацию", 
                  command=self.retry_database_init).pack()
    
    def create_status_bar(self):
        """Создание статусной строки"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_label = ttk.Label(self.status_bar, text="Готов к работе")
        self.status_label.pack(side="left", padx=5)
        
        # Индикатор базы данных
        if self.database_plugin:
            self.db_status = ttk.Label(self.status_bar, text="🟢 БД подключена", foreground="green")
        else:
            self.db_status = ttk.Label(self.status_bar, text="🔴 БД недоступна", foreground="red")
        self.db_status.pack(side="right", padx=5)
    
    def bind_events(self):
        """Привязка событий"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Обработка изменения вкладок
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        try:
            # Сохраняем настройки окна
            self.save_window_settings()
            
            # Закрываем плагины через PluginManager
            if hasattr(self, 'plugin_manager'):
                self.plugin_manager.shutdown_plugins()
            
            self.root.destroy()
            
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")
            self.root.destroy()
    
    def on_tab_changed(self, event):
        """Обработка смены вкладки"""
        current_tab = self.notebook.select()
        tab_id = self.notebook.index(current_tab)
        
        if tab_id == 0:  # Парсер ВК
            self.status_label.config(text="Парсер ВК - готов к работе")
        elif tab_id == 1:  # Сравнитель ссылок
            self.status_label.config(text="Сравнитель ссылок - готов к работе")
        elif tab_id == 2:  # База данных
            self.status_label.config(text="База данных - управление результатами")
    
    def show_database_interface(self):
        """Показать интерфейс базы данных"""
        self.notebook.select(2)  # Переключаемся на вкладку БД
    
    def show_database_stats(self):
        """Показать статистику базы данных"""
        if not self.database_plugin:
            messagebox.showwarning("Внимание", "База данных недоступна")
            return
        
        try:
            tasks = self.database_plugin.get_tasks()
            total_posts = sum(task['total_posts'] for task in tasks)
            total_likes = sum(task['total_likes'] for task in tasks)
            total_SI = sum(task['total_SI'] for task in tasks)
            
            stats_text = f"Статистика базы данных:\n\n"
            stats_text += f"Задач: {len(tasks)}\n"
            stats_text += f"Постов: {total_posts}\n"
            stats_text += f"Лайков: {total_likes}\n"
            stats_text += f"Общий SI: {total_SI}\n"
            
            messagebox.showinfo("Статистика БД", stats_text)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить статистику: {e}")
    
    def show_plugin_status(self):
        """Показать статус плагинов"""
        if not hasattr(self, 'plugin_manager'):
            messagebox.showwarning("Внимание", "PluginManager недоступен")
            return
        
        try:
            plugin_status = self.plugin_manager.get_plugin_status()
            dependencies = self.plugin_manager.validate_plugin_dependencies()
            
            status_text = "Статус плагинов:\n\n"
            
            for plugin_name, status in plugin_status.items():
                status_text += f"{plugin_name}: {status}\n"
            
            status_text += "\nЗависимости:\n"
            for plugin_name, deps in dependencies.items():
                for dep in deps:
                    status_text += f"{plugin_name}: {dep}\n"
            
            messagebox.showinfo("Статус плагинов", status_text)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить статус плагинов: {e}")
    
    def clear_database(self):
        """Очистить базу данных"""
        if not self.database_plugin:
            messagebox.showwarning("Внимание", "База данных недоступна")
            return
        
        result = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите очистить всю базу данных?\n"
            "Это действие нельзя отменить!"
        )
        
        if result:
            try:
                cursor = self.database_plugin.connection.cursor()
                cursor.execute("DELETE FROM posts")
                cursor.execute("DELETE FROM tasks")
                cursor.execute("DELETE FROM task_metadata")
                self.database_plugin.connection.commit()
                
                messagebox.showinfo("Успех", "База данных очищена")
                
                # Обновляем интерфейс БД
                if hasattr(self, 'db_interface'):
                    self.db_interface.load_tasks()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить БД: {e}")
    
    def retry_database_init(self):
        """Повторная инициализация базы данных"""
        try:
            # Переинициализируем существующий PluginManager
            self.plugin_manager.load_plugins()
            self.plugin_manager.initialize_plugins()
            
            # Получаем обновленные плагины
            self.database_plugin = self.plugin_manager.get_plugin('database')
            self.filter_plugin = self.plugin_manager.get_plugin('filter')
            self.vk_search_plugin = self.plugin_manager.get_plugin('vk_search')
            self.token_manager = self.plugin_manager.get_plugin('token_manager')
            
            if self.database_plugin:
                # Пересоздаем интерфейс БД
                for widget in self.db_frame.winfo_children():
                    widget.destroy()
                
                self.db_interface = DatabaseInterface(self.db_frame, self.database_plugin)
                self.db_status.config(text="🟢 БД подключена", foreground="green")
                
                messagebox.showinfo("Успех", "База данных успешно переинициализирована")
            else:
                messagebox.showerror("Ошибка", "Не удалось переинициализировать базу данных")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка переинициализации: {e}")
    
    def show_about(self):
        """Показать информацию о программе"""
        about_text = """
Сравнитель ссылок и Парсер ВК
Версия с поддержкой базы данных

Функции:
• Парсинг постов ВК по ключевым словам
• Сравнение ссылок на дубликаты
• Сохранение результатов в базу данных
• Экспорт в CSV/JSON по требованию
• Поиск и удаление дубликатов
• Статистика и аналитика

База данных: SQLite
Формат: parser_results.db
Архитектура: PluginManager
        """
        
        messagebox.showinfo("О программе", about_text)
    
    def load_window_settings(self):
        """Загрузка настроек окна"""
        try:
            import json
            import os
            
            settings_file = "data/window_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Применяем настройки
                if 'window_width' in settings and 'window_height' in settings:
                    width = settings['window_width']
                    height = settings['window_height']
                    x = settings.get('window_x', 100)
                    y = settings.get('window_y', 100)
                    
                    self.root.geometry(f"{width}x{height}+{x}+{y}")
                    
        except Exception as e:
            print(f"Ошибка загрузки настроек окна: {e}")
    
    def save_window_settings(self):
        """Сохранение настроек окна"""
        try:
            import json
            import os
            
            # Создаем папку если её нет
            os.makedirs("data", exist_ok=True)
            
            # Получаем текущие размеры и позицию окна
            geometry = self.root.geometry()
            # Формат: "widthxheight+x+y"
            parts = geometry.split('+')
            size_parts = parts[0].split('x')
            
            settings = {
                'window_width': int(size_parts[0]),
                'window_height': int(size_parts[1]),
                'window_x': int(parts[1]),
                'window_y': int(parts[2]),
                'last_saved': datetime.now().isoformat()
            }
            
            # Сохраняем в файл
            with open("data/window_settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек окна: {e}") 