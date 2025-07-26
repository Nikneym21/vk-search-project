#!/usr/bin/env python3
"""
Тестовый скрипт для проверки горячих клавиш
"""

import tkinter as tk
from tkinter import ttk
import platform

def create_test_window():
    """Создает тестовое окно с горячими клавишами"""
    root = tk.Tk()
    root.title("Тест горячих клавиш")
    root.geometry("500x400")

    # Определяем модификатор
    is_macos = platform.system() == "Darwin"
    modifier = "Command" if is_macos else "Control"

    # Инструкции
    instructions = f"""
Тест горячих клавиш для {platform.system()}

Попробуйте следующие комбинации:
• {modifier}+C - Копировать
• {modifier}+V - Вставить
• {modifier}+X - Вырезать
• {modifier}+A - Выделить все

Введите текст в поля ниже и проверьте работу горячих клавиш:
"""

    ttk.Label(root, text=instructions, font=("Arial", 11)).pack(pady=10, padx=10)

    # Тестовые поля
    ttk.Label(root, text="Entry поле:").pack(anchor="w", padx=10)
    entry = ttk.Entry(root, width=50)
    entry.pack(pady=5, padx=10, fill="x")
    entry.insert(0, "Тестовый текст для Entry")

    ttk.Label(root, text="Text поле:").pack(anchor="w", padx=10, pady=(10,0))
    text = tk.Text(root, height=8, width=50)
    text.pack(pady=5, padx=10, fill="both", expand=True)
    text.insert("1.0", "Тестовый текст для Text виджета\nВторая строка\nТретья строка")

    # Статус
    status = tk.StringVar()
    status_label = ttk.Label(root, textvariable=status, font=("Arial", 9), foreground="blue")
    status_label.pack(pady=5)

    def setup_hotkeys():
        """Настройка горячих клавиш"""
        def copy_handler(event):
            try:
                focused = root.focus_get()
                if focused == entry:
                    if entry.selection_present():
                        text_to_copy = entry.selection_get()
                    else:
                        text_to_copy = entry.get()
                elif focused == text:
                    if text.tag_ranges("sel"):
                        text_to_copy = text.get("sel.first", "sel.last")
                    else:
                        text_to_copy = text.get("1.0", "end-1c")
                else:
                    return

                root.clipboard_clear()
                root.clipboard_append(text_to_copy)
                status.set(f"Скопирован текст: {len(text_to_copy)} символов")
                root.after(2000, lambda: status.set(""))
                return "break"
            except Exception as e:
                status.set(f"Ошибка копирования: {e}")
                return "break"

        def paste_handler(event):
            try:
                text_to_paste = root.clipboard_get()
                focused = root.focus_get()

                if focused == entry:
                    if entry.selection_present():
                        entry.delete("sel.first", "sel.last")
                    entry.insert("insert", text_to_paste)
                elif focused == text:
                    if text.tag_ranges("sel"):
                        text.delete("sel.first", "sel.last")
                    text.insert("insert", text_to_paste)

                status.set(f"Вставлен текст: {len(text_to_paste)} символов")
                root.after(2000, lambda: status.set(""))
                return "break"
            except Exception as e:
                status.set(f"Ошибка вставки: {e}")
                return "break"

        def cut_handler(event):
            try:
                focused = root.focus_get()
                if focused == entry:
                    if entry.selection_present():
                        text_to_cut = entry.selection_get()
                        root.clipboard_clear()
                        root.clipboard_append(text_to_cut)
                        entry.delete("sel.first", "sel.last")
                        status.set(f"Вырезан текст: {len(text_to_cut)} символов")
                elif focused == text:
                    if text.tag_ranges("sel"):
                        text_to_cut = text.get("sel.first", "sel.last")
                        root.clipboard_clear()
                        root.clipboard_append(text_to_cut)
                        text.delete("sel.first", "sel.last")
                        status.set(f"Вырезан текст: {len(text_to_cut)} символов")

                root.after(2000, lambda: status.set(""))
                return "break"
            except Exception as e:
                status.set(f"Ошибка вырезания: {e}")
                return "break"

        def select_all_handler(event):
            try:
                focused = root.focus_get()
                if focused == entry:
                    entry.select_range(0, 'end')
                elif focused == text:
                    text.tag_add("sel", "1.0", "end-1c")
                    text.mark_set("insert", "1.0")
                    text.see("insert")

                status.set("Весь текст выделен")
                root.after(2000, lambda: status.set(""))
                return "break"
            except Exception as e:
                status.set(f"Ошибка выделения: {e}")
                return "break"

        # Привязываем горячие клавиши
        if is_macos:
            root.bind_all("<Command-c>", copy_handler)
            root.bind_all("<Command-v>", paste_handler)
            root.bind_all("<Command-x>", cut_handler)
            root.bind_all("<Command-a>", select_all_handler)
        else:
            root.bind_all("<Control-c>", copy_handler)
            root.bind_all("<Control-v>", paste_handler)
            root.bind_all("<Control-x>", cut_handler)
            root.bind_all("<Control-a>", select_all_handler)

        status.set("Горячие клавиши настроены")

    # Настраиваем горячие клавиши
    setup_hotkeys()

    # Добавляем фокус на первое поле
    entry.focus_set()

    return root

if __name__ == "__main__":
    print("🧪 Запуск тестового окна для горячих клавиш...")
    print(f"🖥️ Платформа: {platform.system()}")

    root = create_test_window()

    print("✅ Окно создано. Проверьте работу горячих клавиш.")
    print("❌ Если не работают, возможно нужны разрешения macOS")

    root.mainloop()
