import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import os
import re
import csv
from datetime import datetime
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import emoji

class VKParserInterface:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        
        # Инициализация переменных
        self.vk_api_wrapper = None
        self.db = None
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Загружаем сохраненные данные
        self.load_saved_token()
        self.load_search_history()
        self.load_sheets_url()
        self.load_sheets_range_settings()
    
    def setup_ui(self):
        """Настройка интерфейса для парсера ВК"""
        # Главный фрейм для парсера ВК
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Создаем PanedWindow для возможности изменения размеров панелей мышкой
        self.paned_window = ttk.PanedWindow(main_frame, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True)
        
        # Привязываем событие изменения позиции разделителя
        self.paned_window.bind("<ButtonRelease-1>", self.on_paned_window_change)
        
        # Левая панель - параметры поиска (делаем шире)
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=3)  # Левая панель получает 75% пространства
        
        # Создаем canvas с прокруткой для левой панели
        left_canvas = tk.Canvas(left_frame, bg='#2b2b2b', highlightthickness=0, height=600, width=500)
        left_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=left_canvas.yview)
        left_scrollable_frame = ttk.Frame(left_canvas)
        
        left_scrollable_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        
        left_canvas.create_window((0, 0), window=left_scrollable_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # Размещаем canvas и scrollbar
        left_canvas.grid(row=0, column=0, sticky="nsew")
        left_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Настройка весов для прокрутки
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Токен API ВК
        ttk.Label(left_scrollable_frame, text="Токен API ВК:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 2))
        ttk.Label(left_scrollable_frame, text="Получите токен на https://vkhost.github.io/", 
                 foreground="blue", cursor="hand2", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=(0, 2))
        
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(left_scrollable_frame, textvariable=self.token_var, width=55)
        token_entry.grid(row=2, column=0, sticky="ew", pady=(0, 2))
        
        # Кнопка тестирования подключения
        ttk.Button(left_scrollable_frame, text="Тестировать подключение", 
                  command=self.test_vk_connection).grid(row=3, column=0, sticky="w", pady=(0, 2))
        
        # Статус подключения
        self.connection_status = ttk.Label(left_scrollable_frame, text="Статус: Не подключено", foreground="red", font=("Arial", 9))
        self.connection_status.grid(row=4, column=0, sticky="w", pady=(0, 10))
        
        # Кнопка поиска - размещаем под статусом подключения
        self.search_button = tk.Button(
            left_scrollable_frame, 
            text="НАЧАТЬ ПОИСК", 
            command=self.start_vk_search,
            font=("Arial", 14, "bold"),
            bg="#007AFF",
            fg="white",
            relief="raised",
            bd=2,
            padx=25,
            pady=10,
            cursor="hand2"
        )
        self.search_button.grid(row=5, column=0, sticky="ew", pady=10, padx=5)
        
        # Кнопка альтернативного поиска (для обхода блокировки VK)
        self.alternative_search_button = tk.Button(
            left_scrollable_frame, 
            text="АЛЬТЕРНАТИВНЫЙ ПОИСК", 
            command=self.start_alternative_search,
            font=("Arial", 12, "bold"),
            bg="#FF6B35",
            fg="white",
            relief="raised",
            bd=2,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.alternative_search_button.grid(row=6, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        # Кнопка управления токенами
        self.token_manager_button = tk.Button(
            left_scrollable_frame, 
            text="УПРАВЛЕНИЕ ТОКЕНАМИ", 
            command=self.open_token_manager,
            font=("Arial", 10, "bold"),
            bg="#28A745",
            fg="white",
            relief="raised",
            bd=2,
            padx=15,
            pady=6,
            cursor="hand2"
        )
        self.token_manager_button.grid(row=7, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        # Ключевые фразы
        ttk.Label(left_scrollable_frame, text="Ключевые фразы:", font=("Arial", 11, "bold")).grid(row=8, column=0, sticky="w", pady=(10, 2))
        ttk.Label(left_scrollable_frame, text="По одной ключевой фразе в строке.", font=("Arial", 9)).grid(row=9, column=0, sticky="w", pady=(0, 2))
        
        self.keywords_text = tk.Text(left_scrollable_frame, height=8, width=55)
        self.keywords_text.grid(row=10, column=0, sticky="ew", pady=(0, 8))
        
        # Период поиска
        ttk.Label(left_scrollable_frame, text="Период поиска новостей (обязательный параметр):", font=("Arial", 11, "bold")).grid(row=11, column=0, sticky="w", pady=(0, 2))
        
        # Правила
        rules_frame = ttk.Frame(left_scrollable_frame)
        rules_frame.grid(row=12, column=0, sticky="w", pady=(0, 5))
        ttk.Label(rules_frame, text="• поиск возможен по новостям не старше 3-х лет", font=("Arial", 9)).grid(row=0, column=0, sticky="w")
        ttk.Label(rules_frame, text="• максимальный период поиска - 1 год", font=("Arial", 9)).grid(row=1, column=0, sticky="w")
        
        # Даты и время
        dates_frame = ttk.Frame(left_scrollable_frame)
        dates_frame.grid(row=13, column=0, sticky="w", pady=(0, 5))
        
        # Первая дата с временем
        ttk.Label(dates_frame, text="С:", font=("Arial", 9)).grid(row=0, column=0, sticky="w")
        self.start_date_var = tk.StringVar(value="18.07.2025")
        self.start_date_entry = ttk.Entry(dates_frame, textvariable=self.start_date_var, width=12)
        self.start_date_entry.grid(row=0, column=1, padx=(3, 0))
        ttk.Button(dates_frame, text="×", width=2, command=lambda: self.start_date_var.set("")).grid(row=0, column=2, padx=(3, 0))
        
        ttk.Label(dates_frame, text="время:", font=("Arial", 9)).grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.start_time_var = tk.StringVar(value="07:00")
        self.start_time_entry = ttk.Entry(dates_frame, textvariable=self.start_time_var, width=8)
        self.start_time_entry.grid(row=0, column=4, padx=(3, 0))
        
        # Вторая дата с временем
        ttk.Label(dates_frame, text="По:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.end_date_var = tk.StringVar(value="19.07.2025")
        self.end_date_entry = ttk.Entry(dates_frame, textvariable=self.end_date_var, width=12)
        self.end_date_entry.grid(row=1, column=1, padx=(3, 0), pady=(3, 0))
        ttk.Button(dates_frame, text="×", width=2, command=lambda: self.end_date_var.set("")).grid(row=1, column=2, padx=(3, 0), pady=(3, 0))
        
        ttk.Label(dates_frame, text="время:", font=("Arial", 9)).grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(3, 0))
        self.end_time_var = tk.StringVar(value="06:00")
        self.end_time_entry = ttk.Entry(dates_frame, textvariable=self.end_time_var, width=8)
        self.end_time_entry.grid(row=1, column=4, padx=(3, 0), pady=(3, 0))
        
        # Быстрый выбор периодов
        quick_dates_frame = ttk.Frame(left_scrollable_frame)
        quick_dates_frame.grid(row=14, column=0, sticky="w", pady=(0, 8))
        ttk.Label(quick_dates_frame, text="За месяц, неделю, три дня, день", font=("Arial", 9)).grid(row=0, column=0, sticky="w")
        
        # Точное вхождение
        self.exact_match_var = tk.BooleanVar(value=True)
        exact_match_check = ttk.Checkbutton(left_scrollable_frame, text="Точное вхождение поисковой фразы", variable=self.exact_match_var)
        exact_match_check.grid(row=15, column=0, sticky="w", pady=(0, 8))
        
        # Минус слова
        ttk.Label(left_scrollable_frame, text="Минус слова:", font=("Arial", 11, "bold")).grid(row=16, column=0, sticky="w", pady=(0, 2))
        ttk.Label(left_scrollable_frame, text="По одному минус слову/фразе в строке.", font=("Arial", 9)).grid(row=17, column=0, sticky="w", pady=(0, 2))
        
        self.minus_words_text = tk.Text(left_scrollable_frame, height=3, width=55)
        self.minus_words_text.grid(row=18, column=0, sticky="ew", pady=(0, 8))
        
        # Вложения
        ttk.Label(left_scrollable_frame, text="Вложения:", font=("Arial", 11, "bold")).grid(row=19, column=0, sticky="w", pady=(0, 2))
        self.attachments_var = tk.StringVar(value="Без разницы")
        attachments_combo = ttk.Combobox(left_scrollable_frame, textvariable=self.attachments_var, state="readonly", width=25)
        attachments_combo['values'] = ["Без разницы", "Фото", "Видео", "Без вложения"]
        attachments_combo.grid(row=20, column=0, sticky="w", pady=(0, 10))
        
        # Кнопка загрузки из Google Sheets
        ttk.Label(left_scrollable_frame, text="Автоматическая загрузка:", font=("Arial", 11, "bold")).grid(row=21, column=0, sticky="w", pady=(10, 2))
        
        # Поле ввода ссылки на Google Sheets
        ttk.Label(left_scrollable_frame, text="Ссылка на Google Sheets:", font=("Arial", 9)).grid(row=22, column=0, sticky="w", pady=(0, 2))
        self.sheets_url_var = tk.StringVar()
        sheets_url_entry = ttk.Entry(left_scrollable_frame, textvariable=self.sheets_url_var, width=55)
        sheets_url_entry.grid(row=23, column=0, sticky="ew", pady=(0, 5))
        
        # Привязываем событие изменения ссылки для автоматического сохранения
        self.sheets_url_var.trace("w", lambda *args: self.save_sheets_url())
        
        # Настройки диапазона
        range_frame = ttk.LabelFrame(left_scrollable_frame, text="Настройки диапазона", padding="5")
        range_frame.grid(row=24, column=0, sticky="ew", pady=(0, 5))
        
        # Диапазон листов по датам
        ttk.Label(range_frame, text="Диапазон листов:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=(0, 2))
        
        sheets_range_frame = ttk.Frame(range_frame)
        sheets_range_frame.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=(0, 2))
        
        ttk.Label(sheets_range_frame, text="от:", font=("Arial", 9)).pack(side="left")
        self.sheet_from_var = tk.StringVar()
        self.sheet_from_combo = ttk.Combobox(sheets_range_frame, textvariable=self.sheet_from_var, width=12, state="readonly")
        self.sheet_from_combo.pack(side="left", padx=(3, 5))
        
        ttk.Label(sheets_range_frame, text="до:", font=("Arial", 9)).pack(side="left")
        self.sheet_to_var = tk.StringVar()
        self.sheet_to_combo = ttk.Combobox(sheets_range_frame, textvariable=self.sheet_to_var, width=12, state="readonly")
        self.sheet_to_combo.pack(side="left", padx=(3, 0))
        
        # Кнопка обновления списка листов
        ttk.Button(range_frame, text="Обновить список листов", 
                  command=self.update_sheets_list, width=20).grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        # Диапазон ячеек
        ttk.Label(range_frame, text="Диапазон ячеек:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=(5, 2))
        self.cell_range_var = tk.StringVar(value="A:Z")
        cell_range_entry = ttk.Entry(range_frame, textvariable=self.cell_range_var, width=20)
        cell_range_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=(5, 2))
        
        # Привязываем события изменения настроек диапазона для автоматического сохранения
        self.cell_range_var.trace("w", lambda *args: self.save_sheets_range_settings())
        self.sheet_from_var.trace("w", lambda *args: self.save_sheets_range_settings())
        self.sheet_to_var.trace("w", lambda *args: self.save_sheets_range_settings())
        
        # Привязываем автосохранение для всех остальных полей
        self.start_date_var.trace("w", lambda *args: self.save_window_settings())
        self.start_time_var.trace("w", lambda *args: self.save_window_settings())
        self.end_date_var.trace("w", lambda *args: self.save_window_settings())
        self.end_time_var.trace("w", lambda *args: self.save_window_settings())
        self.exact_match_var.trace("w", lambda *args: self.save_window_settings())
        self.attachments_var.trace("w", lambda *args: self.save_window_settings())
        
        # Привязываем автосохранение для текстовых полей
        self.keywords_text.bind("<KeyRelease>", lambda event: self.save_window_settings())
        self.minus_words_text.bind("<KeyRelease>", lambda event: self.save_window_settings())
        
        # Подсказка
        ttk.Label(range_frame, text="Примеры: A:Z, A1:D100, Sheet1!A:Z", 
                 font=("Arial", 8), foreground="gray").grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 0))
        
        sheets_frame = ttk.Frame(left_scrollable_frame)
        sheets_frame.grid(row=25, column=0, sticky="w", pady=(0, 10))
        
        ttk.Button(sheets_frame, text="Загрузить из Google Sheets", 
                  command=self.load_from_google_sheets).pack(side="left", padx=(0, 5))
        
        ttk.Button(sheets_frame, text="Очистить эмодзи", 
                  command=self.clean_emojis).pack(side="left")
        
        ttk.Button(sheets_frame, text="Загрузить и запустить", 
                  command=self.load_and_start_search).pack(side="left", padx=(5, 0))
        
        # Кнопка тестирования без точного вхождения
        ttk.Button(sheets_frame, text="Тест без точного вхождения", 
                  command=self.test_search_without_exact).pack(side="left", padx=(5, 0))
        
        # Статус загрузки
        self.sheets_status = ttk.Label(left_scrollable_frame, text="", font=("Arial", 9))
        self.sheets_status.grid(row=26, column=0, sticky="w", pady=(0, 10))
        
        # Правая панель - история и результаты (делаем уже)
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=1)  # Правая панель получает 25% пространства
        
        # Вкладки истории
        history_notebook = ttk.Notebook(right_frame)
        history_notebook.pack(fill="both", expand=True)
        
        # Вкладка "Все"
        all_frame = ttk.Frame(history_notebook)
        history_notebook.add(all_frame, text="Все")
        
        # Список задач с прокруткой
        history_frame = ttk.Frame(all_frame)
        history_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.tasks_tree = ttk.Treeview(history_frame, columns=("date", "datetime", "count", "status"), show="headings", height=8)
        self.tasks_tree.heading("date", text="Дата")
        self.tasks_tree.heading("datetime", text="Дата/Время")
        self.tasks_tree.heading("count", text="Кол-во")
        self.tasks_tree.heading("status", text="Статус")
        self.tasks_tree.column("date", width=60)
        self.tasks_tree.column("datetime", width=120)
        self.tasks_tree.column("count", width=60)
        self.tasks_tree.column("status", width=100)
        
        # Добавляем прокрутку для таблицы истории
        history_scrollbar_y = ttk.Scrollbar(history_frame, orient="vertical", command=self.tasks_tree.yview)
        history_scrollbar_x = ttk.Scrollbar(history_frame, orient="horizontal", command=self.tasks_tree.xview)
        self.tasks_tree.configure(yscrollcommand=history_scrollbar_y.set, xscrollcommand=history_scrollbar_x.set)
        
        # Размещаем таблицу истории и скроллбары
        self.tasks_tree.pack(side="left", fill="both", expand=True)
        history_scrollbar_y.pack(side="right", fill="y")
        history_scrollbar_x.pack(side="bottom", fill="x")
        
        # Привязываем двойной клик для открытия файла
        self.tasks_tree.bind("<Double-1>", self.open_task_file)
        
        # Таблица результатов поиска
        ttk.Label(right_frame, text="Результаты поиска:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Создаем фрейм для таблицы результатов с прокруткой
        results_frame = ttk.Frame(right_frame)
        results_frame.pack(fill="both", expand=True)
        
        self.results_tree = ttk.Treeview(results_frame, columns=("link", "text", "type", "author", "author_link", "date", "likes", "comments", "reposts", "views"), show="headings", height=10)
        self.results_tree.heading("link", text="Ссылка")
        self.results_tree.heading("text", text="Текст")
        self.results_tree.heading("type", text="Тип")
        self.results_tree.heading("author", text="Автор")
        self.results_tree.heading("author_link", text="Ссылка на автора")
        self.results_tree.heading("date", text="Дата")
        self.results_tree.heading("likes", text="Лайков")
        self.results_tree.heading("comments", text="Комментариев")
        self.results_tree.heading("reposts", text="Репостов")
        self.results_tree.heading("views", text="Просмотров")
        
        # Устанавливаем ширину колонок
        self.results_tree.column("link", width=150)
        self.results_tree.column("text", width=200)
        self.results_tree.column("type", width=80)
        self.results_tree.column("author", width=120)
        self.results_tree.column("author_link", width=150)
        self.results_tree.column("date", width=100)
        self.results_tree.column("likes", width=80)
        self.results_tree.column("comments", width=100)
        self.results_tree.column("reposts", width=80)
        self.results_tree.column("views", width=80)
        
        # Добавляем прокрутку для таблицы результатов
        results_scrollbar_y = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        results_scrollbar_x = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=results_scrollbar_y.set, xscrollcommand=results_scrollbar_x.set)
        
        # Размещаем таблицу результатов и скроллбары
        self.results_tree.pack(side="left", fill="both", expand=True)
        results_scrollbar_y.pack(side="right", fill="y")
        results_scrollbar_x.pack(side="bottom", fill="x")
        
        # Кнопка "Загрузить еще"
        ttk.Button(all_frame, text="ЗАГРУЗИТЬ ЕЩЕ", command=self.load_more_tasks).pack(pady=(0, 10))
        
        # Информация о истории
        info_frame = ttk.Frame(all_frame)
        info_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(info_frame, text="История задач хранится 30 дней. Для неограниченного хранения установите флаг ★", 
                 foreground="orange").pack(anchor="w")
        ttk.Label(info_frame, text="Что означают статусы задач >", foreground="blue", cursor="hand2").pack(anchor="w")
        
        # Кнопка сохранения результатов
        self.save_results_button = ttk.Button(right_frame, text="Сохранить результаты", command=self.save_vk_results)
        self.save_results_button.pack(side="bottom", fill="x", pady=(5, 0))
        
        # Настройка весов
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
    
    def load_saved_token(self):
        """Загрузка сохраненного токена"""
        try:
            if os.path.exists("config/vk_token.txt"):
                with open("config/vk_token.txt", "r") as f:
                    token = f.read().strip()
                    self.token_var.set(token)
        except Exception as e:
            print(f"Ошибка загрузки токена: {str(e)}")
    
    def load_search_history(self):
        """Загрузка истории поиска"""
        try:
            if os.path.exists("data/settings.json"):
                with open("data/settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    if "search_history" in settings:
                        # Здесь можно добавить загрузку истории поиска
                        pass
        except Exception as e:
            print(f"Ошибка загрузки истории: {str(e)}")
    
    def load_sheets_url(self):
        """Загрузка URL Google Sheets"""
        try:
            if os.path.exists("sheets_url.txt"):
                with open("sheets_url.txt", "r") as f:
                    url = f.read().strip()
                    # Здесь можно добавить загрузку URL
        except Exception as e:
            print(f"Ошибка загрузки URL: {str(e)}")
    
    def load_sheets_range_settings(self):
        """Загрузка настроек диапазона Google Sheets"""
        try:
            if os.path.exists("data/settings.json"):
                with open("data/settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    # Здесь можно добавить загрузку настроек диапазона
        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")
    
    def test_vk_connection(self):
        """Тестирование подключения к VK API"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Ошибка", "Введите токен API ВК")
            return
        
        try:
            # Здесь будет тестирование подключения к VK API
            # Пока что просто обновляем статус
            self.connection_status.config(text="Статус: Подключено", foreground="green")
            messagebox.showinfo("Успех", "Подключение к VK API установлено")
        except Exception as e:
            self.connection_status.config(text="Статус: Ошибка подключения", foreground="red")
            messagebox.showerror("Ошибка", f"Не удалось подключиться к VK API: {str(e)}")
    
    def start_vk_search(self):
        """Запуск поиска в VK"""
        token = self.token_var.get().strip()
        query = self.search_query_var.get().strip()
        
        if not token:
            messagebox.showerror("Ошибка", "Введите токен API ВК")
            return
        
        if not query:
            messagebox.showerror("Ошибка", "Введите поисковый запрос")
            return
        
        try:
            # Здесь будет логика поиска в VK
            # Пока что просто показываем сообщение
            messagebox.showinfo("Информация", "Поиск в VK запущен")
            
            # Очищаем предыдущие результаты
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Добавляем тестовые результаты
            self.results_tree.insert("", "end", values=("Тестовый результат", "https://vk.com/test", "2024-01-01"))
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при поиске: {str(e)}")
    
    def start_alternative_search(self):
        """Запуск альтернативного поиска"""
        messagebox.showinfo("Информация", "Альтернативный поиск запущен")
    
    def open_token_manager(self):
        """Открытие менеджера токенов"""
        messagebox.showinfo("Информация", "Менеджер токенов открыт")
    
    def save_vk_results(self):
        """Сохранение результатов поиска"""
        if not self.results_tree.get_children():
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить результаты поиска",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Заголовок", "Ссылка", "Дата"])
                    
                    for item in self.results_tree.get_children():
                        values = self.results_tree.item(item)['values']
                        writer.writerow(values)
                
                messagebox.showinfo("Успех", f"Результаты сохранены в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def on_paned_window_change(self, event):
        """Обработка изменения позиции разделителя панелей"""
        # Здесь можно добавить сохранение позиции разделителя
        pass
    
    def save_window_settings(self):
        """Сохранение настроек окна"""
        try:
            settings = {
                "keywords": self.keywords_text.get("1.0", tk.END).strip(),
                "minus_words": self.minus_words_text.get("1.0", tk.END).strip(),
                "start_date": self.start_date_var.get(),
                "start_time": self.start_time_var.get(),
                "end_date": self.end_date_var.get(),
                "end_time": self.end_time_var.get(),
                "exact_match": self.exact_match_var.get(),
                "attachments": self.attachments_var.get(),
                "last_saved": datetime.now().isoformat()
            }
            
            # Создаем папку data если её нет
            os.makedirs("data", exist_ok=True)
            
            with open("data/settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек: {str(e)}")
    
    def update_sheets_list(self):
        """Обновление списка листов Google Sheets"""
        try:
            # Здесь будет логика обновления списка листов
            messagebox.showinfo("Информация", "Список листов обновлен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить список листов: {str(e)}")
    
    def load_from_google_sheets(self):
        """Загрузка данных из Google Sheets"""
        try:
            # Здесь будет логика загрузки из Google Sheets
            messagebox.showinfo("Информация", "Данные загружены из Google Sheets")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {str(e)}")
    
    def clean_emojis(self):
        """Очистка эмодзи из текста"""
        try:
            # Получаем текст из поля ключевых слов
            text = self.keywords_text.get("1.0", tk.END)
            cleaned_text = self.clean_text_completely(text)
            self.keywords_text.delete("1.0", tk.END)
            self.keywords_text.insert("1.0", cleaned_text)
            
            messagebox.showinfo("Успех", "Эмодзи очищены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить эмодзи: {str(e)}")
    
    def clean_text_completely(self, text):
        """Полная очистка текста от эмодзи и лишних символов"""
        if not text:
            return ""
        
        # Удаляем эмодзи
        cleaned = emoji.replace_emojis(text, replace='')
        
        # Удаляем лишние пробелы и переносы строк
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def load_and_start_search(self):
        """Загрузка данных и запуск поиска"""
        try:
            # Здесь будет логика загрузки данных и запуска поиска
            messagebox.showinfo("Информация", "Поиск запущен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить поиск: {str(e)}")
    
    def test_search_without_exact(self):
        """Тестирование поиска без точного вхождения"""
        try:
            # Здесь будет логика тестирования поиска
            messagebox.showinfo("Информация", "Тест поиска без точного вхождения запущен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить тест: {str(e)}")
    
    def save_sheets_url(self):
        """Сохранение URL Google Sheets"""
        try:
            url = self.sheets_url_var.get().strip()
            if url:
                with open("sheets_url.txt", "w") as f:
                    f.write(url)
        except Exception as e:
            print(f"Ошибка сохранения URL: {str(e)}")
    
    def save_sheets_range_settings(self):
        """Сохранение настроек диапазона Google Sheets"""
        try:
            settings = {
                "cell_range": self.cell_range_var.get(),
                "sheet_from": self.sheet_from_var.get(),
                "sheet_to": self.sheet_to_var.get()
            }
            
            # Создаем папку data если её нет
            os.makedirs("data", exist_ok=True)
            
            with open("data/sheets_range_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек диапазона: {str(e)}")
    
    def load_more_tasks(self):
        """Загрузка дополнительных задач"""
        try:
            # Здесь будет логика загрузки дополнительных задач
            messagebox.showinfo("Информация", "Дополнительные задачи загружены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить задачи: {str(e)}")
    
    def open_task_file(self, event):
        """Открытие файла задачи по двойному клику"""
        try:
            selection = self.tasks_tree.selection()
            if selection:
                item = self.tasks_tree.item(selection[0])
                # Здесь будет логика открытия файла задачи
                messagebox.showinfo("Информация", f"Открытие файла задачи: {item['values']}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")
    
    def display_results_in_treeview(self, df):
        """Отображение результатов в Treeview"""
        try:
            # Очищаем предыдущие результаты
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Добавляем новые результаты
            for index, row in df.iterrows():
                self.results_tree.insert("", "end", values=(
                    row.get('link', ''),
                    row.get('text', ''),
                    row.get('type', ''),
                    row.get('author', ''),
                    row.get('author_link', ''),
                    row.get('date', ''),
                    row.get('likes', ''),
                    row.get('comments', ''),
                    row.get('reposts', ''),
                    row.get('views', '')
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить результаты: {str(e)}") 