"""
Менеджер плагинов - центральное ядро системы.
Координирует загрузку, зависимости и взаимодействие всех плагинов.
"""

import asyncio
import importlib
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import src.plugins
from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin
from loguru import logger


class PluginManager:
    """Менеджер для загрузки и управления плагинами"""

    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._plugin_cache: Dict[str, Any] = {}  # Кэш плагинов
        self._init_times: Dict[str, float] = {}  # Времена инициализации

    def load_plugins(self, use_cache: bool = True) -> None:
        """
        Загружает все доступные плагины из PLUGIN_CLASSES

        Args:
            use_cache: Использовать кэширование для ускорения загрузки
        """
        try:
            from src.plugins import PLUGIN_CLASSES
            import time

            start_time = time.time()
            logger.info(f"🔄 Загрузка {len(PLUGIN_CLASSES)} плагинов из PLUGIN_CLASSES")

            # Группируем плагины по типам для оптимизации
            core_plugins = []  # Основные плагины (загружаем первыми)
            service_plugins = []  # Служебные плагины
            ui_plugins = []  # Плагины интерфейса (загружаем последними)

            plugin_priorities = {
                'database': 1,
                'logger': 1,
                'settings_manager': 1,
                'hotkeys': 2,
                'token_manager': 2,
                'vk_search': 2,
                'filter': 3,
                'deduplication': 3,
                'text_processing': 3,
                'post_processor': 4,
                'monitoring': 5,
                'google_sheets': 5,
                'link_comparator': 5
            }

            # Сортируем плагины по приоритету
            sorted_plugins = sorted(
                PLUGIN_CLASSES.items(),
                key=lambda x: plugin_priorities.get(x[0], 999)
            )

            for plugin_name, plugin_class in sorted_plugins:
                try:
                    plugin_start = time.time()

                    # Проверяем кэш
                    if use_cache and plugin_name in self._plugin_cache:
                        self.plugins[plugin_name] = self._plugin_cache[plugin_name]
                        logger.info(f"📦 Плагин загружен из кэша: {plugin_name}")
                        continue

                    # Создаем экземпляр плагина
                    plugin_instance = plugin_class()
                    self.plugins[plugin_name] = plugin_instance

                    # Кэшируем для следующего использования
                    if use_cache:
                        self._plugin_cache[plugin_name] = plugin_instance

                    plugin_time = time.time() - plugin_start
                    self._init_times[plugin_name] = plugin_time

                    logger.info(f"✅ Плагин загружен: {plugin_name} -> {plugin_class.__name__} ({plugin_time:.3f}с)")

                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки плагина {plugin_name}: {e}")

            total_time = time.time() - start_time
            logger.info(f"🎯 Всего загружено плагинов: {len(self.plugins)} за {total_time:.3f}с")

            # Выводим статистику времени загрузки
            if self._init_times:
                slowest = max(self._init_times.items(), key=lambda x: x[1])
                logger.info(f"⏱️ Самый медленный плагин: {slowest[0]} ({slowest[1]:.3f}с)")

        except ImportError as e:
            logger.error(f"❌ Не удалось импортировать PLUGIN_CLASSES: {e}")
            # Fallback к старому методу
            self._load_plugins_fallback()

    def _load_plugins_fallback(self) -> None:
        """Fallback метод загрузки плагинов по директориям"""
        logger.info("🔄 Используется fallback загрузка плагинов")
        plugins_path = Path("src/plugins")

        if not plugins_path.exists():
            logger.warning("Директория плагинов не найдена")
            return

        for plugin_dir in plugins_path.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("_"):
                self._load_plugin_from_directory(plugin_dir)

    def _load_plugin_from_directory(self, plugin_dir: Path) -> None:
        """Загружает отдельный плагин"""
        plugin_name = plugin_dir.name

        try:
            # Импортируем модуль плагина
            module_path = f"src.plugins.{plugin_name}.{plugin_name}_plugin"
            module = importlib.import_module(module_path)

            # Ищем класс плагина
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj != BasePlugin:

                    # Создаем экземпляр плагина
                    plugin_instance = obj()
                    self.plugins[plugin_name] = plugin_instance

                    logger.info(f"Плагин загружен: {plugin_name} -> {type(plugin_instance).__name__}")
                    break
            else:
                logger.warning(f"Класс плагина не найден в {plugin_name}")

        except ImportError as e:
            logger.error(f"Ошибка загрузки плагина {plugin_name}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке плагина {plugin_name}: {e}")

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Получает плагин по имени"""
        return self.plugins.get(name)

    def get_logger(self):
        """Получает логгер для плагинов"""
        from loguru import logger

        return logger

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Возвращает все загруженные плагины"""
        return self.plugins.copy()

    def execute_plugin_method(self, plugin_name: str, method_name: str, *args, **kwargs) -> Any:
        """Выполняет метод плагина"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Плагин {plugin_name} не найден")

        if not hasattr(plugin, method_name):
            raise AttributeError(f"Метод {method_name} не найден в плагине {plugin_name}")

        method = getattr(plugin, method_name)
        return method(*args, **kwargs)

    def initialize_plugins(self) -> None:
        """Инициализирует все загруженные плагины"""
        for name, plugin in self.plugins.items():
            try:
                plugin.initialize()
                logger.info(f"Плагин инициализирован: {name}")
            except Exception as e:
                logger.error(f"Ошибка инициализации плагина {name}: {e}")

        # Устанавливаем зависимости между плагинами
        self.setup_plugin_dependencies()

    def setup_plugin_dependencies(self):
        """Устанавливает зависимости между плагинами"""
        logger.info("🔗 Настройка зависимостей между плагинами...")

        # FilterPlugin -> DatabasePlugin
        filter_plugin = self.get_plugin("filter")
        database_plugin = self.get_plugin("database")

        if filter_plugin and database_plugin:
            if hasattr(filter_plugin, "set_database_plugin"):
                filter_plugin.set_database_plugin(database_plugin)
                logger.info("✅ FilterPlugin подключен к DatabasePlugin")
            else:
                logger.warning("FilterPlugin не имеет метода set_database_plugin")

        # DeduplicationPlugin -> DatabasePlugin
        deduplication_plugin = self.get_plugin("deduplication")

        if deduplication_plugin and database_plugin:
            if hasattr(deduplication_plugin, "set_database_plugin"):
                deduplication_plugin.set_database_plugin(database_plugin)
                logger.info("✅ DeduplicationPlugin подключен к DatabasePlugin")
            else:
                logger.warning("DeduplicationPlugin не имеет метода set_database_plugin")

        # PostProcessorPlugin -> FilterPlugin, DeduplicationPlugin, TextProcessingPlugin, DatabasePlugin
        post_processor_plugin = self.get_plugin("post_processor")
        text_processing_plugin = self.get_plugin("text_processing")

        if post_processor_plugin:
            if filter_plugin and hasattr(post_processor_plugin, "set_filter_plugin"):
                post_processor_plugin.set_filter_plugin(filter_plugin)
                logger.info("✅ PostProcessorPlugin подключен к FilterPlugin")

            if deduplication_plugin and hasattr(post_processor_plugin, "set_deduplication_plugin"):
                post_processor_plugin.set_deduplication_plugin(deduplication_plugin)
                logger.info("✅ PostProcessorPlugin подключен к DeduplicationPlugin")

            if text_processing_plugin and hasattr(post_processor_plugin, "set_text_processing_plugin"):
                post_processor_plugin.set_text_processing_plugin(text_processing_plugin)
                logger.info("✅ PostProcessorPlugin подключен к TextProcessingPlugin")
            else:
                logger.warning("TextProcessingPlugin не найден или не имеет нужного метода")

            if database_plugin and hasattr(post_processor_plugin, "set_database_plugin"):
                post_processor_plugin.set_database_plugin(database_plugin)
                logger.info("✅ PostProcessorPlugin подключен к DatabasePlugin")

        # VKSearchPlugin -> TokenManagerPlugin
        vk_plugin = self.get_plugin("vk_search")
        token_manager = self.get_plugin("token_manager")

        if vk_plugin and token_manager:
            if hasattr(vk_plugin, "set_token_manager"):
                vk_plugin.set_token_manager(token_manager)
                logger.info("✅ VKSearchPlugin подключен к TokenManagerPlugin")
            else:
                logger.warning("VKSearchPlugin не имеет метода set_token_manager")

        # DatabasePlugin -> FilterPlugin (обратная связь)
        if database_plugin and filter_plugin:
            if hasattr(database_plugin, "set_filter_plugin"):
                database_plugin.set_filter_plugin(filter_plugin)
                logger.info("✅ DatabasePlugin подключен к FilterPlugin")

        logger.info("🔗 Настройка зависимостей завершена")

    def shutdown_plugins(self) -> None:
        """Завершает работу всех плагинов"""
        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
                logger.info(f"Плагин завершен: {name}")
            except Exception as e:
                logger.error(f"Ошибка завершения плагина {name}: {e}")

    def get_plugin_status(self) -> Dict[str, str]:
        """Получает статус всех плагинов"""
        status = {}
        for name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, "is_initialized"):
                    status[name] = "✅ Инициализирован" if plugin.is_initialized() else "❌ Не инициализирован"
                else:
                    status[name] = "✅ Загружен"
            except Exception as e:
                status[name] = f"❌ Ошибка: {e}"
        return status

    def validate_plugin_dependencies(self) -> Dict[str, List[str]]:
        """Проверяет зависимости между плагинами"""
        dependencies = {}

        # Проверяем необходимые плагины
        required_plugins = ["database", "filter", "vk_search", "token_manager"]

        for plugin_name in required_plugins:
            plugin = self.get_plugin(plugin_name)
            if plugin:
                dependencies[plugin_name] = ["✅ Найден"]
            else:
                dependencies[plugin_name] = ["❌ Не найден"]

        return dependencies

    async def coordinate_search_and_filter(
        self,
        keywords: List[str],
        start_date: str,
        end_date: str,
        exact_match: bool = True,
        minus_words: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Координация поиска и фильтрации с параллельной обработкой
        """
        import time

        start_time = time.time()
        logger = self.get_logger()

        try:
            # Автоматически включаем режим больших объемов для LoggerPlugin
            if len(keywords) > 20:
                logger_plugin = self.get_plugin("logger")
                if logger_plugin:
                    logger_plugin.set_high_volume_mode(True)
                    logger.info(f"🔧 Включен режим больших объемов для {len(keywords)} ключевых фраз")

            logger.info(f"🚀 Координация поиска и фильтрации для {len(keywords)} ключевых слов")

            # Получаем VKSearchPlugin
            vk_plugin = self.get_plugin("vk_search")
            if not vk_plugin:
                raise ValueError("VKSearchPlugin не найден")

            # Получаем токен из TokenManagerPlugin
            token_manager = self.get_plugin("token_manager")
            if not token_manager:
                raise ValueError("TokenManagerPlugin не найден")

            # Получаем VK токен
            token = token_manager.get_token("vk")
            if not token:
                # Пытаемся загрузить из файла
                try:
                    with open("config/vk_token.txt", "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith("#") and not line.startswith("//"):
                                token = line
                                break
                except Exception as e:
                    logger.error(f"Ошибка загрузки токена из файла: {e}")

            if not token:
                raise ValueError("Токен VK не найден ни в TokenManager, ни в файле")

            # Устанавливаем токен в VKSearchPlugin
            vk_plugin.config["access_token"] = token
            logger.info("Токен VK установлен в VKSearchPlugin")

            # Обрабатываем даты - если передана только дата, добавляем время
            if isinstance(start_date, str) and len(start_date.split()) == 1:
                start_date = f"{start_date} 00:00"
            if isinstance(end_date, str) and len(end_date.split()) == 1:
                end_date = f"{end_date} 23:59"

            # Получаем все доступные токены для ротации
            all_tokens = token_manager.list_vk_tokens()
            if not all_tokens:
                # Если нет токенов в менеджере, используем токен из файла
                all_tokens = [token]

            logger.info(f"Доступно токенов для ротации: {len(all_tokens)}")

            # Создаем пары (ключевое слово, токен) с ротацией токенов
            keyword_token_pairs = []
            for i, keyword in enumerate(keywords):
                token_index = i % len(all_tokens)
                selected_token = all_tokens[token_index]
                keyword_token_pairs.append((keyword, selected_token))

            logger.info(f"Создано {len(keyword_token_pairs)} пар (ключевое слово, токен) с ротацией")

            # Выполняем поиск с параллельной фильтрацией
            raw_posts = await vk_plugin.mass_search_with_tokens(
                keyword_token_pairs, start_date, end_date, exact_match, minus_words
            )

            logger.info(f"📊 Получено {len(raw_posts)} сырых постов от VK API")

            # Параллельная фильтрация
            filter_plugin = self.get_plugin("filter")
            if not filter_plugin:
                raise ValueError("FilterPlugin не найден")

            # Используем новую параллельную фильтрацию
            filtered_posts = await filter_plugin.filter_posts_comprehensive_parallel(raw_posts, keywords, exact_match)

            execution_time = time.time() - start_time
            logger.info(f"✅ Отфильтровано {len(filtered_posts)} постов за {execution_time:.2f} сек")

            # Отключаем режим больших объемов после завершения
            if len(keywords) > 20:
                logger_plugin = self.get_plugin("logger")
                if logger_plugin:
                    logger_plugin.set_high_volume_mode(False)

            return filtered_posts

        except Exception as e:
            logger.error(f"Ошибка координации поиска: {e}")
            return []

    async def coordinate_full_search(
        self,
        keywords: List[str],
        api_keywords: List[str],
        start_ts: int,
        end_ts: int,
        exact_match: bool = True,
        minus_words: List[str] = None,
        start_date: str = None,
        start_time: str = None,
        end_date: str = None,
        end_time: str = None,
        progress_callback=None,
        disable_local_filtering: bool = False  # Новый параметр
    ) -> dict:
        """
        Полная координация поиска: VKSearch → PostProcessor → Database → Export

        Args:
            keywords: Оригинальные ключевые слова для фильтрации
            api_keywords: Обработанные ключевые слова для API
            start_ts, end_ts: Временные метки для API
            exact_match: Точное соответствие
            minus_words: Исключаемые слова
            start_date, start_time, end_date, end_time: Для фильтрации результатов
            progress_callback: Функция обратного вызова для прогресса

        Returns:
            {"filepath": str, "posts_count": int, "task_id": int}
        """
        from datetime import datetime

        start_time_all = time.time()
        logger = self.get_logger()

        try:
            logger.info(f"🚀 Начинаем полный поиск по {len(keywords)} запросам")

            # 1. Получаем необходимые плагины
            vk_plugin = self.get_plugin("vk_search")
            token_manager = self.get_plugin("token_manager")
            post_processor = self.get_plugin("post_processor")
            database_plugin = self.get_plugin("database")

            if not all([vk_plugin, token_manager, database_plugin]):
                raise ValueError("Не все необходимые плагины доступны")

            # 2. Инициализация поиска
            if progress_callback:
                progress_callback(f"Инициализация поиска по {len(keywords)} запросам...", 0)

            # Получаем токены для ротации
            all_tokens = token_manager.list_vk_tokens()
            if not all_tokens:
                # Fallback к файлу токенов
                try:
                    with open("config/vk_token.txt", "r", encoding="utf-8") as f:
                        all_tokens = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                except Exception:
                    raise ValueError("Токены VK не найдены")

            logger.info(f"Доступно токенов: {len(all_tokens)}")

            # 3. Выполняем поиск через VKSearchPlugin
            if progress_callback:
                progress_callback("Выполняется поиск в VK...", 10)

            search_results = await vk_plugin.mass_search_with_tokens(
                queries=api_keywords,
                start_date=start_ts,
                end_date=end_ts,
                exact_match=exact_match,
                minus_words=minus_words or [],
                tokens=all_tokens
            )

            logger.info(f"Найдено {len(search_results)} постов через VKSearchPlugin")

            # 4. Создаём задачу в базе данных
            if progress_callback:
                progress_callback("Создание задачи в базе данных...", 30)

            task_params = {
                "keywords": keywords,
                "start_date": start_date,
                "start_time": start_time,
                "end_date": end_date,
                "end_time": end_time,
                "exact_match": exact_match,
                "minus_words": minus_words or []
            }

            task_id = database_plugin.create_task(
                task_name=f"Поиск: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''} [{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}]",
                keywords=keywords,
                start_date=start_date,
                end_date=end_date,
                exact_match=exact_match,
                minus_words=minus_words or []
            )

            if task_id is None:
                logger.error("Не удалось создать задачу в базе данных")
                if progress_callback:
                    progress_callback("Ошибка создания задачи", 100)
                return {
                    "success": False,
                    "error": "Не удалось создать задачу в базе данных",
                    "task_id": None,
                    "posts_count": len(search_results) if search_results else 0,
                    "filepath": None,
                    "execution_time": time.time() - start_time
                }

            # 5. Сохраняем сырые результаты
            if progress_callback:
                progress_callback("Сохранение результатов поиска...", 50)

            if search_results:
                database_plugin.save_posts(task_id, search_results)
                logger.info(f"Сохранено {len(search_results)} постов для задачи {task_id}")

            # Постобработка (если включена локальная фильтрация)
            if not disable_local_filtering and post_processor and search_results:
                logger.info(f"🔄 Запуск постобработки для {len(search_results)} постов...")

                processed_results = await post_processor.process_posts(
                    search_results,
                    keywords,
                    remove_duplicates=False,  # Дедупликацию уже провели в VKSearch
                    clean_text=True,
                    filter_keywords=True
                )

                if isinstance(processed_results, dict):
                    final_posts = processed_results.get('final_posts', search_results)
                    logger.info(f"Постобработка: {len(search_results)} → {len(final_posts)} постов")
                else:
                    final_posts = processed_results
                    logger.info(f"Постобработка: {len(search_results)} → {len(final_posts)} постов")
            elif disable_local_filtering:
                logger.info(f"🚫 Локальная фильтрация отключена. Используем только VK API + строгую фильтрацию: {len(search_results)} постов")
                final_posts = search_results
            else:
                logger.warning("PostProcessorPlugin недоступен")
                final_posts = search_results

            # 7. Экспорт результатов в CSV
            if progress_callback:
                progress_callback("Экспорт результатов...", 90)

            filename = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = None

            if processed_results:
                try:
                    filepath = database_plugin.export_task_to_csv(task_id, filename)
                    logger.info(f"Результаты экспортированы в {filepath}")
                except Exception as e:
                    logger.error(f"Ошибка экспорта: {e}")

            # 8. Завершение
            elapsed = time.time() - start_time_all
            database_plugin.update_task_status(task_id, "completed")

            if progress_callback:
                progress_callback(f"Поиск завершён! Найдено {len(processed_results)} постов", 100)

            logger.info(f"✅ Полный поиск завершён за {elapsed:.1f}с. Задача: {task_id}")

            return {
                "filepath": filepath,
                "posts_count": len(processed_results),
                "task_id": task_id,
                "elapsed_time": elapsed
            }

        except Exception as e:
            logger.error(f"Ошибка координации полного поиска: {e}")
            if progress_callback:
                progress_callback(f"Ошибка: {str(e)}", 0)
            raise

    def _format_search_results(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Форматирует результаты поиска для отображения"""
        from datetime import datetime

        formatted_results = []
        for post in posts:
            # Получаем информацию о посте
            owner_id = post.get("owner_id", 0)
            post_id = post.get("id", 0)
            text = post.get("text", "")
            date = post.get("date", 0)

            # Форматируем дату
            if date:
                dt = datetime.fromtimestamp(date)
                formatted_date = dt.strftime("%H:%M %d.%m.%Y")
            else:
                formatted_date = ""

            # Получаем статистику
            likes = post.get("likes", {})
            comments = post.get("comments", {})
            reposts = post.get("reposts", {})
            views = post.get("views", {})

            # Извлекаем значения
            likes_count = likes.get("count", 0) if isinstance(likes, dict) else likes
            comments_count = comments.get("count", 0) if isinstance(comments, dict) else comments
            reposts_count = reposts.get("count", 0) if isinstance(reposts, dict) else reposts
            views_count = views.get("count", 0) if isinstance(views, dict) else views

            # Формируем ссылку
            if owner_id < 0:
                author_link = f"https://vk.com/club{abs(owner_id)}"
            else:
                author_link = f"https://vk.com/id{owner_id}"

            formatted_post = {
                "link": f"https://vk.com/wall{owner_id}_{post_id}",
                "text": text,
                "type": "Пост",
                "author": post.get("author_name", ""),
                "author_link": author_link,
                "date": formatted_date,
                "likes": likes_count,
                "comments": comments_count,
                "reposts": reposts_count,
                "views": views_count,
            }
            formatted_results.append(formatted_post)

        return formatted_results

    def get_load_stats(self) -> Dict[str, Any]:
        """Получение статистики загрузки плагинов"""
        return {
            "total_plugins": len(self.plugins),
            "cached_plugins": len(self._plugin_cache),
            "init_times": self._init_times.copy(),
            "total_time": sum(self._init_times.values()),
            "average_time": sum(self._init_times.values()) / len(self._init_times) if self._init_times else 0
        }

    def clear_plugin_cache(self) -> None:
        """Очистка кэша плагинов"""
        self._plugin_cache.clear()
        logger.info("🧹 Кэш плагинов очищен")
