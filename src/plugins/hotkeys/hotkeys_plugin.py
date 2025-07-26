"""
Плагин для управления горячими клавишами в tkinter
Специально адаптирован для macOS
"""

import platform
import tkinter as tk
from typing import List, Union, Optional

from src.plugins.base_plugin import BasePlugin


class HotkeysPlugin(BasePlugin):
    """Плагин для управления горячими клавишами"""

    def __init__(self):
        super().__init__()
        self.name = "HotkeysPlugin"
        self.version = "1.0.0"
        self.description = "Управление горячими клавишами для всех интерфейсов"

        # Определяем ОС и модификаторы
        self.is_macos = platform.system() == "Darwin"
        self.modifier_key = "Command" if self.is_macos else "Control"
        self.modifier_symbol = "⌘" if self.is_macos else "Ctrl"

        # Список зарегистрированных виджетов
        self.registered_widgets = []

    def initialize(self) -> bool:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина горячих клавиш")
        self.log_info(f"ОС: {platform.system()}, модификатор: {self.modifier_key}")

        # Настройка для macOS
        if self.is_macos:
            self._setup_macos_hotkeys()

        self.log_info("Плагин горячих клавиш инициализирован")
        return True

    def _setup_macos_hotkeys(self):
        """Специальная настройка для macOS"""
        try:
            # Создаем временное окно для проверки
            test_root = tk.Tk()
            test_root.withdraw()

            # Настраиваем системные привязки
            test_root.option_add('*tearOff', False)

            # Проверяем поддержку Command модификатора
            test_entry = tk.Entry(test_root)
            test_entry.bind('<Command-v>', lambda e: None)

            test_root.destroy()
            self.log_info("macOS горячие клавиши настроены")

        except Exception as e:
            self.log_error(f"Ошибка настройки macOS: {e}")

    def register_widget(self, widget: Union[tk.Entry, tk.Text],
                       widget_type: str = "auto") -> bool:
        """
        Регистрирует виджет для поддержки горячих клавиш

        Args:
            widget: Виджет tkinter (Entry или Text)
            widget_type: Тип виджета ("entry", "text", "auto")
        """
        try:
            if widget_type == "auto":
                widget_type = "text" if isinstance(widget, tk.Text) else "entry"

            # Проверяем, не зарегистрирован ли уже
            if widget in self.registered_widgets:
                return True

            # Пробуем два метода: основной и системный
            success1 = self._apply_hotkeys(widget, widget_type)
            success2 = self._setup_system_hotkeys(widget, widget_type)

            # Всегда добавляем контекстное меню как запасной вариант
            self._add_context_menu(widget, widget_type)

            if success1 or success2:
                self.registered_widgets.append(widget)
                self.log_info(f"Виджет {widget_type} зарегистрирован для горячих клавиш")
                return True

        except Exception as e:
            self.log_error(f"Ошибка регистрации виджета: {e}")

        return False

    def register_multiple_widgets(self, widgets: List[Union[tk.Entry, tk.Text]]) -> int:
        """Регистрирует несколько виджетов сразу"""
        success_count = 0
        for widget in widgets:
            if widget and self.register_widget(widget):
                success_count += 1

        self.log_info(f"Зарегистрировано {success_count}/{len(widgets)} виджетов")
        return success_count

    def _apply_hotkeys(self, widget: Union[tk.Entry, tk.Text], widget_type: str) -> bool:
        """Применяет горячие клавиши к виджету"""
        try:
            # Определяем модификатор
            mod = "<Command-" if self.is_macos else "<Control-"

            # Базовые горячие клавиши
            hotkeys = {
                f"{mod}c>": lambda e: self._copy_text(widget, widget_type),
                f"{mod}C>": lambda e: self._copy_text(widget, widget_type),
                f"{mod}v>": lambda e: self._paste_text(widget, widget_type),
                f"{mod}V>": lambda e: self._paste_text(widget, widget_type),
                f"{mod}x>": lambda e: self._cut_text(widget, widget_type),
                f"{mod}X>": lambda e: self._cut_text(widget, widget_type),
                f"{mod}a>": lambda e: self._select_all(widget, widget_type),
                f"{mod}A>": lambda e: self._select_all(widget, widget_type),
            }

            # Дополнительные для Text виджетов
            if widget_type == "text":
                hotkeys.update({
                    f"{mod}z>": lambda e: self._undo(widget),
                    f"{mod}Z>": lambda e: self._undo(widget),
                    f"{mod}y>": lambda e: self._redo(widget),
                    f"{mod}Y>": lambda e: self._redo(widget),
                })

            # Привязываем горячие клавиши
            for key_combo, handler in hotkeys.items():
                widget.bind(key_combo, handler)

            # Дополнительная настройка для macOS
            if self.is_macos and hasattr(widget, 'tk'):
                self._setup_macos_widget(widget)

            return True

        except Exception as e:
            self.log_error(f"Ошибка применения горячих клавиш: {e}")
            return False

    def _setup_system_hotkeys(self, widget: Union[tk.Entry, tk.Text], widget_type: str) -> bool:
        """Альтернативный метод настройки горячих клавиш через системные события"""
        try:
            root = widget.winfo_toplevel()

            # Настройка глобальных привязок на уровне root окна
            if self.is_macos:
                # macOS специфичные привязки
                root.bind_all("<Command-c>", lambda e: self._handle_copy(e, widget_type))
                root.bind_all("<Command-v>", lambda e: self._handle_paste(e, widget_type))
                root.bind_all("<Command-x>", lambda e: self._handle_cut(e, widget_type))
                root.bind_all("<Command-a>", lambda e: self._handle_select_all(e, widget_type))
            else:
                # Windows/Linux привязки
                root.bind_all("<Control-c>", lambda e: self._handle_copy(e, widget_type))
                root.bind_all("<Control-v>", lambda e: self._handle_paste(e, widget_type))
                root.bind_all("<Control-x>", lambda e: self._handle_cut(e, widget_type))
                root.bind_all("<Control-a>", lambda e: self._handle_select_all(e, widget_type))

            self.log_info(f"Системные горячие клавиши настроены для {widget_type}")
            return True

        except Exception as e:
            self.log_error(f"Ошибка настройки системных горячих клавиш: {e}")
            return False

    def _handle_copy(self, event, widget_type: str) -> str:
        """Обработчик копирования через системный focus"""
        try:
            focused_widget = event.widget.focus_get()
            if focused_widget and hasattr(focused_widget, 'get'):
                return self._copy_text(focused_widget, widget_type)
        except:
            pass
        return "break"

    def _handle_paste(self, event, widget_type: str) -> str:
        """Обработчик вставки через системный focus"""
        try:
            focused_widget = event.widget.focus_get()
            if focused_widget and hasattr(focused_widget, 'insert'):
                return self._paste_text(focused_widget, widget_type)
        except:
            pass
        return "break"

    def _handle_cut(self, event, widget_type: str) -> str:
        """Обработчик вырезания через системный focus"""
        try:
            focused_widget = event.widget.focus_get()
            if focused_widget and hasattr(focused_widget, 'get'):
                return self._cut_text(focused_widget, widget_type)
        except:
            pass
        return "break"

    def _handle_select_all(self, event, widget_type: str) -> str:
        """Обработчик выделения всего через системный focus"""
        try:
            focused_widget = event.widget.focus_get()
            if focused_widget:
                return self._select_all(focused_widget, widget_type)
        except:
            pass
        return "break"

    def _setup_macos_widget(self, widget):
        """Дополнительная настройка виджета для macOS"""
        try:
            # Отключаем стандартные привязки, чтобы избежать конфликтов
            widget.unbind_class("Text", "<Command-a>")
            widget.unbind_class("Entry", "<Command-a>")
            widget.unbind_class("Text", "<Command-c>")
            widget.unbind_class("Entry", "<Command-c>")
            widget.unbind_class("Text", "<Command-v>")
            widget.unbind_class("Entry", "<Command-v>")
            widget.unbind_class("Text", "<Command-x>")
            widget.unbind_class("Entry", "<Command-x>")

        except Exception as e:
            # Игнорируем ошибки unbind - они не критичны
            pass

    def _add_context_menu(self, widget: Union[tk.Entry, tk.Text], widget_type: str):
        """Добавляет контекстное меню с операциями копирования/вставки"""
        try:
            menu = tk.Menu(widget, tearoff=0)

            # Определяем символ модификатора для отображения
            mod_symbol = "⌘" if self.is_macos else "Ctrl"

            # Добавляем пункты меню
            menu.add_command(
                label=f"Копировать {mod_symbol}+C",
                command=lambda: self._copy_text(widget, widget_type)
            )
            menu.add_command(
                label=f"Вставить {mod_symbol}+V",
                command=lambda: self._paste_text(widget, widget_type)
            )
            menu.add_command(
                label=f"Вырезать {mod_symbol}+X",
                command=lambda: self._cut_text(widget, widget_type)
            )
            menu.add_separator()
            menu.add_command(
                label=f"Выделить все {mod_symbol}+A",
                command=lambda: self._select_all(widget, widget_type)
            )

            # Добавляем для Text виджетов
            if widget_type == "text":
                menu.add_separator()
                menu.add_command(
                    label=f"Отмена {mod_symbol}+Z",
                    command=lambda: self._undo(widget)
                )
                menu.add_command(
                    label=f"Повтор {mod_symbol}+Y",
                    command=lambda: self._redo(widget)
                )

            def show_context_menu(event):
                """Показать контекстное меню"""
                try:
                    menu.post(event.x_root, event.y_root)
                except Exception:
                    pass

            # Привязываем к правой кнопке мыши
            widget.bind("<Button-2>", show_context_menu)  # macOS/Linux
            widget.bind("<Button-3>", show_context_menu)  # Windows

            # Также привязываем к Ctrl+клик на macOS
            if self.is_macos:
                widget.bind("<Control-Button-1>", show_context_menu)

            self.log_info(f"Контекстное меню добавлено для {widget_type}")

        except Exception as e:
            self.log_error(f"Ошибка добавления контекстного меню: {e}")

    def _copy_text(self, widget: Union[tk.Entry, tk.Text], widget_type: str) -> str:
        """Копирование текста"""
        try:
            if widget_type == "entry":
                if hasattr(widget, 'selection_present') and widget.selection_present():
                    text = widget.selection_get()
                else:
                    text = widget.get()
            else:  # text
                if widget.tag_ranges("sel"):
                    text = widget.get("sel.first", "sel.last")
                else:
                    text = widget.get("1.0", "end-1c")

            # Копируем в буфер
            widget.clipboard_clear()
            widget.clipboard_append(text)

            self.log_info(f"Скопирован текст ({len(text)} символов)")
            return "break"

        except Exception as e:
            self.log_error(f"Ошибка копирования: {e}")
            return "break"

    def _paste_text(self, widget: Union[tk.Entry, tk.Text], widget_type: str) -> str:
        """Вставка текста"""
        try:
            text = widget.clipboard_get()

            if widget_type == "entry":
                if hasattr(widget, 'selection_present') and widget.selection_present():
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)
            else:  # text
                if widget.tag_ranges("sel"):
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)

            self.log_info(f"Вставлен текст ({len(text)} символов)")
            return "break"

        except Exception as e:
            self.log_error(f"Ошибка вставки: {e}")
            return "break"

    def _cut_text(self, widget: Union[tk.Entry, tk.Text], widget_type: str) -> str:
        """Вырезание текста"""
        try:
            if widget_type == "entry":
                if hasattr(widget, 'selection_present') and widget.selection_present():
                    text = widget.selection_get()
                    widget.clipboard_clear()
                    widget.clipboard_append(text)
                    widget.delete("sel.first", "sel.last")
            else:  # text
                if widget.tag_ranges("sel"):
                    text = widget.get("sel.first", "sel.last")
                    widget.clipboard_clear()
                    widget.clipboard_append(text)
                    widget.delete("sel.first", "sel.last")

            self.log_info("Текст вырезан")
            return "break"

        except Exception as e:
            self.log_error(f"Ошибка вырезания: {e}")
            return "break"

    def _select_all(self, widget: Union[tk.Entry, tk.Text], widget_type: str) -> str:
        """Выделение всего текста"""
        try:
            if widget_type == "entry":
                widget.select_range(0, 'end')
            else:  # text
                widget.tag_add("sel", "1.0", "end-1c")
                widget.mark_set("insert", "1.0")
                widget.see("insert")

            self.log_info("Весь текст выделен")
            return "break"

        except Exception as e:
            self.log_error(f"Ошибка выделения: {e}")
            return "break"

    def _undo(self, widget: tk.Text) -> str:
        """Отмена для Text виджета"""
        try:
            widget.edit_undo()
            self.log_info("Отмена выполнена")
            return "break"
        except:
            return "break"

    def _redo(self, widget: tk.Text) -> str:
        """Повтор для Text виджета"""
        try:
            widget.edit_redo()
            self.log_info("Повтор выполнен")
            return "break"
        except:
            return "break"

    def get_statistics(self) -> dict:
        """Получение статистики плагина"""
        return {
            "registered_widgets": len(self.registered_widgets),
            "platform": platform.system(),
            "modifier_key": self.modifier_key,
            "is_macos": self.is_macos
        }

    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина горячих клавиш")
        self.registered_widgets.clear()
        self.log_info("Плагин горячих клавиш завершен")
