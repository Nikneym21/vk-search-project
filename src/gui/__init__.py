"""
GUI модули для приложения
"""

from .link_comparator_interface import LinkComparatorInterface
from .main_interface import MainInterface
from .settings_adapter import SettingsAdapter
from .vk_parser_interface import VKParserInterface

__all__ = ["MainInterface", "LinkComparatorInterface", "VKParserInterface", "SettingsAdapter"]
