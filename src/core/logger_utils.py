import os
from loguru import logger
from functools import wraps
import inspect

def setup_logger(log_file: str = None, level: str = "INFO"):
    """
    Настраивает глобальный логгер loguru.
    log_file: путь к файлу для логов (если None, лог только в консоль)
    level: уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=level)
    if log_file:
        logger.add(log_file, rotation="10 MB", retention="10 days", level=level, encoding="utf-8")


def log_function_call(level: str = "DEBUG"):
    """
    Декоратор для автоматического логирования вызова функции, её аргументов и результата.
    level: уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__qualname__
            arg_str = inspect.signature(func).bind(*args, **kwargs)
            arg_str.apply_defaults()
            logger.log(level, f"Вызов {func_name} с аргументами {arg_str.arguments}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"{func_name} вернула {result}")
                return result
            except Exception as e:
                logger.exception(f"Ошибка в {func_name}: {e}")
                raise
        return wrapper
    return decorator 