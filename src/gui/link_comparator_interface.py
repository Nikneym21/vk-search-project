import csv
import os
import re
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import pandas as pd


class LinkComparatorInterface:
    def __init__(self, parent_frame, plugin_manager=None):
        self.parent_frame = parent_frame
        self.plugin_manager = plugin_manager
        self.table1_data = None
        self.table2_data = None
        self.table1_path = None
        self.table2_path = None

        # Получаем GoogleSheetsPlugin через PluginManager
        if self.plugin_manager:
            self.google_sheets_plugin = self.plugin_manager.get_plugin("google_sheets")
            if self.google_sheets_plugin:
                print("✅ GoogleSheetsPlugin получен через PluginManager")
            else:
                print("⚠️ GoogleSheetsPlugin не найден в PluginManager")

            # Получаем DatabasePlugin для сохранения результатов
            self.database_plugin = self.plugin_manager.get_plugin("database")
            if self.database_plugin:
                print("✅ DatabasePlugin получен через PluginManager")
            else:
                print("⚠️ DatabasePlugin не найден в PluginManager")
        else:
            self.google_sheets_plugin = None
            self.database_plugin = None
            print("⚠️ PluginManager не передан в LinkComparatorInterface")

        # Настройка интерфейса
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса для сравнения ссылок"""
        # Главный фрейм для сравнителя ссылок
        main_frame = ttk.Frame(self.parent_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Заголовок
        title_label = ttk.Label(main_frame, text="Сравнитель ссылок", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Секция для первой таблицы
        ttk.Label(main_frame, text="Таблица 1 (основная):", font=("Arial", 12, "bold")).grid(
            row=1, column=0, sticky="w", pady=(0, 5)
        )

        self.table1_frame = ttk.Frame(main_frame)
        self.table1_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.table1_label = ttk.Label(self.table1_frame, text="Файл не выбран")
        self.table1_label.grid(row=0, column=0, sticky="w")

        ttk.Button(self.table1_frame, text="Выбрать файл", command=self.load_table1).grid(row=0, column=1, padx=(10, 0))
        # Кнопка загрузки из Google Sheets
        ttk.Button(self.table1_frame, text="Загрузить из Google Sheets", command=self.open_gsheets_dialog_table1).grid(
            row=0, column=2, padx=(10, 0)
        )

        # Выбор столбцов для таблицы 1
        self.table1_columns_frame = ttk.Frame(main_frame)
        self.table1_columns_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        ttk.Label(self.table1_columns_frame, text="Столбцы для поиска ссылок:").grid(row=0, column=0, sticky="w")

        self.table1_columns_var = tk.StringVar(value="all")
        self.table1_columns_combo = ttk.Combobox(
            self.table1_columns_frame, textvariable=self.table1_columns_var, state="readonly", width=30
        )
        self.table1_columns_combo.grid(row=0, column=1, padx=(10, 0))

        # Секция для второй таблицы
        ttk.Label(main_frame, text="Таблица 2 (для сравнения):", font=("Arial", 12, "bold")).grid(
            row=4, column=0, sticky="w", pady=(10, 5)
        )

        self.table2_frame = ttk.Frame(main_frame)
        self.table2_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.table2_label = ttk.Label(self.table2_frame, text="Файл не выбран")
        self.table2_label.grid(row=0, column=0, sticky="w")

        ttk.Button(self.table2_frame, text="Выбрать файл", command=self.load_table2).grid(row=0, column=1, padx=(10, 0))

        # Выбор столбцов для таблицы 2
        self.table2_columns_frame = ttk.Frame(main_frame)
        self.table2_columns_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        ttk.Label(self.table2_columns_frame, text="Столбцы для поиска ссылок:").grid(row=0, column=0, sticky="w")

        self.table2_columns_var = tk.StringVar(value="all")
        self.table2_columns_combo = ttk.Combobox(
            self.table2_columns_frame, textvariable=self.table2_columns_var, state="readonly", width=30
        )
        self.table2_columns_combo.grid(row=0, column=1, padx=(10, 0))

        # Кнопка сравнения
        self.compare_button = ttk.Button(
            main_frame, text="Сравнить ссылки", command=self.compare_links, state="disabled"
        )
        self.compare_button.grid(row=7, column=0, columnspan=3, pady=20)

        # Результаты
        ttk.Label(main_frame, text="Результаты:", font=("Arial", 12, "bold")).grid(
            row=8, column=0, sticky="w", pady=(10, 5)
        )

        # Создаем Treeview для отображения результатов
        self.result_tree = ttk.Treeview(main_frame, columns=("link",), show="headings", height=15)
        self.result_tree.heading("link", text="Ссылки из таблицы 2, которых нет в таблице 1")
        self.result_tree.column("link", width=700)
        self.result_tree.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=(0, 10))

        # Скроллбар для результатов
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar.grid(row=9, column=3, sticky="ns")
        self.result_tree.configure(yscrollcommand=scrollbar.set)

        # Статистика
        self.stats_label = ttk.Label(main_frame, text="")
        self.stats_label.grid(row=10, column=0, columnspan=3, sticky="w")

        # Кнопки сохранения результатов
        self.save_csv_button = ttk.Button(
            main_frame, text="Сохранить как CSV", command=self.save_results_csv, state="disabled"
        )
        self.save_csv_button.grid(row=11, column=0, pady=(10, 0), sticky="ew")

        self.save_txt_button = ttk.Button(
            main_frame, text="Сохранить как TXT", command=self.save_results_txt, state="disabled"
        )
        self.save_txt_button.grid(row=11, column=1, pady=(10, 0), sticky="ew")

        # Кнопка сохранения в базу данных (через DatabasePlugin)
        self.save_db_button = ttk.Button(
            main_frame, text="Сохранить в БД", command=self.save_results_db, state="disabled"
        )
        self.save_db_button.grid(row=11, column=2, pady=(10, 0), sticky="ew")

        # Настройка весов для растягивания
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)

    def load_table1(self):
        """Загрузка первой таблицы"""
        file_path = filedialog.askopenfilename(
            title="Выберите первую таблицу",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if file_path:
            self.table1_path = file_path
            self.table1_data = self.load_file(file_path)
            self.table1_label.config(text=os.path.basename(file_path))
            self.update_columns_list(1)
            self.check_ready()

    def load_table2(self):
        """Загрузка второй таблицы"""
        file_path = filedialog.askopenfilename(
            title="Выберите вторую таблицу",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if file_path:
            self.table2_path = file_path
            self.table2_data = self.load_file(file_path)
            self.table2_label.config(text=os.path.basename(file_path))
            self.update_columns_list(2)
            self.check_ready()

    def update_columns_list(self, table_num):
        """Обновление списка столбцов для выбранной таблицы"""
        if table_num == 1 and self.table1_data is not None:
            columns = ["all"] + list(self.table1_data.columns)
            self.table1_columns_combo["values"] = columns
        elif table_num == 2 and self.table2_data is not None:
            columns = ["all"] + list(self.table2_data.columns)
            self.table2_columns_combo["values"] = columns

    def load_file(self, file_path):
        try:
            if file_path.endswith(".csv"):
                return pd.read_csv(file_path)
            elif file_path.endswith((".xlsx", ".xls")):
                return pd.read_excel(file_path)
            elif file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                return pd.DataFrame({"text": lines})
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат файла")
                return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
            return None

    def check_ready(self):
        """Проверка готовности к сравнению"""
        if self.table1_data is not None and self.table2_data is not None:
            self.compare_button.config(state="normal")
        else:
            self.compare_button.config(state="disabled")

    def compare_links(self):
        """Сравнение ссылок между таблицами"""
        if self.table1_data is None or self.table2_data is None:
            messagebox.showerror("Ошибка", "Загрузите обе таблицы")
            return

        # Очищаем предыдущие результаты
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # Извлекаем ссылки из обеих таблиц
        links1 = self.extract_links(self.table1_data, self.table1_columns_var.get())
        links2 = self.extract_links(self.table2_data, self.table2_columns_var.get())

        # Находим ссылки из таблицы 2, которых нет в таблице 1
        unique_links = links2 - links1

        # Отображаем результаты
        for link in sorted(unique_links):
            self.result_tree.insert("", "end", values=(link,))

        # Обновляем статистику
        self.stats_label.config(text=f"Найдено {len(unique_links)} уникальных ссылок из {len(links2)} в таблице 2")

        # Активируем кнопки сохранения
        if unique_links:
            self.save_csv_button.config(state="normal")
            self.save_txt_button.config(state="normal")
            # Активируем кнопку БД только если DatabasePlugin доступен
            if self.database_plugin:
                self.save_db_button.config(state="normal")

    def extract_links(self, df, selected_column):
        """Извлечение ссылок из DataFrame"""
        links = set()
        if selected_column == "all":
            for column in df.columns:
                for value in df[column].dropna():
                    found_links = self.find_links_in_text(str(value))
                    for link in found_links:
                        clean_link = link.strip().rstrip(",;")
                        if clean_link:
                            links.add(clean_link)
        else:
            for value in df[selected_column].dropna():
                found_links = self.find_links_in_text(str(value))
                for link in found_links:
                    clean_link = link.strip().rstrip(",;")
                    if clean_link:
                        links.add(clean_link)
        return links

    def find_links_in_text(self, text):
        """Поиск ссылок в тексте"""
        links = set()

        # Регулярное выражение для поиска ссылок
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, text)

        for match in matches:
            if self.is_valid_link(match):
                links.add(match)

        return links

    def is_valid_link(self, text):
        """Проверка валидности ссылки"""
        if not text:
            return False

        # Проверяем, что это действительно ссылка
        if not self.is_link(text):
            return False

        # Дополнительные проверки можно добавить здесь
        return True

    def is_link(self, text):
        """Проверка, является ли текст ссылкой"""
        return text.startswith(("http://", "https://"))

    def save_results_csv(self):
        """Сохранение результатов в CSV"""
        if not self.result_tree.get_children():
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return
        file_path = filedialog.asksaveasfilename(
            title="Сохранить результаты как CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.")],
        )
        if file_path:
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Уникальные ссылки"])
                    for item in self.result_tree.get_children():
                        link = self.result_tree.item(item)["values"][0]
                        writer.writerow([link])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def save_results_txt(self):
        """Сохранение результатов в TXT"""
        if not self.result_tree.get_children():
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return
        file_path = filedialog.asksaveasfilename(
            title="Сохранить результаты как TXT",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.")],
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    for item in self.result_tree.get_children():
                        link = self.result_tree.item(item)["values"][0]
                        file.write(f"{link}\n")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def _create_gsheets_dialog_ui(self, win):
        """Создаёт UI элементы для диалога Google Sheets"""
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        # URL поле
        ttk.Label(frame, text="URL Google Sheets:").grid(row=0, column=0, sticky="w")
        url_var = tk.StringVar()
        url_entry = ttk.Entry(frame, textvariable=url_var, width=40)
        url_entry.grid(row=0, column=1, sticky="ew")

        # Лист выбор
        ttk.Label(frame, text="Лист:").grid(row=1, column=0, sticky="w")
        sheet_var = tk.StringVar()
        sheet_combo = ttk.Combobox(frame, textvariable=sheet_var, state="readonly", width=30)
        sheet_combo.grid(row=1, column=1, sticky="ew")

        # Столбец выбор
        ttk.Label(frame, text="Столбец:").grid(row=2, column=0, sticky="w")
        column_var = tk.StringVar()
        column_combo = ttk.Combobox(frame, textvariable=column_var, state="readonly", width=30)
        column_combo.grid(row=2, column=1, sticky="ew")

        return {
            'frame': frame,
            'url_var': url_var,
            'sheet_var': sheet_var,
            'column_var': column_var,
            'sheet_combo': sheet_combo,
            'column_combo': column_combo
        }

    def _fetch_gsheets_sheets(self, url_var, sheet_combo, sheet_var, fetch_columns_callback):
        """Загружает список листов из Google Sheets"""
        url = url_var.get().strip()
        if not url:
            messagebox.showwarning("Внимание", "Введите URL Google Sheets!")
            return

        try:
            if not hasattr(self, "google_sheets_plugin") or self.google_sheets_plugin is None:
                messagebox.showerror("Ошибка", "GoogleSheetsPlugin недоступен. Проверьте PluginManager.")
                return

            # Инициализируем соединение если нужно
            if hasattr(self.google_sheets_plugin, "initialize_connection"):
                self.google_sheets_plugin.initialize_connection()

            if not self.google_sheets_plugin.open_spreadsheet(url):
                messagebox.showerror("Ошибка", "Не удалось открыть таблицу по ссылке")
                return

            sheets = self.google_sheets_plugin.list_worksheets()
            if not sheets:
                messagebox.showerror("Ошибка", "Не удалось получить список листов")
                return

            sheet_combo["values"] = sheets
            sheet_var.set(sheets[0])
            fetch_columns_callback()  # Загружаем столбцы для первого листа

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки листов: {e}")

    def _fetch_gsheets_columns(self, sheet_var, column_combo, column_var):
        """Загружает список столбцов из выбранного листа"""
        sheet = sheet_var.get().strip()
        if not sheet:
            return

        try:
            data = self.google_sheets_plugin.download_data(sheet)
            if not data:
                messagebox.showerror("Ошибка", "Лист пуст или не удалось загрузить данные")
                return

            columns = list(data[0].keys()) if data else []
            column_combo["values"] = columns
            if columns:
                column_var.set(columns[0])

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки столбцов: {e}")

    def _load_gsheets_data(self, url_var, sheet_var, column_var, win):
        """Загружает данные из Google Sheets"""
        url = url_var.get().strip()
        sheet = sheet_var.get().strip()
        column = column_var.get().strip()

        if not url or not sheet or not column:
            messagebox.showwarning("Внимание", "Выберите все параметры!")
            return

        try:
            data = self.google_sheets_plugin.download_data(sheet)
            if not data:
                messagebox.showerror("Ошибка", "Не удалось загрузить данные с листа")
                return

            # Преобразуем в DataFrame
            df = pd.DataFrame(data)
            self.table1_data = df
            self.table1_path = f"Google Sheets: {sheet} ({url})"
            self.table1_label.config(text=f"Google Sheets: {sheet}")
            self.update_columns_list(1)
            self.check_ready()
            win.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки данных: {e}")

    def open_gsheets_dialog_table1(self):
        """Открывает окно выбора Google Sheets для первой таблицы"""
        # Создание окна
        win = tk.Toplevel(self.parent_frame)
        win.title("Загрузка из Google Sheets (Таблица 1)")
        win.geometry("400x250")

        # Создание UI элементов
        ui_elements = self._create_gsheets_dialog_ui(win)

        # Создание callback функций с замыканием
        def fetch_columns(*args):
            self._fetch_gsheets_columns(
                ui_elements['sheet_var'],
                ui_elements['column_combo'],
                ui_elements['column_var']
            )

        def fetch_sheets():
            self._fetch_gsheets_sheets(
                ui_elements['url_var'],
                ui_elements['sheet_combo'],
                ui_elements['sheet_var'],
                fetch_columns
            )

        def load_data():
            self._load_gsheets_data(
                ui_elements['url_var'],
                ui_elements['sheet_var'],
                ui_elements['column_var'],
                win
            )

        # Создание кнопок
        ttk.Button(ui_elements['frame'], text="Получить листы", command=fetch_sheets).grid(
            row=3, column=0, pady=10, sticky="ew"
        )
        ttk.Button(ui_elements['frame'], text="Загрузить данные", command=load_data).grid(
            row=3, column=1, pady=10, sticky="ew"
        )

        # Привязка событий
        ui_elements['sheet_combo'].bind("<<ComboboxSelected>>", fetch_columns)

    def save_results_db(self):
        """Сохранение результатов сравнения в базу данных через DatabasePlugin"""
        if not self.result_tree.get_children():
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return

        if not self.database_plugin:
            messagebox.showerror("Ошибка", "DatabasePlugin недоступен")
            return

        try:
            # Собираем результаты из таблицы
            results = []
            for item in self.result_tree.get_children():
                link = self.result_tree.item(item, "values")[0]
                results.append(
                    {
                        "link": link,
                        "source": "link_comparator",
                        "timestamp": datetime.now().isoformat(),
                        "table1_path": getattr(self, "table1_path", "unknown"),
                        "table2_path": getattr(self, "table2_path", "unknown"),
                    }
                )

            # Создаем задачу в базе данных для сравнения ссылок
            task_id = self.database_plugin.create_task(
                keywords=["link_comparison"],
                start_date=datetime.now().strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
                exact_match=True,
                minus_words=[],
            )

            # Сохраняем результаты как посты
            saved_count = self.database_plugin.save_posts(task_id, results)

            messagebox.showinfo("Успех", f"Сохранено {saved_count} результатов в базу данных\nЗадача #{task_id}")
            print(f"✅ Результаты сравнения сохранены в БД: задача #{task_id}, {saved_count} записей")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить в базу данных: {str(e)}")
            print(f"❌ Ошибка сохранения в БД: {e}")

    def _setup_hotkeys(self):
        """Настройка горячих клавиш через HotkeysPlugin"""
        try:
            hotkeys_plugin = self.plugin_manager.get_plugin("hotkeys")
            if hotkeys_plugin:
                # Собираем Entry виджеты
                widgets = []
                if hasattr(self, 'path1_entry'):
                    widgets.append(self.path1_entry)
                if hasattr(self, 'path2_entry'):
                    widgets.append(self.path2_entry)

                # Регистрируем виджеты
                success_count = hotkeys_plugin.register_multiple_widgets(widgets)
                print(f"🎮 LinkComparator: Горячие клавиши настроены для {success_count} виджетов")
        except Exception as e:
            print(f"❌ LinkComparator: Ошибка настройки горячих клавиш: {e}")
