#!/usr/bin/env python3
"""
Скрипт для исправления импортов после реорганизации плагинов
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Исправляет импорты в файле"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Исправляем импорты core
    content = re.sub(
        r'from \.\.\.core\.event_system import EventType',
        'from src.core.event_system import EventType',
        content
    )

    content = re.sub(
        r'from \.\.\.core\.event_system import event_system, EventType',
        'from src.core.event_system import event_system, EventType',
        content
    )

    # Исправляем импорты base_plugin
    content = re.sub(
        r'from \.\.base_plugin import BasePlugin',
        'from src.plugins.base_plugin import BasePlugin',
        content
    )

    # Исправляем импорты между плагинами
    content = re.sub(
        r'from \.\.text_processing\.text_processing_plugin import TextProcessingPlugin',
        'from src.plugins.post_processor.text_processing.text_processing_plugin import TextProcessingPlugin',
        content
    )

    content = re.sub(
        r'from \.\.deduplication\.deduplication_plugin import DeduplicationPlugin',
        'from src.plugins.post_processor.deduplication.deduplication_plugin import DeduplicationPlugin',
        content
    )

    content = re.sub(
        r'from \.\.filter\.filter_plugin import FilterPlugin',
        'from src.plugins.post_processor.filter.filter_plugin import FilterPlugin',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Исправлен {file_path}")

def main():
    """Основная функция"""
    src_dir = Path("src/plugins")

    # Список файлов для исправления
    files_to_fix = [
        "post_processor/filter/filter_plugin.py",
        "post_processor/text_processing/text_processing_plugin.py",
        "post_processor/deduplication/deduplication_plugin.py",
        "post_processor/post_processor_plugin.py",
        "monitoring/monitoring_plugin.py",
        "database/database_plugin.py",
        "token_manager/token_manager_plugin.py",
        "settings_manager/settings_manager_plugin.py",
        "vk_search/vk_search_plugin.py",
        "logger/logger_plugin.py",
        "link_comparator/link_comparator_plugin.py",
        "google_sheets/google_sheets_plugin.py"
    ]

    for file_path in files_to_fix:
        full_path = src_dir / file_path
        if full_path.exists():
            fix_imports_in_file(full_path)
        else:
            print(f"⚠️ Файл не найден: {full_path}")

if __name__ == "__main__":
    main()
