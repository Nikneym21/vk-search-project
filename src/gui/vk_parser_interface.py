import asyncio
import csv
import json
import os
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from src.plugins.token_manager.token_limiter import TokenLimiter
from src.plugins.vk_search.vk_time_utils import to_vk_timestamp

# Удалены прямые импорты плагинов - теперь получаем через PluginManager:
# from src.plugins.google_sheets.google_sheets_plugin import GoogleSheetsPlugin
# from src.plugins.post_processor.text_processing.text_processing_plugin import TextProcessingPlugin
# from src.plugins.vk_search.vk_search_plugin import VKSearchPlugin


# StatsPlugin был удален, функциональность перенесена в DatabasePlugin


class TokenPool:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.index = 0
        self.lock = threading.Lock()

    def get_token(self):
        with self.lock:
            token = self.tokens[self.index]
            self.index = (self.index + 1) % len(self.tokens)
            return token


class VKParserInterface:
    def __init__(self, parent_frame, plugin_manager=None, settings_adapter=None):
        self.parent_frame = parent_frame
        self.root = parent_frame.winfo_toplevel()  # Получаем корневое окно

        # Сохраняем PluginManager
        self.plugin_manager = plugin_manager
        if not self.plugin_manager:
            raise ValueError("PluginManager обязателен для VKParserInterface")

        # Инициализируем переменные
        self.token_var = tk.StringVar()
        self.vk_api_wrapper = None
        self.db = None

        # Получаем плагины через PluginManager
        self.google_sheets_plugin = self.plugin_manager.get_plugin("google_sheets")
        self.text_processing_plugin = self.plugin_manager.get_plugin("post_processor")
        if self.text_processing_plugin:
            # Получаем TextProcessingPlugin из PostProcessorPlugin
            self.text_processing_plugin = self.text_processing_plugin.text_processing_plugin

        # Создаем адаптер настроек если не передан
        if settings_adapter is None:
            from .settings_adapter import SettingsAdapter

            self.settings_adapter = SettingsAdapter()
            # Передаем PluginManager в create_settings_manager
            self.settings_plugin = self.settings_adapter.create_settings_manager(self.plugin_manager)
            if self.settings_plugin:
                self.settings_adapter.set_settings_plugin(self.settings_plugin)
                print("VK Parser: Плагин настроек подключен через PluginManager")
            else:
                print("VK Parser: Используется простой менеджер настроек")
        else:
            self.settings_adapter = settings_adapter
            self.settings_plugin = getattr(settings_adapter, "settings_plugin", None)

        # Получаем плагины через PluginManager
        self.token_manager = self.plugin_manager.get_plugin("token_manager")
        if not self.token_manager:
            raise RuntimeError("TokenManagerPlugin не инициализирован через PluginManager")

        self.token_limiter = TokenLimiter(self.token_manager.list_vk_tokens(), cooldown_seconds=60)

        # Инициализируем VKSearchPlugin через PluginManager
        self.vk_search_plugin = self.plugin_manager.get_plugin("vk_search")
        if self.vk_search_plugin and hasattr(self.vk_search_plugin, "initialize"):
            self.vk_search_plugin.initialize()

        # Получаем дополнительные плагины
        self.database_plugin = self.plugin_manager.get_plugin("database")
        self.filter_plugin = self.plugin_manager.get_plugin("filter")
        self.text_processing_plugin = self.plugin_manager.get_plugin("text_processing")

        print("VK Parser: Все плагины получены через PluginManager")

        # Настройка интерфейса
        self.setup_ui()

        # Загружаем сохраненные данные
        self.load_saved_token()
        self.load_sheets_url()
        self.load_sheets_range_settings()
        self._update_task_history()  # Загружаем историю задач из базы данных

        # Автоматическое подключение токенов при запуске
        self.root.after(500, self.auto_connect_tokens)
        # Автоматическая проверка токена при запуске
        self.root.after(1000, self.auto_check_token)
        # Автоматическое подключение Google Sheets
        self.root.after(1200, self.auto_connect_google_sheets)

    def _init_token_manager(self):
        """Инициализирует упрощенный TokenManager"""
        try:
            # Создаем простой менеджер токенов без зависимостей
            token_manager = self.settings_plugin.get_token_manager()  # Используем плагин настроек
            print("TokenManagerPlugin инициализирован")
            return token_manager
        except Exception as e:
            print(f"Ошибка инициализации TokenManager: {e}")
            return None

    def _init_google_sheets_plugin(self):
        try:
            plugin = self.plugin_manager.get_plugin("google_sheets")
            plugin.initialize()
            print("GoogleSheetsPlugin инициализирован")
            return plugin
        except Exception as e:
            print(f"Ошибка инициализации GoogleSheetsPlugin: {e}")
            return None

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
        left_canvas = tk.Canvas(left_frame, bg="#2b2b2b", highlightthickness=0, height=600, width=500)
        left_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=left_canvas.yview)
        left_scrollable_frame = ttk.Frame(left_canvas)

        left_scrollable_frame.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))

        left_canvas.create_window((0, 0), window=left_scrollable_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        # Размещаем canvas и scrollbar
        left_canvas.grid(row=0, column=0, sticky="nsew")
        left_scrollbar.grid(row=0, column=1, sticky="ns")

        # Настройка весов для прокрутки
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # Статус подключения к ВК
        self.connection_status = ttk.Label(
            left_scrollable_frame, text="Статус: Проверка подключения...", foreground="orange", font=("Arial", 9)
        )
        self.connection_status.grid(row=0, column=0, sticky="w", pady=(0, 2))
        # Статус подключения к Google Sheets
        self.gsheets_status = ttk.Label(
            left_scrollable_frame, text="Google Sheets: ...", foreground="orange", font=("Arial", 9)
        )
        self.gsheets_status.grid(row=1, column=0, sticky="w", pady=(0, 10))

        # Кнопка 'Начать поиск' в отдельном контейнере
        search_frame = ttk.Frame(left_scrollable_frame)
        search_frame.grid(row=2, column=0, sticky="w", pady=(10, 15), padx=5)
        ttk.Button(search_frame, text="НАЧАТЬ ПОИСК", command=self.start_vk_search, width=24).pack(
            side="left", padx=(0, 5)
        )

        # Ключевые фразы
        ttk.Label(left_scrollable_frame, text="Ключевые фразы:", font=("Arial", 11, "bold")).grid(
            row=3, column=0, sticky="w", pady=(10, 2)
        )
        ttk.Label(left_scrollable_frame, text="По одной ключевой фразе в строке.", font=("Arial", 9)).grid(
            row=4, column=0, sticky="w", pady=(0, 2)
        )

        self.keywords_text = tk.Text(left_scrollable_frame, height=8, width=55)
        self.keywords_text.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self.keywords_text.bind("<KeyRelease>", self._on_keywords_changed)

        # Период поиска
        ttk.Label(
            left_scrollable_frame, text="Период поиска новостей (обязательный параметр):", font=("Arial", 11, "bold")
        ).grid(row=6, column=0, sticky="w", pady=(0, 2))

        # Правила
        rules_frame = ttk.Frame(left_scrollable_frame)
        rules_frame.grid(row=7, column=0, sticky="w", pady=(0, 5))
        ttk.Label(rules_frame, text="• поиск возможен по новостям не старше 3-х лет", font=("Arial", 9)).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(rules_frame, text="• максимальный период поиска - 1 год", font=("Arial", 9)).grid(
            row=1, column=0, sticky="w"
        )

        # Даты и время
        dates_frame = ttk.Frame(left_scrollable_frame)
        dates_frame.grid(row=8, column=0, sticky="w", pady=(0, 5))

        # Первая дата с временем
        ttk.Label(dates_frame, text="С:", font=("Arial", 9)).grid(row=0, column=0, sticky="w")
        self.start_date_var = tk.StringVar(value="18.07.2025")
        self.start_date_entry = ttk.Entry(dates_frame, textvariable=self.start_date_var, width=12)
        self.start_date_entry.grid(row=0, column=1, padx=(3, 0))
        ttk.Button(dates_frame, text="×", width=2, command=lambda: self.start_date_var.set("")).grid(
            row=0, column=2, padx=(3, 0)
        )

        ttk.Label(dates_frame, text="время:", font=("Arial", 9)).grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.start_time_var = tk.StringVar(value="07:00")
        self.start_time_entry = ttk.Entry(dates_frame, textvariable=self.start_time_var, width=8)
        self.start_time_entry.grid(row=0, column=4, padx=(3, 0))

        # Вторая дата с временем
        ttk.Label(dates_frame, text="По:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.end_date_var = tk.StringVar(value="19.07.2025")
        self.end_date_entry = ttk.Entry(dates_frame, textvariable=self.end_date_var, width=12)
        self.end_date_entry.grid(row=1, column=1, padx=(3, 0), pady=(3, 0))
        ttk.Button(dates_frame, text="×", width=2, command=lambda: self.end_date_var.set("")).grid(
            row=1, column=2, padx=(3, 0), pady=(3, 0))

        ttk.Label(dates_frame, text="время:", font=("Arial", 9)).grid(
            row=1, column=3, sticky="w", padx=(8, 0), pady=(3, 0)
        )
        self.end_time_var = tk.StringVar(value="06:00")
        self.end_time_entry = ttk.Entry(dates_frame, textvariable=self.end_time_var, width=8)
        self.end_time_entry.grid(row=1, column=4, padx=(3, 0), pady=(3, 0))

        # Быстрый выбор периодов
        quick_dates_frame = ttk.Frame(left_scrollable_frame)
        quick_dates_frame.grid(row=9, column=0, sticky="w", pady=(0, 8))
        ttk.Label(quick_dates_frame, text="За месяц, неделю, три дня, день", font=("Arial", 9)).grid(
            row=0, column=0, sticky="w"
        )

        # Точное вхождение
        self.exact_match_var = tk.BooleanVar(value=True)
        exact_match_check = ttk.Checkbutton(
            left_scrollable_frame, text="Точное вхождение поисковой фразы", variable=self.exact_match_var
        )
        exact_match_check.grid(row=10, column=0, sticky="w", pady=(0, 3))

        # Отключение локальной фильтрации
        self.disable_local_filtering_var = tk.BooleanVar(value=False)
        disable_local_filtering_check = ttk.Checkbutton(
            left_scrollable_frame,
            text="Отключить локальную фильтрацию (использовать только API VK)",
            variable=self.disable_local_filtering_var
        )
        disable_local_filtering_check.grid(row=10, column=0, sticky="w", pady=(20, 8))

        # Минус слова
        ttk.Label(left_scrollable_frame, text="Минус слова:", font=("Arial", 11, "bold")).grid(
            row=11, column=0, sticky="w", pady=(0, 2)
        )
        ttk.Label(left_scrollable_frame, text="По одному минус слову/фразе в строке.", font=("Arial", 9)).grid(
            row=12, column=0, sticky="w", pady=(0, 2)
        )

        self.minus_words_text = tk.Text(left_scrollable_frame, height=3, width=55)
        self.minus_words_text.grid(row=13, column=0, sticky="ew", pady=(0, 8))

        # Вложения
        ttk.Label(left_scrollable_frame, text="Вложения:", font=("Arial", 11, "bold")).grid(
            row=14, column=0, sticky="w", pady=(0, 2)
        )
        self.attachments_var = tk.StringVar(value="Без разницы")
        attachments_combo = ttk.Combobox(
            left_scrollable_frame, textvariable=self.attachments_var, state="readonly", width=25
        )
        attachments_combo["values"] = ["Без разницы", "Фото", "Видео", "Без вложения"]
        attachments_combo.grid(row=15, column=0, sticky="w", pady=(0, 10))

        # Кнопка загрузки из Google Sheets
        ttk.Label(left_scrollable_frame, text="Автоматическая загрузка:", font=("Arial", 11, "bold")).grid(
            row=16, column=0, sticky="w", pady=(10, 2)
        )

        # Поле ввода ссылки на Google Sheets
        ttk.Label(left_scrollable_frame, text="Ссылка на Google Sheets:", font=("Arial", 9)).grid(
            row=17, column=0, sticky="w", pady=(0, 2)
        )
        self.sheets_url_var = tk.StringVar()
        self.sheets_url_entry = ttk.Entry(left_scrollable_frame, textvariable=self.sheets_url_var, width=55)
        self.sheets_url_entry.grid(row=18, column=0, sticky="ew", pady=(0, 5))

        # Привязываем событие изменения ссылки для автоматического сохранения
        self.sheets_url_var.trace("w", lambda *args: self.save_sheets_url())

        # Настройки диапазона
        range_frame = ttk.LabelFrame(left_scrollable_frame, text="Настройки диапазона", padding="5")
        range_frame.grid(row=19, column=0, sticky="ew", pady=(0, 5))

        # Диапазон листов по датам
        ttk.Label(range_frame, text="Диапазон листов:", font=("Arial", 9)).grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )

        sheets_range_frame = ttk.Frame(range_frame)
        sheets_range_frame.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=(0, 2))

        ttk.Label(sheets_range_frame, text="от:", font=("Arial", 9)).pack(side="left")
        self.sheet_from_var = tk.StringVar()
        self.sheet_from_combo = ttk.Combobox(
            sheets_range_frame, textvariable=self.sheet_from_var, width=12, state="readonly"
        )
        self.sheet_from_combo.pack(side="left", padx=(3, 5))

        ttk.Label(sheets_range_frame, text="до:", font=("Arial", 9)).pack(side="left")
        self.sheet_to_var = tk.StringVar()
        self.sheet_to_combo = ttk.Combobox(
            sheets_range_frame, textvariable=self.sheet_to_var, width=12, state="readonly"
        )
        self.sheet_to_combo.pack(side="left", padx=(3, 0))

        # Кнопка обновления списка листов
        ttk.Button(range_frame, text="Обновить список листов", command=self.update_sheets_list, width=20).grid(
            row=1, column=0, columnspan=2, pady=(5, 0)
        )

        # Диапазон ячеек
        ttk.Label(range_frame, text="Диапазон ячеек:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=(5, 2))
        self.cell_range_var = tk.StringVar(value="A:Z")
        self.cell_range_entry = ttk.Entry(range_frame, textvariable=self.cell_range_var, width=20)
        self.cell_range_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=(5, 2))

        # Привязываем настройки к автосохранению
        if self.settings_adapter:
            # Привязываем переменные к настройкам
            self.settings_adapter.bind_variable_to_setting(self.sheets_url_var, "sheets", "url")
            self.settings_adapter.bind_variable_to_setting(self.cell_range_var, "sheets", "cell_range")
            self.settings_adapter.bind_variable_to_setting(self.sheet_from_var, "sheets", "sheet_from")
            self.settings_adapter.bind_variable_to_setting(self.sheet_to_var, "sheets", "sheet_to")
            self.settings_adapter.bind_variable_to_setting(self.exact_match_var, "parser", "exact_match")
            self.settings_adapter.bind_variable_to_setting(self.attachments_var, "parser", "attachments")
            self.settings_adapter.bind_variable_to_setting(self.disable_local_filtering_var, "parser", "disable_local_filtering")

            # Привязываем текстовые виджеты к настройкам
            self.settings_adapter.bind_text_widget_to_setting(self.keywords_text, "parser", "keywords")
            self.settings_adapter.bind_text_widget_to_setting(self.minus_words_text, "parser", "minus_words")

            # Привязываем даты к настройкам
            self.settings_adapter.bind_variable_to_setting(self.start_date_var, "parser", "start_date")
            self.settings_adapter.bind_variable_to_setting(self.start_time_var, "parser", "start_time")
            self.settings_adapter.bind_variable_to_setting(self.end_date_var, "parser", "end_date")
            self.settings_adapter.bind_variable_to_setting(self.end_time_var, "parser", "end_time")
        else:
            # Fallback к старому способу
            self.cell_range_var.trace("w", lambda *args: self.save_sheets_range_settings())
            self.sheet_from_var.trace("w", lambda *args: self.save_sheets_range_settings())
            self.sheet_to_var.trace("w", lambda *args: self.save_sheets_range_settings())

            self.start_date_var.trace("w", lambda *args: self.save_window_settings())
            self.start_time_var.trace("w", lambda *args: self.save_window_settings())
            self.end_date_var.trace("w", lambda *args: self.save_window_settings())
            self.end_time_var.trace("w", lambda *args: self.save_window_settings())
            self.exact_match_var.trace("w", lambda *args: self.save_window_settings())
            self.attachments_var.trace("w", lambda *args: self.save_window_settings())
            self.disable_local_filtering_var.trace("w", lambda *args: self.save_window_settings())

            self.keywords_text.bind("<KeyRelease>", lambda event: self.save_window_settings())
            self.minus_words_text.bind("<KeyRelease>", lambda event: self.save_window_settings())

        # Подсказка
        ttk.Label(range_frame, text="Примеры: A:Z, A1:D100, Sheet1!A:Z", font=("Arial", 8), foreground="gray").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(2, 0)
        )

        sheets_frame = ttk.Frame(left_scrollable_frame)
        sheets_frame.grid(row=20, column=0, sticky="w", pady=(0, 10))

        ttk.Button(sheets_frame, text="Загрузить из Google Sheets", command=self.load_from_google_sheets).pack(
            side="left", padx=(0, 5)
        )

        # Статус загрузки
        self.sheets_status = ttk.Label(left_scrollable_frame, text="", font=("Arial", 9))
        self.sheets_status.grid(row=21, column=0, sticky="w", pady=(0, 10))

        # Строка прогресса поиска
        self.progress_label = ttk.Label(left_scrollable_frame, text="", font=("Arial", 9), foreground="blue")
        self.progress_label.grid(row=22, column=0, sticky="w", pady=(0, 5))
        # Прогресс-бар поиска
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(left_scrollable_frame, variable=self.progress_var, maximum=100, length=350)
        self.progress_bar.grid(row=23, column=0, sticky="ew", pady=(0, 10))

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
        self.tasks_tree = ttk.Treeview(
            history_frame, columns=("date", "time", "count", "si", "views", "status"), show="headings", height=8
        )
        self.tasks_tree.heading("date", text="Дата")
        self.tasks_tree.heading("time", text="Время")
        self.tasks_tree.heading("count", text="Кол-во")
        self.tasks_tree.heading("si", text="SI")
        self.tasks_tree.heading("views", text="Просмотры")
        self.tasks_tree.heading("status", text="Статус")
        self.tasks_tree.column("date", width=80)
        self.tasks_tree.column("time", width=80)
        self.tasks_tree.column("count", width=60)
        self.tasks_tree.column("si", width=80)
        self.tasks_tree.column("views", width=100)
        self.tasks_tree.column("status", width=80)

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

        self.results_tree = ttk.Treeview(
            results_frame,
            columns=("link", "text", "type", "author", "author_link", "date", "likes", "comments", "reposts", "views"),
            show="headings",
            height=10,
        )
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
        ttk.Label(
            info_frame,
            text="История задач хранится 30 дней. Для неограниченного хранения установите флаг ★",
            foreground="orange",
        ).pack(anchor="w")
        ttk.Label(info_frame, text="Что означают статусы задач >", foreground="blue", cursor="hand2").pack(anchor="w")

        # Кнопка сохранения результатов
        # Удалить старую кнопку сохранения результатов
        # self.save_results_button = ttk.Button(right_frame, text="Сохранить результаты", command=self.save_vk_results)
        # self.save_results_button.pack(side="bottom", fill="x", pady=(5, 0))
        # Оставить только новую кнопку экспорта
        self.export_results_button = ttk.Button(
            right_frame, text="Экспортировать результаты", command=self._export_current_results
        )
        self.export_results_button.pack(side="bottom", fill="x", pady=(5, 0))

        # Настройка весов
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)

        # Настройка горячих клавиш для macOS
        self._setup_hotkeys()

    def _setup_hotkeys(self):
        """Настройка горячих клавиш через HotkeysPlugin"""
        try:
            # Получаем плагин горячих клавиш
            hotkeys_plugin = self.plugin_manager.get_plugin("hotkeys")
            if not hotkeys_plugin:
                print("⚠️ HotkeysPlugin не найден")
                return

            # Собираем все виджеты для регистрации
            widgets_to_register = []

            # Entry виджеты
            if hasattr(self, 'start_date_entry'):
                widgets_to_register.append(self.start_date_entry)
            if hasattr(self, 'start_time_entry'):
                widgets_to_register.append(self.start_time_entry)
            if hasattr(self, 'end_date_entry'):
                widgets_to_register.append(self.end_date_entry)
            if hasattr(self, 'end_time_entry'):
                widgets_to_register.append(self.end_time_entry)
            if hasattr(self, 'sheets_url_entry'):
                widgets_to_register.append(self.sheets_url_entry)
            if hasattr(self, 'cell_range_entry'):
                widgets_to_register.append(self.cell_range_entry)

            # Text виджеты
            if hasattr(self, 'keywords_text'):
                widgets_to_register.append(self.keywords_text)
            if hasattr(self, 'minus_words_text'):
                widgets_to_register.append(self.minus_words_text)

            # Регистрируем все виджеты
            success_count = hotkeys_plugin.register_multiple_widgets(widgets_to_register)
            print(f"🎮 Горячие клавиши настроены через HotkeysPlugin: {success_count}/{len(widgets_to_register)} виджетов")

        except Exception as e:
            print(f"❌ Ошибка настройки горячих клавиш: {e}")
            # Fallback к старому методу
            self._setup_hotkeys_fallback()

    def _setup_hotkeys_fallback(self):
        """Резервный метод настройки горячих клавиш"""
        print("🔄 Используется резервный метод горячих клавиш")

    def load_saved_token(self):
        """Загрузка сохраненного токена через TokenManagerPlugin"""
        try:
            if self.token_manager:
                # Пытаемся загрузить токен через плагин
                token = self.token_manager.get_token("vk")
                if token:
                    self.token_var.set(token)
                    print("Токен VK загружен через TokenManagerPlugin")
                    return

            # Fallback к файлу если плагин недоступен
            token_file = os.path.join("config", "vk_token.txt")
            if os.path.exists(token_file):
                with open(token_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("//"):
                            self.token_var.set(line)
                            # Сохраняем в плагин если он доступен
                            if self.token_manager:
                                self.token_manager.add_token("vk", line)
                            print("Токен VK загружен из файла")
                            break
        except Exception as e:
            print(f"Ошибка загрузки токена: {e}")

    def save_token_to_manager(self, token: str):
        """Сохраняет токен в TokenManagerPlugin"""
        try:
            if self.token_manager:
                self.token_manager.add_token("vk", token)
                print("Токен VK сохранен в TokenManagerPlugin")
                return True
        except Exception as e:
            print(f"Ошибка сохранения токена в плагин: {e}")
        return False

    def auto_check_token(self):
        """Автоматическая проверка токена при запуске"""
        try:
            token = self.token_var.get().strip()
            if token:
                # Проверяем токен
                import requests

                test_url = f"https://api.vk.com/method/users.get?access_token={token}&v=5.131"
                response = requests.get(test_url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        self.connection_status.config(text="Статус: Подключено", foreground="green")
                        print("✅ VK API подключение успешно")
                        return True
                    else:
                        self.connection_status.config(text="Статус: Неверный токен", foreground="red")
                        print("❌ VK токен невалиден")
                        return False
                else:
                    self.connection_status.config(text="Статус: Ошибка подключения", foreground="red")
                    print("❌ Ошибка подключения к VK API")
                    return False
            else:
                self.connection_status.config(text="Статус: Токен не найден", foreground="red")
                print("❌ VK токен не найден")
                return False
        except Exception as e:
            self.connection_status.config(text="Статус: Ошибка проверки", foreground="red")
            print(f"❌ Ошибка проверки токена: {e}")
            return False

    def load_sheets_url(self):
        """Загрузка URL Google Sheets"""
        try:
            if self.settings_adapter:
                url = self.settings_adapter.get_setting("sheets", "url", "")
                if url:
                    self.sheets_url_var.set(url)
            else:
                # Fallback к старому способу
                if os.path.exists("sheets_url.txt"):
                    with open("sheets_url.txt", "r") as f:
                        url = f.read().strip()
                        if url:
                            self.sheets_url_var.set(url)
        except Exception as e:
            print(f"Ошибка загрузки URL: {str(e)}")

    def load_sheets_range_settings(self):
        """Загрузка настроек диапазона Google Sheets"""
        try:
            if self.settings_adapter:
                cell_range = self.settings_adapter.get_setting("sheets", "cell_range", "A:Z")
                sheet_from = self.settings_adapter.get_setting("sheets", "sheet_from", "")
                sheet_to = self.settings_adapter.get_setting("sheets", "sheet_to", "")

                if cell_range:
                    self.cell_range_var.set(cell_range)
                if sheet_from:
                    self.sheet_from_var.set(sheet_from)
                if sheet_to:
                    self.sheet_to_var.set(sheet_to)
            else:
                # Fallback к старому способу
                if os.path.exists("data/settings.json"):
                    with open("data/settings.json", "r", encoding="utf-8") as f:
                        _ = json.load(f)  # Загружаем настройки но не используем пока
                        # Здесь можно добавить загрузку настроек диапазона
        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")

    def start_vk_search(self):
        """Запуск асинхронного поиска в ВК (теперь с преобразованием дат и времени через vk_time_utils)"""
        try:
            keywords = self.keywords_text.get("1.0", tk.END).strip().splitlines()
            keywords = [k.strip() for k in keywords if k.strip()]
            if not keywords:
                messagebox.showerror("Ошибка", "Введите ключевые фразы")
                return
            start_date = self.start_date_var.get().strip()
            end_date = self.end_date_var.get().strip()
            start_time = self.start_time_var.get().strip()
            end_time = self.end_time_var.get().strip()
            exact_match = self.exact_match_var.get()
            minus_words = self.minus_words_text.get("1.0", tk.END).strip().splitlines()
            minus_words = [w.strip() for w in minus_words if w.strip()]
            # Получаем токен из лимитера
            token = self.token_limiter.get_token()
            if not token:
                messagebox.showerror("Ошибка", "Нет доступных VK токенов (все на cooldown)")
                return
            # Для массового парсинга: каждый запрос — отдельная ключевая фраза
            api_keywords = keywords
            # Преобразуем даты и время в timestamp через vk_time_utils
            try:
                start_ts = to_vk_timestamp(start_date, start_time)
                end_ts = to_vk_timestamp(end_date, end_time)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка преобразования даты/времени: {e}")
                return
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            threading.Thread(
                target=self._run_async_search_thread_safe,
                args=(
                    keywords,
                    api_keywords,
                    start_ts,
                    end_ts,
                    exact_match,
                    minus_words,
                    token,
                    start_date,
                    start_time,
                    end_date,
                    end_time,
                ),
                daemon=True,
            ).start()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска поиска: {str(e)}")

    def _run_async_search_thread_safe(
        self,
        keywords,
        api_keywords,
        start_ts,
        end_ts,
        exact_match,
        minus_words,
        token,
        start_date,
        start_time,
        end_date,
        end_time,
    ):
        """
        Упрощённый thread-safe поиск через новую архитектуру PluginManager
        """
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Callback для обновления прогресса из другого потока
            def update_progress(message: str, progress: int):
                # Thread-safe обновление UI через after()
                self.parent_frame.after(0, lambda: self._update_ui_progress(message, progress))

            # Используем новую архитектуру PluginManager
            result = loop.run_until_complete(
                self.plugin_manager.coordinate_full_search(
                    keywords=keywords,
                    api_keywords=api_keywords,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    exact_match=exact_match,
                    minus_words=minus_words,
                    start_date=start_date,
                    start_time=start_time,
                    end_date=end_date,
                    end_time=end_time,
                    progress_callback=update_progress
                )
            )

            # Thread-safe обновление UI с результатами
            self.parent_frame.after(0, lambda: self._handle_search_success(result))

        except Exception as e:
            # Thread-safe обработка ошибок
            error_msg = f"Ошибка поиска: {str(e)}"
            self.parent_frame.after(0, lambda: self._handle_search_error(error_msg))

        finally:
            loop.close()
            # Thread-safe сброс UI
            self.parent_frame.after(0, self._reset_search_ui)

    def _update_ui_progress(self, message: str, progress: int):
        """Thread-safe обновление прогресса UI"""
        self._set_progress(message)
        self.progress_var.set(progress)
        self.progress_bar.update()

    def _handle_search_success(self, result):
        """Thread-safe обработка успешного результата поиска"""
        if result["filepath"] and os.path.exists(result["filepath"]):
            self._display_results_from_csv(result["filepath"])
            self._load_tasks_from_results_folder()
            print(f"✅ Поиск завершён: {result['posts_count']} постов за {result['elapsed_time']:.1f}с")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать файл результатов")

    def _handle_search_error(self, error_msg: str):
        """Thread-safe обработка ошибки поиска"""
        messagebox.showerror("Ошибка", error_msg)
        print(f"❌ {error_msg}")

    def _reset_search_ui(self):
        """Thread-safe сброс UI после поиска"""
        self.progress_var.set(0)
        self.progress_bar.update()
        self._set_progress("")

    async def _async_search_and_display(
        self,
        keywords,
        api_keywords,
        start_ts,
        end_ts,
        exact_match,
        minus_words,
        token_limiter,
        start_date,
        start_time,
        end_date,
        end_time,
    ):
        """
        Упрощённый метод поиска - только UI логика.
        Вся бизнес-логика делегируется PluginManager.coordinate_full_search()
        """
        try:
            # Callback для обновления прогресса
            def update_progress(message: str, progress: int):
                self._set_progress(message)
                self.progress_var.set(progress)
                self.progress_bar.update()

            # Делегируем всю логику PluginManager
            result = await self.plugin_manager.coordinate_full_search(
                keywords=keywords,
                api_keywords=api_keywords,
                start_ts=start_ts,
                end_ts=end_ts,
                exact_match=exact_match,
                minus_words=minus_words,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
                progress_callback=update_progress,
                disable_local_filtering=self.disable_local_filtering_var.get()
            )

            # Только отображение результатов
            if result["filepath"] and os.path.exists(result["filepath"]):
                self._display_results_from_csv(result["filepath"])
                print(f"✅ Поиск завершён: {result['posts_count']} постов за {result['elapsed_time']:.1f}с")

                # Обновляем историю задач после завершения поиска
                self._update_task_history()
            else:
                messagebox.showerror("Ошибка", "Не удалось создать файл результатов")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {str(e)}")
            print(f"❌ Ошибка поиска: {e}")

        finally:
            # Сброс UI состояния
            self.progress_var.set(0)
            self.progress_bar.update()
            self._set_progress("")

    def _set_progress(self, text):
        self.progress_label.config(text=text)
        self.progress_label.update_idletasks()

    def _update_task_history(self):
        """Обновление истории задач из базы данных"""
        try:
            # Очищаем текущий список
            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)

            # Получаем задачи из базы данных
            database_plugin = self.plugin_manager.get_plugin("database")
            if not database_plugin:
                print("❌ DatabasePlugin недоступен для обновления истории")
                return

            tasks = database_plugin.get_tasks()

            for task in tasks:
                # Форматируем дату
                from datetime import datetime
                try:
                    created_at = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                    date_str = created_at.strftime("%d.%m.%Y")
                    time_str = created_at.strftime("%H:%M:%S")
                except:
                    date_str = task["created_at"][:10] if task["created_at"] else ""
                    time_str = task["created_at"][11:19] if len(task["created_at"]) > 10 else ""

                # Добавляем в таблицу
                self.tasks_tree.insert(
                    "",
                    "end",
                    values=(
                        date_str,
                        time_str,
                        task["total_posts"],
                        task["total_SI"],
                        task["total_views"],
                        task["status"]
                    )
                )

            print(f"✅ История задач обновлена: {len(tasks)} задач")

        except Exception as e:
            print(f"❌ Ошибка обновления истории задач: {e}")

    def save_window_settings(self):
        """Сохранение настроек парсера"""
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
                "disable_local_filtering": self.disable_local_filtering_var.get(),
                "vk_token": self.token_var.get(),
                "last_saved": datetime.now().isoformat(),
            }

            if self.settings_adapter:
                self.settings_adapter.save_parser_settings(settings)
            else:
                # Fallback к старому способу
                os.makedirs("data", exist_ok=True)
                with open("data/settings.json", "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Ошибка сохранения настроек: {str(e)}")

    def update_sheets_list(self):
        """Обновление списка листов Google Sheets"""
        try:
            url = self.sheets_url_var.get().strip()
            if not url:
                messagebox.showwarning("Внимание", "Сначала введите ссылку на Google Sheets!")
                return
            if not self.google_sheets_plugin:
                messagebox.showerror("Ошибка", "Плагин Google Sheets недоступен")
                return
            # Открываем таблицу
            if not self.google_sheets_plugin.open_spreadsheet(url):
                messagebox.showerror("Ошибка", "Не удалось открыть таблицу по ссылке")
                return
            # Получаем список листов
            worksheets = self.google_sheets_plugin.list_worksheets()
            if not worksheets:
                messagebox.showerror("Ошибка", "Не удалось получить список листов или таблица пуста")
                return
            # Обновляем значения в Combobox
            self.sheet_from_combo.configure(values=worksheets)
            self.sheet_to_combo.configure(values=worksheets)
            # Сбрасываем выбранные значения
            self.sheet_from_var.set(worksheets[0])
            self.sheet_to_var.set(worksheets[-1])
            messagebox.showinfo("Информация", f"Список листов обновлен: {', '.join(worksheets)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить список листов: {str(e)}")

    def load_from_google_sheets(self):
        """Загрузка данных из Google Sheets и очистка через TextProcessingPlugin"""
        try:
            # Получаем параметры из интерфейса
            spreadsheet_url = self.sheets_url_var.get().strip()
            sheet_from = self.sheet_from_var.get().strip()
            sheet_to = self.sheet_to_var.get().strip()
            cell_range = self.cell_range_var.get().strip()

            if not spreadsheet_url or not sheet_from or not sheet_to or not cell_range:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все параметры для загрузки из Google Sheets.")
                return

            # Инициализируем подключение и открываем таблицу
            if not self.google_sheets_plugin.initialize_connection():
                messagebox.showerror("Ошибка", "Не удалось инициализировать подключение к Google Sheets.")
                return
            if not self.google_sheets_plugin.open_spreadsheet(spreadsheet_url):
                messagebox.showerror("Ошибка", "Не удалось открыть таблицу по указанному URL.")
                return

            # Загружаем данные из диапазона листов
            all_texts, processed_sheets = self.google_sheets_plugin.load_data_from_sheets(
                sheet_from, sheet_to, cell_range
            )
            if not all_texts:
                messagebox.showwarning("Внимание", "Не найдено ни одной ключевой фразы в указанном диапазоне.")
                return

            # Очищаем тексты через TextProcessingPlugin
            cleaned_texts = [self.text_processing_plugin.clean_text_completely(t) for t in all_texts]
            cleaned_texts = [t for t in cleaned_texts if t]  # Убираем пустые строки

            # Вставляем в поле ключевых фраз
            self.keywords_text.delete("1.0", tk.END)
            self.keywords_text.insert("1.0", "\n".join(cleaned_texts))

            messagebox.showinfo(
                "Успех",
                f"Загружено и очищено {len(cleaned_texts)} ключевых фраз из листов: {', '.join(processed_sheets)}",
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {str(e)}")

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
                "sheet_to": self.sheet_to_var.get(),
                "url": self.sheets_url_var.get(),
            }

            if self.settings_adapter:
                self.settings_adapter.save_sheets_settings(settings)
            else:
                # Fallback к старому способу
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
        # Двойной клик — открывает окно настроек задачи через DataManagerPlugin
        item_id = self.tasks_tree.identify_row(event.y)
        if not item_id:
            return
        tags = self.tasks_tree.item(item_id, "tags")
        if tags and tags[0]:
            # В новой архитектуре tags[0] содержит task_id, а не filepath
            task_id = int(tags[0]) if tags[0].isdigit() else None
            database_plugin = self.plugin_manager.get_plugin("database")
            if database_plugin and task_id:
                # Получаем информацию о задаче из БД
                tasks = database_plugin.get_tasks()
                task_meta = None
                for task in tasks:
                    if task.get("id") == task_id:
                        task_meta = task
                        break

                if task_meta:
                    # Конвертируем формат задачи для совместимости с интерфейсом
                    self._show_task_settings_window(task_meta, task_id)
                else:
                    print(f"⚠️ Задача #{task_id} не найдена в базе данных")

    def _show_task_settings_window(self, meta, filepath):
        """Открывает окно с настройками задачи и итоговыми метриками, позволяет повторно запустить задачу."""
        win = tk.Toplevel(self.root)
        win.title("Настройки задачи и метрики")
        win.geometry("500x600")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)
        # Настройки задачи
        ttk.Label(frame, text="Параметры задачи", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))
        params = [
            ("Ключевые слова", ", ".join(meta.get("keywords", []))),
            ("Дата с", meta.get("start_date", "")),
            ("Дата по", meta.get("end_date", "")),
            ("Точное вхождение", str(meta.get("exact_match", ""))),
            ("Минус-слова", ", ".join(meta.get("minus_words", []))),
        ]
        for label, value in params:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label + ":", width=18).pack(side="left")
            ttk.Label(row, text=value, wraplength=350).pack(side="left", fill="x", expand=True)
        # Итоговые метрики
        ttk.Label(frame, text="\nИтоговые метрики", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
        stats = meta.get("stats", {})
        stats_params = [
            ("Кол-во ссылок", meta.get("count", 0)),
            ("Сумма SI (лайки+репосты+комменты)", stats.get("total_SI", 0)),
            ("Лайки", stats.get("total_likes", 0)),
            ("Комментарии", stats.get("total_comments", 0)),
            ("Репосты", stats.get("total_reposts", 0)),
            ("Просмотры", stats.get("total_views", 0)),
        ]
        for label, value in stats_params:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label + ":", width=28).pack(side="left")
            ttk.Label(row, text=str(value)).pack(side="left", fill="x", expand=True)

        # Кнопка повторного запуска
        def rerun_task():
            win.destroy()
            self._rerun_task_from_meta(meta)

        ttk.Button(frame, text="Запустить задачу с этими настройками", command=rerun_task).pack(pady=20)

    def _rerun_task_from_meta(self, meta):
        """Повторно запускает задачу с настройками из meta.json"""
        try:
            keywords = meta.get("keywords", [])
            start_date = meta.get("start_date", "")
            end_date = meta.get("end_date", "")
            exact_match = meta.get("exact_match", True)
            minus_words = meta.get("minus_words", [])
            # Можно добавить другие параметры при необходимости
            # Преобразуем даты и время в timestamp через vk_time_utils
            start_time = meta.get("start_time", "07:00")
            end_time = meta.get("end_time", "06:00")
            start_ts = to_vk_timestamp(start_date, start_time)
            end_ts = to_vk_timestamp(end_date, end_time)
            token = self.token_limiter.get_token()
            if not token:
                messagebox.showerror("Ошибка", "Нет доступных VK токенов (все на cooldown)")
                return
            threading.Thread(
                target=self._run_async_search_thread_safe,
                args=(
                    keywords,
                    keywords,
                    start_ts,
                    end_ts,
                    exact_match,
                    minus_words,
                    token,
                    start_date,
                    start_time,
                    end_date,
                    end_time,
                ),
                daemon=True,
            ).start()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось повторно запустить задачу: {str(e)}")

    def display_results_in_treeview(self, df):
        """Отображение результатов в Treeview"""
        try:
            # Очищаем предыдущие результаты
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            # Добавляем новые результаты
            for index, row in df.iterrows():
                self.results_tree.insert(
                    "",
                    "end",
                    values=(
                        row.get("link", ""),
                        row.get("text", ""),
                        row.get("type", ""),
                        row.get("author", ""),
                        row.get("author_link", ""),
                        row.get("date", ""),
                        row.get("likes", ""),
                        row.get("comments", ""),
                        row.get("reposts", ""),
                        row.get("views", ""),
                    ),
                )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить результаты: {str(e)}")

    def _display_results_from_csv(self, filepath):
        """Загружает CSV и отображает результаты в Treeview"""
        try:
            df = pd.read_csv(filepath)
            self.display_results_in_treeview(df)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить результаты из файла: {str(e)}")

    def auto_connect_tokens(self):
        """Автоматическое подключение всех токенов при запуске"""
        try:
            print("🔄 Автоподключение токенов...")

            if not self.token_manager:
                print("❌ TokenManager недоступен")
                return

            # Подключаем VK токен
            vk_token = self.token_manager.get_token("vk")
            if vk_token:
                self.token_var.set(vk_token)
                print("✅ VK токен подключен")

                # Проверяем валидность
                if self.token_manager._is_token_valid("vk"):
                    self.connection_status.config(text="Статус: Подключено", foreground="green")
                    print("✅ VK токен валиден")
                else:
                    self.connection_status.config(text="Статус: Неверный токен", foreground="red")
                    print("❌ VK токен невалиден")
            else:
                # Пытаемся загрузить из файла
                self._load_token_from_file()
                print("📁 VK токен загружен из файла")

            # Подключаем Google Sheets токен
            sheets_token = self.token_manager.get_token("google_sheets")
            if sheets_token:
                print("✅ Google Sheets токен подключен")
            else:
                print("ℹ️ Google Sheets токен не найден")

            # Подключаем другие токены если есть
            all_tokens = self.token_manager.list_tokens()
            for token_info in all_tokens:
                service = token_info.get("service", "")
                if service not in ["vk", "google_sheets"]:
                    print(f"✅ Токен {service} подключен")

            print(f"🎯 Всего подключено токенов: {len(all_tokens)}")

        except Exception as e:
            print(f"❌ Ошибка автоподключения токенов: {e}")

    def _load_token_from_file(self):
        """Загружает токен из файла и сохраняет в менеджер"""
        try:
            token_file = os.path.join("config", "vk_token.txt")
            if os.path.exists(token_file):
                with open(token_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("//"):
                            self.token_var.set(line)
                            # Сохраняем в менеджер
                            if self.token_manager:
                                self.token_manager.add_token("vk", line)
                            print("📁 Токен загружен из файла и сохранен в менеджер")
                            break
        except Exception as e:
            print(f"❌ Ошибка загрузки токена из файла: {e}")

    def auto_connect_google_sheets(self):
        """Автоматическое подключение Google Sheets при запуске"""
        try:
            if not self.google_sheets_plugin:
                print("❌ GoogleSheetsPlugin недоступен")
                self.gsheets_status.config(text="Google Sheets: Плагин недоступен", foreground="red")
                return

            # Пробуем инициализировать соединение
            connected = self.google_sheets_plugin.initialize_connection()
            if connected:
                self.gsheets_status.config(text="Google Sheets: Подключено", foreground="green")
                print("✅ Google Sheets API подключен")
            else:
                self.gsheets_status.config(text="Google Sheets: Ошибка подключения", foreground="red")
                print("❌ Ошибка подключения к Google Sheets API")
        except Exception as e:
            self.gsheets_status.config(text="Google Sheets: Ошибка", foreground="red")
            print(f"❌ Ошибка автоподключения Google Sheets: {e}")

    def _get_utc_timestamps(self, start_date, start_time, end_date, end_time, only_date=False):
        # Упрощённая версия: используем to_vk_timestamp для преобразования
        try:
            if only_date:
                start_ts = to_vk_timestamp(start_date, "00:00")
                end_ts = to_vk_timestamp(end_date, "23:59")
            else:
                start_ts = to_vk_timestamp(start_date, start_time)
                end_ts = to_vk_timestamp(end_date, end_time)
            print(f"[VKParser] start_ts: {start_ts}, end_ts: {end_ts}")
            return start_ts, end_ts
        except Exception as e:
            print(f"[VKParser] Ошибка преобразования времени: {e}")
            return None, None

    def on_paned_window_change(self, event):
        """Обработка изменения позиции разделителя панелей (заглушка)"""

    def _on_keywords_changed(self, event=None):
        if hasattr(self, "settings_adapter") and self.settings_adapter:
            keywords = self.keywords_text.get("1.0", tk.END).strip()
            self.settings_adapter.set_setting("window", "keywords", keywords)

    def _load_tasks_from_results_folder(self):
        """Загружает все задачи через DatabasePlugin и обновляет таблицу задач."""
        print("[DEBUG] Обновление таблицы задач через DatabasePlugin...")
        self.tasks_tree.delete(*self.tasks_tree.get_children())
        database_plugin = self.plugin_manager.get_plugin("database")
        if not database_plugin:
            print("[DEBUG] DatabasePlugin не найден")
            return
        tasks = database_plugin.get_tasks()
        print(f"[DEBUG] Найдено задач: {len(tasks)}")
        if tasks:
            print(f"[DEBUG] Первая задача: {tasks[0]}")

        # Сортируем задачи по дате/времени в обратном порядке (новые сверху)
        sorted_tasks = sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)

        for meta in sorted_tasks:
            try:
                # Адаптируем формат для DatabasePlugin
                dt = meta.get("created_at", "")
                if dt:
                    # DatabasePlugin использует формат datetime как строку
                    if isinstance(dt, str):
                        dt_obj = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                    else:
                        dt_obj = dt
                    date_str = dt_obj.strftime("%d.%m.%Y")
                    time_str = dt_obj.strftime("%H:%M:%S")
                else:
                    date_str = time_str = "?"

                # DatabasePlugin использует другие поля
                count = meta.get("total_posts", 0)
                si = meta.get("total_SI", 0)
                views = meta.get("total_views", 0)
                status = meta.get("status", "completed")
                task_id = meta.get("id", "")  # Используем task_id вместо filepath
                print(f"[DEBUG] Вставка задачи: {date_str} {time_str} {count} {si} {views} {status} task_id={task_id}")
                self.tasks_tree.insert(
                    "", "end", values=(date_str, time_str, count, si, views, status), tags=(str(task_id),)
                )
            except Exception as e:
                print(f"[DEBUG] Ошибка добавления задачи: {e}")

    def _on_task_single_click(self, event):
        """Одиночный клик — отображает результаты задачи в нижней таблице через DatabasePlugin"""
        item_id = self.tasks_tree.identify_row(event.y)
        if not item_id:
            return
        tags = self.tasks_tree.item(item_id, "tags")
        if tags and tags[0]:
            task_id = int(tags[0]) if tags[0].isdigit() else None
            database_plugin = self.plugin_manager.get_plugin("database")
            if database_plugin and task_id:
                try:
                    # Получаем посты задачи из БД
                    posts = database_plugin.get_task_posts(task_id)
                    print(f"✅ Загружено {len(posts)} постов для задачи #{task_id}")

                    # Отображаем результаты в таблице
                    self._display_results_from_data(posts)

                except Exception as e:
                    print(f"❌ Ошибка загрузки результатов задачи #{task_id}: {e}")
                    messagebox.showerror("Ошибка", f"Не удалось загрузить результаты задачи: {e}")

    def _display_results_from_data(self, posts):
        """Отображает результаты из списка постов в нижней таблице"""
        # Очищаем таблицу
        self.results_tree.delete(*self.results_tree.get_children())

        for post in posts:
            try:
                # Адаптируем формат поста для отображения
                link = post.get("link", "")
                text = post.get("text", "")[:100] + "..." if len(post.get("text", "")) > 100 else post.get("text", "")
                post_type = "Пост"
                author = post.get("author_name", "")
                author_link = post.get("author_link", "")
                date = post.get("date", "")
                likes = post.get("likes", 0)
                comments = post.get("comments", 0)
                reposts = post.get("reposts", 0)
                views = post.get("views", 0)

                self.results_tree.insert(
                    "",
                    "end",
                    values=(link, text, post_type, author, author_link, date, likes, comments, reposts, views),
                )
            except Exception as e:
                print(f"❌ Ошибка отображения поста: {e}")

        print(f"✅ Отображено {len(posts)} результатов в таблице")

    def _save_task_meta(self, meta, task_id):
        """Сохранение метаданных задачи через DatabasePlugin"""
        database_plugin = self.plugin_manager.get_plugin("database")
        if database_plugin and task_id:
            try:
                # Обновляем статус задачи или другие параметры
                if isinstance(meta, dict) and "status" in meta:
                    database_plugin.update_task_status(task_id, meta["status"])
                    print(f"✅ Метаданные задачи #{task_id} обновлены")
            except Exception as e:
                print(f"❌ Ошибка сохранения метаданных задачи #{task_id}: {e}")

    def _export_current_results(self):
        """Экспортирует текущие результаты из нижней таблицы в CSV"""
        if not self.results_tree.get_children():
            messagebox.showwarning("Предупреждение", "Нет результатов для экспорта")
            return
        file_path = filedialog.asksaveasfilename(
            title="Экспортировать результаты",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.")],
        )
        if file_path:
            try:
                columns = [self.results_tree.heading(col)["text"] for col in self.results_tree["columns"]]
                with open(file_path, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(columns)
                    for item in self.results_tree.get_children():
                        values = self.results_tree.item(item)["values"]
                        writer.writerow(values)
                messagebox.showinfo("Успех", f"Результаты экспортированы в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать файл: {str(e)}")
