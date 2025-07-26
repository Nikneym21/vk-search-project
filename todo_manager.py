#!/usr/bin/env python3
"""
TODO Manager - Простая система управления задачами

Возможности:
- Добавление новых задач
- Закрепление важных задач
- Установка приоритетов
- Отметка выполненных задач
- Просмотр статистики
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class TodoManager:
    def __init__(self, todo_file: str = "todo_tasks.json"):
        self.todo_file = todo_file
        self.tasks = self.load_tasks()
    
    def load_tasks(self) -> Dict:
        """Загрузить задачи из файла"""
        if os.path.exists(self.todo_file):
            try:
                with open(self.todo_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.get_default_structure()
        return self.get_default_structure()
    
    def save_tasks(self):
        """Сохранить задачи в файл"""
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
    
    def get_default_structure(self) -> Dict:
        """Создать структуру по умолчанию"""
        return {
            "pinned": {
                "critical": [],
                "important": []
            },
            "active": {
                "technical": [],
                "documentation": [],
                "cleanup": []
            },
            "completed": [],
            "statistics": {
                "total": 0,
                "completed": 0,
                "pinned": 0
            }
        }
    
    def add_task(self, task: str, category: str = "active", subcategory: str = "technical", 
                 priority: str = "normal", pinned: bool = False):
        """Добавить новую задачу"""
        task_obj = {
            "id": len(self.tasks["active"].get(subcategory, [])) + len(self.tasks["pinned"].get(subcategory, [])) + 1,
            "text": task,
            "created": datetime.now().isoformat(),
            "completed": False,
            "priority": priority
        }
        
        if pinned:
            if subcategory not in self.tasks["pinned"]:
                self.tasks["pinned"][subcategory] = []
            self.tasks["pinned"][subcategory].append(task_obj)
        else:
            if subcategory not in self.tasks["active"]:
                self.tasks["active"][subcategory] = []
            self.tasks["active"][subcategory].append(task_obj)
        
        self.update_statistics()
        self.save_tasks()
        print(f"✅ Задача добавлена: {task}")
    
    def complete_task(self, task_id: int, category: str = "active", subcategory: str = "technical"):
        """Отметить задачу как выполненную"""
        if category == "pinned":
            tasks = self.tasks["pinned"].get(subcategory, [])
        else:
            tasks = self.tasks["active"].get(subcategory, [])
        
        for task in tasks:
            if task["id"] == task_id:
                task["completed"] = True
                task["completed_at"] = datetime.now().isoformat()
                self.tasks["completed"].append(task)
                tasks.remove(task)
                self.update_statistics()
                self.save_tasks()
                print(f"🎉 Задача выполнена: {task['text']}")
                return
        
        print(f"❌ Задача с ID {task_id} не найдена")
    
    def pin_task(self, task_id: int, subcategory: str = "technical"):
        """Закрепить задачу"""
        tasks = self.tasks["active"].get(subcategory, [])
        for task in tasks:
            if task["id"] == task_id:
                tasks.remove(task)
                if subcategory not in self.tasks["pinned"]:
                    self.tasks["pinned"][subcategory] = []
                self.tasks["pinned"][subcategory].append(task)
                self.update_statistics()
                self.save_tasks()
                print(f"📌 Задача закреплена: {task['text']}")
                return
        
        print(f"❌ Задача с ID {task_id} не найдена")
    
    def unpin_task(self, task_id: int, subcategory: str = "technical"):
        """Открепить задачу"""
        tasks = self.tasks["pinned"].get(subcategory, [])
        for task in tasks:
            if task["id"] == task_id:
                tasks.remove(task)
                if subcategory not in self.tasks["active"]:
                    self.tasks["active"][subcategory] = []
                self.tasks["active"][subcategory].append(task)
                self.update_statistics()
                self.save_tasks()
                print(f"📌 Задача откреплена: {task['text']}")
                return
        
        print(f"❌ Задача с ID {task_id} не найдена")
    
    def update_statistics(self):
        """Обновить статистику"""
        total = 0
        completed = len(self.tasks["completed"])
        pinned = 0
        
        for category in self.tasks["active"].values():
            total += len(category)
        
        for category in self.tasks["pinned"].values():
            total += len(category)
            pinned += len(category)
        
        self.tasks["statistics"] = {
            "total": total,
            "completed": completed,
            "pinned": pinned
        }
    
    def show_tasks(self, show_completed: bool = False):
        """Показать все задачи"""
        print("\n" + "="*60)
        print("📋 СИСТЕМА УПРАВЛЕНИЯ ЗАДАЧАМИ")
        print("="*60)
        
        # Закрепленные задачи
        print("\n🎯 ЗАКРЕПЛЕННЫЕ ЗАДАЧИ:")
        for priority, tasks in self.tasks["pinned"].items():
            if tasks:
                print(f"\n🔴 {priority.upper()}:")
                for task in tasks:
                    status = "✅" if task["completed"] else "⏳"
                    print(f"  {status} [{task['id']}] {task['text']}")
        
        # Активные задачи
        print("\n📝 АКТИВНЫЕ ЗАДАЧИ:")
        for category, tasks in self.tasks["active"].items():
            if tasks:
                print(f"\n🔧 {category.upper()}:")
                for task in tasks:
                    status = "✅" if task["completed"] else "⏳"
                    priority_icon = "🔴" if task["priority"] == "critical" else "🟡" if task["priority"] == "important" else "🟢"
                    print(f"  {status} [{task['id']}] {priority_icon} {task['text']}")
        
        # Выполненные задачи
        if show_completed and self.tasks["completed"]:
            print("\n✅ ВЫПОЛНЕННЫЕ ЗАДАЧИ:")
            for task in self.tasks["completed"][-10:]:  # Последние 10
                print(f"  ✅ [{task['id']}] {task['text']}")
        
        # Статистика
        stats = self.tasks["statistics"]
        print(f"\n📊 СТАТИСТИКА:")
        print(f"  Всего задач: {stats['total']}")
        print(f"  Выполнено: {stats['completed']}")
        print(f"  Закреплено: {stats['pinned']}")
        if stats['total'] > 0:
            progress = (stats['completed'] / (stats['total'] + stats['completed'])) * 100
            print(f"  Прогресс: {progress:.1f}%")
        
        print("="*60)

def main():
    """Главная функция"""
    manager = TodoManager()
    
    while True:
        print("\n" + "="*40)
        print("📋 TODO МЕНЕДЖЕР")
        print("="*40)
        print("1. Показать задачи")
        print("2. Добавить задачу")
        print("3. Выполнить задачу")
        print("4. Закрепить задачу")
        print("5. Открепить задачу")
        print("6. Статистика")
        print("0. Выход")
        
        choice = input("\nВыберите действие (0-6): ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
        elif choice == "1":
            show_completed = input("Показать выполненные задачи? (y/n): ").lower() == 'y'
            manager.show_tasks(show_completed)
        elif choice == "2":
            task = input("Введите задачу: ").strip()
            if task:
                category = input("Категория (active/pinned): ").strip() or "active"
                subcategory = input("Подкатегория (technical/documentation/cleanup): ").strip() or "technical"
                priority = input("Приоритет (normal/important/critical): ").strip() or "normal"
                pinned = input("Закрепить? (y/n): ").lower() == 'y'
                manager.add_task(task, category, subcategory, priority, pinned)
        elif choice == "3":
            task_id = input("Введите ID задачи: ").strip()
            if task_id.isdigit():
                category = input("Категория (active/pinned): ").strip() or "active"
                subcategory = input("Подкатегория: ").strip() or "technical"
                manager.complete_task(int(task_id), category, subcategory)
        elif choice == "4":
            task_id = input("Введите ID задачи для закрепления: ").strip()
            if task_id.isdigit():
                subcategory = input("Подкатегория: ").strip() or "technical"
                manager.pin_task(int(task_id), subcategory)
        elif choice == "5":
            task_id = input("Введите ID задачи для открепления: ").strip()
            if task_id.isdigit():
                subcategory = input("Подкатегория: ").strip() or "technical"
                manager.unpin_task(int(task_id), subcategory)
        elif choice == "6":
            manager.show_tasks()
        else:
            print("❌ Неверный выбор!")

if __name__ == "__main__":
    main() 