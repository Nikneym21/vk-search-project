#!/usr/bin/env python3
"""
Интерфейс для работы с базой данных результатов парсинга
"""

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk


class DatabaseInterface:
    """Интерфейс для работы с базой данных"""

    def __init__(self, parent, database_plugin):
        self.parent = parent
        self.database_plugin = database_plugin
        self.current_task_id = None

        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        """Создание интерфейса"""
        # Основной фрейм
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок
        ttk.Label(self.frame, text="База данных результатов парсинга", font=("Arial", 14, "bold")).pack(pady=(0, 20))

        # Создаем панели
        self.create_tasks_panel()
        self.create_posts_panel()
        self.create_export_panel()

    def create_tasks_panel(self):
        """Панель задач"""
        tasks_frame = ttk.LabelFrame(self.frame, text="Задачи", padding=10)
        tasks_frame.pack(fill="x", pady=(0, 10))

        # Кнопки управления задачами
        btn_frame = ttk.Frame(tasks_frame)
        btn_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(btn_frame, text="Обновить", command=self.load_tasks).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Экспорт выбранной", command=self.export_selected_task).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text="Удалить задачу", command=self.delete_selected_task).pack(side="left")

        # Таблица задач
        columns = (
            "ID",
            "Название",
            "Статус",
            "Постов",
            "Лайков",
            "Комментариев",
            "Репостов",
            "Просмотров",
            "SI",
            "Дата",
        )
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=columns, show="headings", height=8)

        # Настройка колонок
        for col in columns:
            self.tasks_tree.heading(col, text=col)
            self.tasks_tree.column(col, width=80)

        # Специальная ширина для названия
        self.tasks_tree.column("Название", width=200)
        self.tasks_tree.column("Дата", width=120)

        # Скроллбар
        tasks_scrollbar = ttk.Scrollbar(tasks_frame, orient="vertical", command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=tasks_scrollbar.set)

        self.tasks_tree.pack(side="left", fill="both", expand=True)
        tasks_scrollbar.pack(side="right", fill="y")

        # Привязка событий
        self.tasks_tree.bind("<<TreeviewSelect>>", self.on_task_selected)

    def create_posts_panel(self):
        """Панель постов"""
        posts_frame = ttk.LabelFrame(self.frame, text="Посты выбранной задачи", padding=10)
        posts_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Кнопки управления постами
        posts_btn_frame = ttk.Frame(posts_frame)
        posts_btn_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(posts_btn_frame, text="Обновить посты", command=self.load_posts).pack(side="left", padx=(0, 5))
        ttk.Button(posts_btn_frame, text="Найти дубликаты", command=self.find_duplicates).pack(side="left")

        # Таблица постов
        columns = ("ID", "VK ID", "Текст", "Дата", "Лайки", "Комментарии", "Репосты", "Просмотры", "Ключевые слова")
        self.posts_tree = ttk.Treeview(posts_frame, columns=columns, show="headings", height=10)

        # Настройка колонок
        for col in columns:
            self.posts_tree.heading(col, text=col)
            self.posts_tree.column(col, width=100)

        # Специальная ширина для текста
        self.posts_tree.column("Текст", width=300)
        self.posts_tree.column("VK ID", width=120)
        self.posts_tree.column("Ключевые слова", width=150)

        # Скроллбар
        posts_scrollbar = ttk.Scrollbar(posts_frame, orient="vertical", command=self.posts_tree.yview)
        self.posts_tree.configure(yscrollcommand=posts_scrollbar.set)

        self.posts_tree.pack(side="left", fill="both", expand=True)
        posts_scrollbar.pack(side="right", fill="y")

    def create_export_panel(self):
        """Панель экспорта"""
        export_frame = ttk.LabelFrame(self.frame, text="Экспорт", padding=10)
        export_frame.pack(fill="x")

        # Статистика
        self.stats_label = ttk.Label(export_frame, text="Выберите задачу для просмотра статистики")
        self.stats_label.pack(anchor="w", pady=(0, 10))

        # Кнопки экспорта
        export_btn_frame = ttk.Frame(export_frame)
        export_btn_frame.pack(fill="x")

        ttk.Button(export_btn_frame, text="Экспорт в CSV", command=self.export_to_csv).pack(side="left", padx=(0, 5))
        ttk.Button(export_btn_frame, text="Экспорт в JSON", command=self.export_to_json).pack(side="left", padx=(0, 5))
        ttk.Button(export_btn_frame, text="Экспорт статистики", command=self.export_statistics).pack(side="left")

    def load_tasks(self):
        """Загрузка списка задач"""
        # Очищаем таблицу
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        # Получаем задачи из БД
        tasks = self.database_plugin.get_tasks()

        for task in tasks:
            # Форматируем дату
            created_at = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
            date_str = created_at.strftime("%d.%m.%Y %H:%M")

            # Добавляем в таблицу
            self.tasks_tree.insert(
                "",
                "end",
                values=(
                    task["id"],
                    task["task_name"][:30] + "..." if len(task["task_name"]) > 30 else task["task_name"],
                    task["status"],
                    task["total_posts"],
                    task["total_likes"],
                    task["total_comments"],
                    task["total_reposts"],
                    task["total_views"],
                    task["total_SI"],
                    date_str,
                ),
            )

        # Обновляем статистику
        self.update_statistics()

    def on_task_selected(self, event):
        """Обработка выбора задачи"""
        selection = self.tasks_tree.selection()
        if selection:
            item = self.tasks_tree.item(selection[0])
            self.current_task_id = item["values"][0]
            self.load_posts()
            self.update_statistics()
        else:
            self.current_task_id = None

    def load_posts(self):
        """Загрузка постов выбранной задачи"""
        if not self.current_task_id:
            return

        # Очищаем таблицу
        for item in self.posts_tree.get_children():
            self.posts_tree.delete(item)

        # Получаем посты из БД
        posts = self.database_plugin.get_task_posts(self.current_task_id, limit=1000)

        for post in posts:
            # Форматируем дату
            date_str = ""
            if post["date"]:
                try:
                    dt = datetime.fromtimestamp(post["date"])
                    date_str = dt.strftime("%H:%M %d.%m.%Y")
                except (ValueError, TypeError, OSError):
                    date_str = str(post["date"])

            # Обрезаем текст
            text = post["text"][:100] + "..." if len(post["text"]) > 100 else post["text"]

            # Ключевые слова
            keywords = ", ".join(post["keywords_matched"][:3])
            if len(post["keywords_matched"]) > 3:
                keywords += "..."

            # Добавляем в таблицу
            self.posts_tree.insert(
                "",
                "end",
                values=(
                    post["id"],
                    post["vk_id"],
                    text,
                    date_str,
                    post["likes"],
                    post["comments"],
                    post["reposts"],
                    post["views"],
                    keywords,
                ),
            )

    def update_statistics(self):
        """Обновление статистики"""
        if not self.current_task_id:
            self.stats_label.config(text="Выберите задачу для просмотра статистики")
            return

        stats = self.database_plugin.get_task_statistics(self.current_task_id)
        if stats:
            stats_text = f"Задача: {stats['task_name']} | Статус: {stats['status']} | "
            stats_text += f"Постов: {stats['total_posts']} | Лайков: {stats['total_likes']} | "
            stats_text += f"Комментариев: {stats['total_comments']} | Репостов: {stats['total_reposts']} | "
            stats_text += f"Просмотров: {stats['total_views']} | SI: {stats['total_SI']}"

            self.stats_label.config(text=stats_text)

    def export_selected_task(self):
        """Экспорт выбранной задачи"""
        if not self.current_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу для экспорта")
            return

        # Получаем информацию о задаче
        stats = self.database_plugin.get_task_statistics(self.current_task_id)
        if not stats:
            messagebox.showerror("Ошибка", "Не удалось получить информацию о задаче")
            return

        # Выбираем файл для сохранения
        filename = f"task_{self.current_task_id}_{stats['task_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], initialfile=filename
        )

        if filepath:
            if self.database_plugin.export_task_to_csv(self.current_task_id, filepath):
                messagebox.showinfo("Успех", f"Задача экспортирована в {filepath}")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать задачу")

    def export_to_csv(self):
        """Экспорт в CSV"""
        self.export_selected_task()

    def export_to_json(self):
        """Экспорт в JSON"""
        if not self.current_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу для экспорта")
            return

        # Получаем посты
        posts = self.database_plugin.get_task_posts(self.current_task_id)

        if not posts:
            messagebox.showwarning("Внимание", "Нет постов для экспорта")
            return

        # Выбираем файл
        filename = f"task_{self.current_task_id}_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], initialfile=filename
        )

        if filepath:
            try:
                import json

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(posts, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Успех", f"Посты экспортированы в {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")

    def export_statistics(self):
        """Экспорт статистики"""
        if not self.current_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу для экспорта статистики")
            return

        stats = self.database_plugin.get_task_statistics(self.current_task_id)
        if not stats:
            messagebox.showerror("Ошибка", "Не удалось получить статистику")
            return

        # Выбираем файл
        filename = f"task_{self.current_task_id}_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], initialfile=filename
        )

        if filepath:
            try:
                import json

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Успех", f"Статистика экспортирована в {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")

    def find_duplicates(self):
        """Поиск дубликатов"""
        if not self.current_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу для поиска дубликатов")
            return

        duplicates = self.database_plugin.find_duplicates(self.current_task_id)

        if duplicates:
            messagebox.showinfo("Дубликаты", f"Найдено {len(duplicates)} групп дубликатов")

            # Показываем детали в новом окне
            self.show_duplicates_window(duplicates)
        else:
            messagebox.showinfo("Дубликаты", "Дубликатов не найдено")

    def show_duplicates_window(self, duplicates):
        """Показ окна с дубликатами"""
        window = tk.Toplevel(self.parent)
        window.title("Дубликаты")
        window.geometry("800x600")

        # Создаем текстовое поле
        text_widget = tk.Text(window, wrap="word")
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Заполняем информацией о дубликатах
        for i, dup_group in enumerate(duplicates, 1):
            text_widget.insert("end", f"Группа дубликатов {i} ({len(dup_group)} постов):\n")
            text_widget.insert("end", "-" * 50 + "\n")

            for j, post in enumerate(dup_group, 1):
                text_widget.insert("end", f"{j}. ID: {post['id']}, VK ID: {post['vk_id']}\n")
                text_widget.insert("end", f"   Текст: {post['text'][:100]}...\n")
                text_widget.insert("end", f"   Лайки: {post['likes']}, Комментарии: {post['comments']}\n\n")

            text_widget.insert("end", "\n")

    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        if not self.current_task_id:
            messagebox.showwarning("Внимание", "Выберите задачу для удаления")
            return

        # Подтверждение
        stats = self.database_plugin.get_task_statistics(self.current_task_id)
        if not stats:
            return

        result = messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить задачу '{stats['task_name']}'?\n"
            f"Это также удалит все {stats['total_posts']} постов этой задачи.",
        )

        if result:
            try:
                # Удаляем задачу (посты удалятся автоматически из-за CASCADE)
                cursor = self.database_plugin.connection.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (self.current_task_id,))
                self.database_plugin.connection.commit()

                messagebox.showinfo("Успех", "Задача удалена")
                self.current_task_id = None
                self.load_tasks()
                self.load_posts()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить задачу: {e}")
