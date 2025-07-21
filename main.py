#!/usr/bin/env python3
"""
Главный файл приложения "Сравнитель ссылок и Парсер ВК"
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gui.main_interface import MainInterface
except ImportError as e:
    print(f"Ошибка импорта GUI модулей: {e}")
    print("Убедитесь, что все файлы интерфейса созданы в папке src/gui/")
    sys.exit(1)

def main():
    """Главная функция приложения"""
    try:
        # Создаем главное окно
        root = tk.Tk()
        
        # Создаем и запускаем главный интерфейс
        app = MainInterface(root)
        
        # Запускаем главный цикл приложения
        root.mainloop()
        
    except Exception as e:
        # Показываем ошибку пользователю
        messagebox.showerror("Критическая ошибка", f"Не удалось запустить приложение:\n{str(e)}")
        print(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 