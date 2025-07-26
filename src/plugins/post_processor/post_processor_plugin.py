"""
Центральный плагин для обработки публикаций
Объединяет фильтрацию и дедупликацию
"""

from datetime import datetime
from typing import Any, Dict, List

from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin


class PostProcessorPlugin(BasePlugin):
    """Центральный плагин для обработки публикаций"""

    def __init__(self):
        super().__init__()
        self.name = "PostProcessorPlugin"
        self.version = "1.0.0"
        self.description = "Центральный плагин для обработки публикаций (фильтрация + дедупликация)"

        # Конфигурация по умолчанию
        self.config = {
            "enable_filtering": True,
            "enable_deduplication": True,
            "filter_method": "keywords",  # keywords, exact_match
            "deduplication_method": "link_hash",  # link_hash, text, content_hash
            "processing_order": ["deduplication", "filtering"],  # Порядок обработки
            "batch_size": 1000,
            "enable_logging": True,
        }

        # Связи с другими плагинами
        self.filter_plugin = None
        self.deduplication_plugin = None
        self.text_processing_plugin = None
        self.database_plugin = None

    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина PostProcessor")

        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return

        self.log_info("Плагин PostProcessor инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})

    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина PostProcessor")

        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин PostProcessor завершен")

    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        return True

    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return []

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        return {
            "enabled": self.is_enabled(),
            "config": self.get_config(),
            "plugins_connected": {
                "filter": self.filter_plugin is not None,
                "deduplication": self.deduplication_plugin is not None,
                "text_processing": self.text_processing_plugin is not None,
                "database": self.database_plugin is not None,
            },
        }

    def set_filter_plugin(self, filter_plugin):
        """Устанавливает связь с плагином фильтрации"""
        self.filter_plugin = filter_plugin
        self.log_info("FilterPlugin подключен к PostProcessorPlugin")

    def set_deduplication_plugin(self, deduplication_plugin):
        """Устанавливает связь с плагином дедупликации"""
        self.deduplication_plugin = deduplication_plugin
        self.log_info("DeduplicationPlugin подключен к PostProcessorPlugin")

    def set_text_processing_plugin(self, text_processing_plugin):
        """Устанавливает связь с плагином обработки текста"""
        self.text_processing_plugin = text_processing_plugin
        self.log_info("TextProcessingPlugin подключен к PostProcessorPlugin")

    def set_database_plugin(self, database_plugin):
        """Устанавливает связь с плагином базы данных"""
        self.database_plugin = database_plugin
        self.log_info("DatabasePlugin подключен к PostProcessorPlugin")

    def process_posts(
        self,
        posts: List[Dict[str, Any]],
        keywords: List[str] = None,
        exact_match: bool = True,
        remove_duplicates: bool = True,
        processing_order: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Централизованная обработка публикаций

        Args:
            posts: Список публикаций для обработки
            keywords: Ключевые слова для фильтрации
            exact_match: Точное совпадение для фильтрации
            remove_duplicates: Удалять ли дубликаты
            processing_order: Порядок обработки ['deduplication', 'filtering']

        Returns:
            Словарь с результатами обработки
        """
        if not posts:
            return {
                "original_count": 0,
                "final_count": 0,
                "filtered_count": 0,
                "duplicates_removed": 0,
                "processing_time": 0,
                "final_posts": [],
            }

        start_time = datetime.now()
        original_count = len(posts)
        current_posts = posts.copy()

        # Определяем порядок обработки (правильный: deduplication → text_processing → filtering)
        if processing_order is None:
            processing_order = self.config.get("processing_order", ["deduplication", "text_processing", "filtering"])

        self.log_info(f"🚀 Начало обработки {original_count} публикаций")
        self.log_info(f"📋 Порядок обработки: {processing_order}")

        # Этап 1: Удаление дубликатов
        duplicates_removed = 0
        if remove_duplicates and "deduplication" in processing_order:
            if self.deduplication_plugin:
                before_count = len(current_posts)
                current_posts = self.deduplication_plugin.remove_duplicates_by_link_hash(current_posts)
                duplicates_removed = before_count - len(current_posts)
                self.log_info(f"🗑️ Этап 1: Удалено {duplicates_removed} дубликатов")
            else:
                self.log_warning("DeduplicationPlugin не подключен")

        # Этап 2: Обработка текста (только если нужна фильтрация)
        text_processed = 0
        if keywords and "text_processing" in processing_order:
            if self.text_processing_plugin:
                before_count = len(current_posts)
                current_posts = self.text_processing_plugin.process_posts_text(current_posts)
                text_processed = before_count  # Количество обработанных текстов
                self.log_info(f"📝 Этап 2: Обработано {text_processed} текстов")
            else:
                self.log_warning("TextProcessingPlugin не подключен")

        # Этап 3: Фильтрация по ключевым словам
        filtered_count = 0
        if keywords and "filtering" in processing_order:
            if self.filter_plugin:
                before_count = len(current_posts)
                current_posts = self.filter_plugin.filter_posts_by_multiple_keywords(
                    current_posts, keywords, exact_match
                )
                filtered_count = before_count - len(current_posts)
                self.log_info(f"🔍 Этап 3: Отфильтровано {filtered_count} публикаций")
            else:
                self.log_warning("FilterPlugin не подключен")

        # Вычисляем время обработки
        processing_time = (datetime.now() - start_time).total_seconds()

        result = {
            "original_count": original_count,
            "final_count": len(current_posts),
            "filtered_count": filtered_count,
            "duplicates_removed": duplicates_removed,
            "text_processed": text_processed,
            "processing_time": processing_time,
            "final_posts": current_posts,
            "processing_order": processing_order,
        }

        self.log_info(
            f"✅ Обработка завершена: {original_count} → {len(current_posts)} "
            f"(дубликатов: {duplicates_removed}, текстов: {text_processed}, отфильтровано: {filtered_count})"
        )

        return result

    def process_posts_from_database(
        self, task_id: int, keywords: List[str] = None, exact_match: bool = True, remove_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Обработка публикаций из базы данных

        Args:
            task_id: ID задачи
            keywords: Ключевые слова для фильтрации
            exact_match: Точное совпадение
            remove_duplicates: Удалять ли дубликаты

        Returns:
            Словарь с результатами обработки
        """
        if not self.database_plugin:
            self.log_error("DatabasePlugin не подключен")
            return {}

        try:
            # Получаем публикации из БД
            posts = self.database_plugin.get_task_posts(task_id)

            if not posts:
                self.log_info(f"Задача {task_id} не содержит публикаций")
                return {"task_id": task_id, "posts_count": 0}

            # Обрабатываем публикации
            result = self.process_posts(posts, keywords, exact_match, remove_duplicates)
            result["task_id"] = task_id

            return result

        except Exception as e:
            self.log_error(f"Ошибка обработки публикаций из БД: {e}")
            return {}

    def clean_database_task(self, task_id: int, keywords: List[str] = None, exact_match: bool = True) -> Dict[str, int]:
        """
        Очистка задачи в базе данных (удаление дубликатов + несоответствующих)

        Args:
            task_id: ID задачи
            keywords: Ключевые слова для проверки соответствия
            exact_match: Точное совпадение

        Returns:
            Словарь с результатами очистки
        """
        if not self.database_plugin:
            self.log_error("DatabasePlugin не подключен")
            return {}

        results = {"duplicates_removed": 0, "invalid_posts_removed": 0, "total_cleaned": 0}

        try:
            # Удаляем дубликаты
            if self.deduplication_plugin:
                results["duplicates_removed"] = self.deduplication_plugin.clean_duplicates_from_database(task_id)

            # Удаляем несоответствующие публикации
            if keywords and self.filter_plugin:
                results["invalid_posts_removed"] = self.filter_plugin.clean_by_parsing_parameters(
                    task_id, keywords, exact_match
                )

            results["total_cleaned"] = results["duplicates_removed"] + results["invalid_posts_removed"]

            self.log_info(f"🧹 Очистка задачи {task_id}: {results}")
            return results

        except Exception as e:
            self.log_error(f"Ошибка очистки задачи: {e}")
            return results

    def get_processing_statistics(self, task_id: int = None) -> Dict[str, Any]:
        """
        Получает статистику обработки

        Args:
            task_id: ID задачи (None для всех задач)

        Returns:
            Словарь со статистикой
        """
        stats = {
            "filter_plugin_connected": self.filter_plugin is not None,
            "deduplication_plugin_connected": self.deduplication_plugin is not None,
            "database_plugin_connected": self.database_plugin is not None,
        }

        # Статистика дубликатов
        if self.deduplication_plugin:
            stats["duplicates"] = self.deduplication_plugin.get_database_duplicate_statistics(task_id)

        # Статистика фильтрации
        if self.filter_plugin:
            stats["filtering"] = self.filter_plugin.get_statistics()

        return stats

    # === ОПТИМИЗИРОВАННЫЕ МЕТОДЫ ОБРАБОТКИ ===

    def process_posts_optimized(
        self,
        posts: List[Dict],
        keywords: List[str] = None,
        exact_match: bool = True,
        early_termination: bool = True,
        lazy_processing: bool = True
    ) -> Dict[str, Any]:
        """
        Оптимизированная обработка с ленивой загрузкой и ранним завершением

        Args:
            posts: Список публикаций
            keywords: Ключевые слова для фильтрации
            exact_match: Точное совпадение
            early_termination: Ранний выход при достижении лимита
            lazy_processing: Ленивая обработка (только при необходимости)
        """
        start_time = datetime.now()
        self.log_info(f"🚀 Запуск оптимизированной обработки {len(posts)} публикаций")

        current_posts = posts.copy()
        original_count = len(posts)
        stats = {
            "original_count": original_count,
            "duplicates_removed": 0,
            "text_processed": 0,
            "filtered_count": 0,
            "early_exit": False,
            "lazy_skips": 0
        }

        # Этап 1: Быстрая дедупликация по хэшам ссылок
        if self.config.get("enable_deduplication", True):
            before_count = len(current_posts)
            seen_links = set()
            unique_posts = []

            for post in current_posts:
                link_hash = post.get('link_hash', post.get('link', ''))
                if link_hash not in seen_links:
                    seen_links.add(link_hash)
                    unique_posts.append(post)

                # Ранний выход если достигли разумного лимита
                if early_termination and len(unique_posts) >= 5000:
                    stats["early_exit"] = True
                    self.log_info("⚡ Ранний выход: достигнут лимит 5000 уникальных постов")
                    break

            current_posts = unique_posts
            stats["duplicates_removed"] = before_count - len(current_posts)
            self.log_info(f"🔗 Дедупликация: удалено {stats['duplicates_removed']} дубликатов")

        # Этап 2: Ленивая обработка текста (только если есть фильтрация)
        if keywords and lazy_processing:
            # Обрабатываем текст только для постов, которые потенциально пройдут фильтрацию
            if self.text_processing_plugin:
                processed_posts = []
                for post in current_posts:
                    # Быстрая предварительная проверка
                    text = post.get('text', '').lower()
                    has_keywords = any(kw.lower() in text for kw in keywords[:3])  # Проверяем только первые 3

                    if has_keywords or not exact_match:
                        # Обрабатываем текст только у потенциально подходящих постов
                        processed_text = self.text_processing_plugin.clean_text_completely(post.get('text', ''))
                        post['cleaned_text'] = processed_text
                        processed_posts.append(post)
                        stats["text_processed"] += 1
                    else:
                        # Пропускаем обработку заведомо не подходящих постов
                        stats["lazy_skips"] += 1

                current_posts = processed_posts
                self.log_info(f"📝 Ленивая обработка: {stats['text_processed']} текстов, пропущено {stats['lazy_skips']}")

        # Этап 3: Оптимизированная фильтрация
        if keywords and self.filter_plugin:
            before_count = len(current_posts)
            # Используем cleaned_text если доступен, иначе обычный text
            for post in current_posts:
                if 'cleaned_text' not in post and self.text_processing_plugin:
                    post['cleaned_text'] = self.text_processing_plugin.clean_text_completely(post.get('text', ''))

            current_posts = self.filter_plugin.filter_posts_by_multiple_keywords(
                current_posts, keywords, exact_match
            )
            stats["filtered_count"] = before_count - len(current_posts)
            self.log_info(f"🔍 Фильтрация: отфильтровано {stats['filtered_count']} публикаций")

        # Финальная статистика
        processing_time = (datetime.now() - start_time).total_seconds()
        result = {
            **stats,
            "final_count": len(current_posts),
            "processing_time": processing_time,
            "final_posts": current_posts,
            "optimization_level": "high"
        }

        self.log_info(
            f"✅ Оптимизированная обработка завершена за {processing_time:.2f}с: "
            f"{original_count} → {len(current_posts)} (эконом: {stats['lazy_skips']} пропусков)"
        )

        return result

    def process_posts_in_batches(
        self,
        posts: List[Dict],
        keywords: List[str] = None,
        exact_match: bool = True,
        batch_size: int = None
    ) -> Dict[str, Any]:
        """
        Батчевая обработка больших объёмов данных

        Args:
            posts: Список публикаций
            keywords: Ключевые слова
            exact_match: Точное совпадение
            batch_size: Размер батча (по умолчанию из конфига)
        """
        start_time = datetime.now()
        if batch_size is None:
            batch_size = self.config.get("batch_size", 1000)

        total_posts = len(posts)
        self.log_info(f"📦 Батчевая обработка {total_posts} публикаций (батч: {batch_size})")

        all_results = []
        total_stats = {
            "original_count": total_posts,
            "batches_processed": 0,
            "duplicates_removed": 0,
            "text_processed": 0,
            "filtered_count": 0
        }

        # Обрабатываем батчами
        for i in range(0, total_posts, batch_size):
            batch = posts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_posts + batch_size - 1) // batch_size

            self.log_info(f"📦 Обработка батча {batch_num}/{total_batches} ({len(batch)} постов)")

            # Обрабатываем текущий батч
            batch_result = self.process_posts_optimized(
                batch, keywords, exact_match,
                early_termination=False,  # Не прерываем батчи досрочно
                lazy_processing=True
            )

            # Собираем результаты
            all_results.extend(batch_result["final_posts"])
            total_stats["duplicates_removed"] += batch_result["duplicates_removed"]
            total_stats["text_processed"] += batch_result["text_processed"]
            total_stats["filtered_count"] += batch_result["filtered_count"]
            total_stats["batches_processed"] += 1

            # Прогресс
            if batch_num % 5 == 0 or batch_num == total_batches:
                progress = (batch_num / total_batches) * 100
                self.log_info(f"📊 Прогресс: {progress:.1f}% ({batch_num}/{total_batches} батчей)")

        # Финальная дедупликация между батчами
        self.log_info("🔗 Финальная дедупликация между батчами...")
        seen_links = set()
        final_unique = []
        for post in all_results:
            link_hash = post.get('link_hash', post.get('link', ''))
            if link_hash not in seen_links:
                seen_links.add(link_hash)
                final_unique.append(post)

        cross_batch_duplicates = len(all_results) - len(final_unique)
        total_stats["duplicates_removed"] += cross_batch_duplicates

        processing_time = (datetime.now() - start_time).total_seconds()
        result = {
            **total_stats,
            "final_count": len(final_unique),
            "cross_batch_duplicates": cross_batch_duplicates,
            "processing_time": processing_time,
            "batch_size": batch_size,
            "final_posts": final_unique,
            "optimization_level": "batch"
        }

        self.log_info(
            f"✅ Батчевая обработка завершена за {processing_time:.2f}с: "
            f"{total_posts} → {len(final_unique)} ({total_stats['batches_processed']} батчей)"
        )

        return result

    def process_posts_with_cache(
        self,
        posts: List[Dict],
        keywords: List[str] = None,
        exact_match: bool = True,
        cache_results: bool = True
    ) -> Dict[str, Any]:
        """
        Обработка с кэшированием результатов фильтрации и обработки текста

        Args:
            posts: Список публикаций
            keywords: Ключевые слова
            exact_match: Точное совпадение
            cache_results: Кэшировать ли результаты
        """
        start_time = datetime.now()
        self.log_info(f"💾 Обработка с кэшированием {len(posts)} публикаций")

        # Инициализация кэша (простая реализация в памяти)
        if not hasattr(self, '_processing_cache'):
            self._processing_cache = {
                'text_processing': {},  # hash -> cleaned_text
                'filtering': {},        # (text_hash, keywords_hash) -> bool
                'duplicates': set()     # link_hashes
            }

        current_posts = posts.copy()
        original_count = len(posts)
        cache_hits = {"text": 0, "filter": 0, "dedup": 0}

        # Этап 1: Дедупликация с кэшем
        if self.config.get("enable_deduplication", True):
            before_count = len(current_posts)
            unique_posts = []

            for post in current_posts:
                link_hash = post.get('link_hash', post.get('link', ''))

                if link_hash in self._processing_cache['duplicates']:
                    cache_hits["dedup"] += 1
                    continue  # Пропускаем известный дубликат
                else:
                    self._processing_cache['duplicates'].add(link_hash)
                    unique_posts.append(post)

            current_posts = unique_posts
            duplicates_removed = before_count - len(current_posts)
            self.log_info(f"🔗 Дедупликация: удалено {duplicates_removed} дубликатов (кэш: {cache_hits['dedup']})")

        # Этап 2: Обработка текста с кэшем
        text_processed = 0
        if keywords and self.text_processing_plugin:
            for post in current_posts:
                text = post.get('text', '')
                text_hash = str(hash(text))

                if text_hash in self._processing_cache['text_processing']:
                    # Используем кэшированный результат
                    post['cleaned_text'] = self._processing_cache['text_processing'][text_hash]
                    cache_hits["text"] += 1
                else:
                    # Обрабатываем и кэшируем
                    cleaned_text = self.text_processing_plugin.clean_text_completely(text)
                    post['cleaned_text'] = cleaned_text
                    if cache_results:
                        self._processing_cache['text_processing'][text_hash] = cleaned_text

                text_processed += 1

            self.log_info(f"📝 Обработка текста: {text_processed} текстов (кэш: {cache_hits['text']})")

        # Этап 3: Фильтрация с кэшем
        filtered_count = 0
        if keywords and self.filter_plugin:
            before_count = len(current_posts)
            keywords_hash = str(hash(tuple(sorted(keywords)) + (exact_match,)))

            filtered_posts = []
            for post in current_posts:
                text_to_check = post.get('cleaned_text', post.get('text', ''))
                text_hash = str(hash(text_to_check))
                cache_key = (text_hash, keywords_hash)

                if cache_key in self._processing_cache['filtering']:
                    # Используем кэшированный результат
                    if self._processing_cache['filtering'][cache_key]:
                        filtered_posts.append(post)
                    cache_hits["filter"] += 1
                else:
                    # Проверяем и кэшируем результат
                    # Используем стандартный метод фильтрации для одного поста
                    single_post_result = self.filter_plugin.filter_posts_by_multiple_keywords(
                        [post], keywords, exact_match
                    )
                    matches = len(single_post_result) > 0

                    if cache_results:
                        self._processing_cache['filtering'][cache_key] = matches

                    if matches:
                        filtered_posts.append(post)

            current_posts = filtered_posts
            filtered_count = before_count - len(current_posts)
            self.log_info(f"🔍 Фильтрация: отфильтровано {filtered_count} публикаций (кэш: {cache_hits['filter']})")

        processing_time = (datetime.now() - start_time).total_seconds()
        cache_efficiency = sum(cache_hits.values()) / max(original_count, 1) * 100

        result = {
            "original_count": original_count,
            "final_count": len(current_posts),
            "filtered_count": filtered_count,
            "duplicates_removed": duplicates_removed,
            "text_processed": text_processed,
            "cache_hits": cache_hits,
            "cache_efficiency": cache_efficiency,
            "processing_time": processing_time,
            "final_posts": current_posts,
            "optimization_level": "cached"
        }

        self.log_info(
            f"✅ Кэшированная обработка завершена за {processing_time:.2f}с: "
            f"{original_count} → {len(current_posts)} (кэш: {cache_efficiency:.1f}%)"
        )

        return result

    def process_posts_parallel(
        self,
        posts: List[Dict],
        keywords: List[str] = None,
        exact_match: bool = True,
        max_workers: int = None
    ) -> Dict[str, Any]:
        """
        Параллельная обработка с использованием ThreadPoolExecutor

        Args:
            posts: Список публикаций
            keywords: Ключевые слова
            exact_match: Точное совпадение
            max_workers: Количество потоков
        """
        start_time = datetime.now()

        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
        except ImportError:
            self.log_warning("concurrent.futures недоступен, используем обычную обработку")
            return self.process_posts_optimized(posts, keywords, exact_match)

        if max_workers is None:
            max_workers = min(4, len(posts) // 1000 + 1)  # Адаптивное количество потоков

        total_posts = len(posts)
        self.log_info(f"⚡ Параллельная обработка {total_posts} публикаций ({max_workers} потоков)")

        # Разбиваем данные на чанки для параллельной обработки
        chunk_size = max(100, total_posts // max_workers)
        chunks = [posts[i:i + chunk_size] for i in range(0, total_posts, chunk_size)]

        all_results = []
        total_stats = {
            "original_count": total_posts,
            "threads_used": len(chunks),
            "duplicates_removed": 0,
            "text_processed": 0,
            "filtered_count": 0
        }

        # Параллельная обработка чанков
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Запускаем задачи
            future_to_chunk = {}
            for i, chunk in enumerate(chunks):
                future = executor.submit(
                    self._process_chunk_thread_safe,
                    chunk, keywords, exact_match, i + 1
                )
                future_to_chunk[future] = i

            # Собираем результаты
            completed_chunks = 0
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    chunk_result = future.result()
                    all_results.extend(chunk_result["final_posts"])
                    total_stats["duplicates_removed"] += chunk_result["duplicates_removed"]
                    total_stats["text_processed"] += chunk_result["text_processed"]
                    total_stats["filtered_count"] += chunk_result["filtered_count"]

                    completed_chunks += 1
                    self.log_info(f"✅ Чанк {chunk_idx + 1}/{len(chunks)} завершён ({completed_chunks}/{len(chunks)})")

                except Exception as e:
                    self.log_error(f"❌ Ошибка в чанке {chunk_idx + 1}: {e}")

        # Финальная дедупликация
        self.log_info("🔗 Финальная дедупликация между потоками...")
        seen_links = set()
        final_unique = []
        for post in all_results:
            link_hash = post.get('link_hash', post.get('link', ''))
            if link_hash not in seen_links:
                seen_links.add(link_hash)
                final_unique.append(post)

        cross_thread_duplicates = len(all_results) - len(final_unique)
        total_stats["duplicates_removed"] += cross_thread_duplicates

        processing_time = (datetime.now() - start_time).total_seconds()
        result = {
            **total_stats,
            "final_count": len(final_unique),
            "cross_thread_duplicates": cross_thread_duplicates,
            "processing_time": processing_time,
            "max_workers": max_workers,
            "chunk_size": chunk_size,
            "final_posts": final_unique,
            "optimization_level": "parallel"
        }

        self.log_info(
            f"✅ Параллельная обработка завершена за {processing_time:.2f}с: "
            f"{total_posts} → {len(final_unique)} ({max_workers} потоков)"
        )

        return result

    def _process_chunk_thread_safe(
        self,
        chunk: List[Dict],
        keywords: List[str],
        exact_match: bool,
        chunk_id: int
    ) -> Dict[str, Any]:
        """
        Thread-safe обработка чанка данных
        """
        # Используем оптимизированную обработку для каждого чанка
        return self.process_posts_optimized(
            chunk,
            keywords=keywords,
            exact_match=exact_match,
            early_termination=False,  # Не прерываем чанки досрочно
            lazy_processing=True
        )

    def clear_cache(self):
        """Очистка кэша обработки"""
        if hasattr(self, '_processing_cache'):
            self._processing_cache = {
                'text_processing': {},
                'filtering': {},
                'duplicates': set()
            }
            self.log_info("💾 Кэш обработки очищен")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        if not hasattr(self, '_processing_cache'):
            return {"cache_enabled": False}

        cache = self._processing_cache
        return {
            "cache_enabled": True,
            "text_cache_size": len(cache['text_processing']),
            "filter_cache_size": len(cache['filtering']),
            "duplicates_cache_size": len(cache['duplicates']),
            "total_memory_items": (
                len(cache['text_processing']) +
                len(cache['filtering']) +
                len(cache['duplicates'])
            )
        }

    # === КОНЕЦ ОПТИМИЗИРОВАННЫХ МЕТОДОВ ===
