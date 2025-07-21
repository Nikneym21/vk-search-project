import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import re
import csv
from datetime import datetime

class LinkComparatorInterface:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.table1_data = None
        self.table2_data = None
        self.table1_path = None
        self.table2_path = None
        
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
        ttk.Label(main_frame, text="Таблица 1 (основная):", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        self.table1_frame = ttk.Frame(main_frame)
        self.table1_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        
        self.table1_label = ttk.Label(self.table1_frame, text="Файл не выбран")
        self.table1_label.grid(row=0, column=0, sticky="w")
        
        ttk.Button(self.table1_frame, text="Выбрать файл", command=self.load_table1).grid(row=0, column=1, padx=(10, 0))
        
        # Выбор столбцов для таблицы 1
        self.table1_columns_frame = ttk.Frame(main_frame)
        self.table1_columns_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        
        ttk.Label(self.table1_columns_frame, text="Столбцы для поиска ссылок:").grid(row=0, column=0, sticky="w")
        
        self.table1_columns_var = tk.StringVar(value="all")
        self.table1_columns_combo = ttk.Combobox(self.table1_columns_frame, textvariable=self.table1_columns_var, state="readonly", width=30)
        self.table1_columns_combo.grid(row=0, column=1, padx=(10, 0))
        
        # Секция для второй таблицы
        ttk.Label(main_frame, text="Таблица 2 (для сравнения):", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky="w", pady=(10, 5))
        
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
        self.table2_columns_combo = ttk.Combobox(self.table2_columns_frame, textvariable=self.table2_columns_var, state="readonly", width=30)
        self.table2_columns_combo.grid(row=0, column=1, padx=(10, 0))
        
        # Кнопка сравнения
        self.compare_button = ttk.Button(main_frame, text="Сравнить ссылки", command=self.compare_links, state="disabled")
        self.compare_button.grid(row=7, column=0, columnspan=3, pady=20)
        
        # Результаты
        ttk.Label(main_frame, text="Результаты:", font=("Arial", 12, "bold")).grid(row=8, column=0, sticky="w", pady=(10, 5))
        
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
        
        # Кнопка сохранения результатов
        self.save_button = ttk.Button(main_frame, text="Сохранить результаты", command=self.save_results, state="disabled")
        self.save_button.grid(row=11, column=0, columnspan=3, pady=(10, 0))
        
        # Настройка весов для растягивания
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        self.parent_frame.columnconfigure(0, weight=1)
        self.parent_frame.rowconfigure(0, weight=1)
    
    def load_table1(self):
        """Загрузка первой таблицы"""
        file_path = filedialog.askopenfilename(
            title="Выберите первую таблицу",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
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
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
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
            self.table1_columns_combo['values'] = columns
        elif table_num == 2 and self.table2_data is not None:
            columns = ["all"] + list(self.table2_data.columns)
            self.table2_columns_combo['values'] = columns
    
    def load_file(self, file_path):
        """Загрузка файла в DataFrame"""
        try:
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file_path)
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
        if self.table1_data is None or self.table2_data is not None:
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
        
        # Активируем кнопку сохранения
        if unique_links:
            self.save_button.config(state="normal")
    
    def extract_links(self, df, selected_column):
        """Извлечение ссылок из DataFrame"""
        links = set()
        
        if selected_column == "all":
            # Ищем ссылки во всех столбцах
            for column in df.columns:
                for value in df[column].dropna():
                    found_links = self.find_links_in_text(str(value))
                    links.update(found_links)
        else:
            # Ищем ссылки в выбранном столбце
            for value in df[selected_column].dropna():
                found_links = self.find_links_in_text(str(value))
                links.update(found_links)
        
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
        return text.startswith(('http://', 'https://'))
    
    def save_results(self):
        """Сохранение результатов в файл"""
        if not self.result_tree.get_children():
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить результаты",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Уникальные ссылки"])
                    
                    for item in self.result_tree.get_children():
                        link = self.result_tree.item(item)['values'][0]
                        writer.writerow([link])
                
                messagebox.showinfo("Успех", f"Результаты сохранены в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}") 