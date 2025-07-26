"""
Плагин для управления токенами доступа
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.event_system import EventType
from src.plugins.base_plugin import BasePlugin


class TokenManagerPlugin(BasePlugin):
    """Плагин для управления токенами доступа"""

    def __init__(self):
        super().__init__()
        self.name = "TokenManagerPlugin"
        self.version = "1.0.0"
        self.description = "Плагин для управления токенами доступа к API"

        # Конфигурация по умолчанию
        self.config = {
            "tokens_file": "config/tokens.json",
            "encrypt_tokens": True,
            "auto_refresh": True,
            "backup_tokens": True,
        }

        self.tokens: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> None:
        """Инициализация плагина"""
        self.log_info("Инициализация плагина Token Manager")

        if not self.validate_config():
            self.log_error("Некорректная конфигурация плагина")
            return

        # Создаем директорию для токенов если не существует
        Path(self.config["tokens_file"]).parent.mkdir(parents=True, exist_ok=True)

        # Загружаем токены
        self._load_tokens()
        self._load_vk_tokens_from_txt()

        self.log_info("Плагин Token Manager инициализирован")
        self.emit_event(EventType.PLUGIN_LOADED, {"status": "initialized"})

    def shutdown(self) -> None:
        """Завершение работы плагина"""
        self.log_info("Завершение работы плагина Token Manager")

        # Сохраняем токены перед завершением
        self._save_tokens()

        self.emit_event(EventType.PLUGIN_UNLOADED, {"status": "shutdown"})
        self.log_info("Плагин Token Manager завершен")

    def _load_tokens(self) -> None:
        """Загружает токены из файла"""
        try:
            if os.path.exists(self.config["tokens_file"]):
                with open(self.config["tokens_file"], "r", encoding="utf-8") as f:
                    self.tokens = json.load(f)
                self.log_info(f"Загружено {len(self.tokens)} токенов")
            else:
                self.tokens = {}
                self.log_info("Файл токенов не найден, создан новый")
        except Exception as e:
            self.log_error(f"Ошибка загрузки токенов: {e}")
            self.tokens = {}

    def _save_tokens(self) -> None:
        """Сохраняет токены в файл"""
        try:
            with open(self.config["tokens_file"], "w", encoding="utf-8") as f:
                json.dump(self.tokens, f, ensure_ascii=False, indent=2)
            self.log_info("Токены сохранены")
        except Exception as e:
            self.log_error(f"Ошибка сохранения токенов: {e}")

    def add_token(self, service: str, token: str, expires_at: Optional[str] = None, description: str = "") -> bool:
        """Добавляет новый токен"""
        if not token or not service:
            self.log_error("Токен и сервис не могут быть пустыми")
            return False

        # Проверяем валидность токена
        if not self._validate_token(service, token):
            self.log_error(f"Токен для сервиса {service} невалиден")
            return False

        # Создаем запись токена
        token_data = {
            "token": token,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "description": description,
            "last_used": None,
            "usage_count": 0,
        }

        self.tokens[service] = token_data
        self._save_tokens()

        self.log_info(f"Токен для сервиса {service} добавлен")
        return True

    def get_token(self, service: str) -> Optional[str]:
        """Получает токен для указанного сервиса"""
        if service not in self.tokens:
            self.log_warning(f"Токен для сервиса {service} не найден")
            return None

        token_data = self.tokens[service]

        # Проверяем срок действия
        if token_data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                if datetime.now() > expires_at:
                    self.log_warning(f"Токен для сервиса {service} истек")
                    return None
            except Exception as e:
                self.log_error(f"Ошибка проверки срока действия токена: {e}")

        # Обновляем статистику использования
        token_data["last_used"] = datetime.now().isoformat()
        token_data["usage_count"] = token_data.get("usage_count", 0) + 1
        self._save_tokens()

        return token_data["token"]

    def remove_token(self, service: str) -> bool:
        """Удаляет токен для указанного сервиса"""
        if service not in self.tokens:
            self.log_warning(f"Токен для сервиса {service} не найден")
            return False

        del self.tokens[service]
        self._save_tokens()

        self.log_info(f"Токен для сервиса {service} удален")
        return True

    def update_token(self, service: str, new_token: str, expires_at: Optional[str] = None) -> bool:
        """Обновляет токен для указанного сервиса"""
        if service not in self.tokens:
            self.log_error(f"Токен для сервиса {service} не найден")
            return False

        if not self._validate_token(service, new_token):
            self.log_error(f"Новый токен для сервиса {service} невалиден")
            return False

        token_data = self.tokens[service]
        token_data["token"] = new_token
        token_data["updated_at"] = datetime.now().isoformat()

        if expires_at:
            token_data["expires_at"] = expires_at

        self._save_tokens()

        self.log_info(f"Токен для сервиса {service} обновлен")
        return True

    def get_token_info(self, service: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о токене"""
        if service not in self.tokens:
            return None

        return self.tokens[service].copy()

    def list_tokens(self) -> List[Dict[str, Any]]:
        """Возвращает список всех токенов"""
        tokens_list = []

        for service, token_data in self.tokens.items():
            token_info = {
                "service": service,
                "description": token_data.get("description", ""),
                "created_at": token_data.get("created_at"),
                "expires_at": token_data.get("expires_at"),
                "last_used": token_data.get("last_used"),
                "usage_count": token_data.get("usage_count", 0),
                "is_valid": self._is_token_valid(service),
            }
            tokens_list.append(token_info)

        return tokens_list

    def list_vk_tokens(self) -> list:
        """Возвращает список всех VK токенов"""
        return [t["token"] for s, t in self.tokens.items() if s.startswith("vk") and self._is_token_valid(s)]

    def _validate_token(self, service: str, token: str) -> bool:
        """Проверяет валидность токена"""
        if not token or len(token) < 10:
            return False

        # Специфичные проверки для разных сервисов
        if service == "vk":
            # VK токены обычно содержат определенные символы
            return len(token) > 20 and not token.isspace()
        elif service == "google":
            # Google токены имеют определенный формат
            return "ya29." in token or len(token) > 100
        else:
            # Общая проверка для других сервисов
            return len(token) > 10 and not token.isspace()

    def _is_token_valid(self, service: str) -> bool:
        """Проверяет, валиден ли токен"""
        if service not in self.tokens:
            return False

        token_data = self.tokens[service]
        token = token_data.get("token")

        if not token:
            return False

        # Проверяем срок действия
        if token_data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                if datetime.now() > expires_at:
                    return False
            except Exception:
                return False

        return self._validate_token(service, token)

    def get_expired_tokens(self) -> List[str]:
        """Возвращает список сервисов с истекшими токенами"""
        expired = []

        for service, token_data in self.tokens.items():
            if token_data.get("expires_at"):
                try:
                    expires_at = datetime.fromisoformat(token_data["expires_at"])
                    if datetime.now() > expires_at:
                        expired.append(service)
                except (ValueError, KeyError) as e:
                    self.log_warning(f"Ошибка при проверке токена {service}: {e}")
                    continue

        return expired

    def backup_tokens(self, backup_path: str = None) -> Optional[str]:
        """Создает резервную копию токенов"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"config/tokens_backup_{timestamp}.json"

        try:
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(self.tokens, f, ensure_ascii=False, indent=2)

            self.log_info(f"Резервная копия токенов создана: {backup_file}")
            return str(backup_file)

        except Exception as e:
            self.log_error(f"Ошибка создания резервной копии: {e}")
            return None

    def restore_tokens(self, backup_path: str) -> bool:
        """Восстанавливает токены из резервной копии"""
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_tokens = json.load(f)

            self.tokens = backup_tokens
            self._save_tokens()

            self.log_info(f"Токены восстановлены из: {backup_path}")
            return True

        except Exception as e:
            self.log_error(f"Ошибка восстановления токенов: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику плагина"""
        total_tokens = len(self.tokens)
        valid_tokens = sum(1 for service in self.tokens if self._is_token_valid(service))
        expired_tokens = len(self.get_expired_tokens())

        return {
            "total_tokens": total_tokens,
            "valid_tokens": valid_tokens,
            "expired_tokens": expired_tokens,
            "services": list(self.tokens.keys()),
            "tokens_file": self.config["tokens_file"],
        }

    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации"""
        required_keys = ["tokens_file"]

        for key in required_keys:
            if key not in self.config:
                self.log_error(f"Отсутствует обязательный параметр: {key}")
                return False

        return True

    def get_required_config_keys(self) -> list:
        """Возвращает список обязательных ключей конфигурации"""
        return ["tokens_file"]

    def _load_vk_tokens_from_txt(self):
        vk_txt_path = "config/vk_token.txt"
        if not os.path.exists(vk_txt_path):
            self.log_warning(f"Файл VK токенов не найден: {vk_txt_path}")
            return
        with open(vk_txt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        for idx, token in enumerate(lines):
            service = f"vk{'' if idx == 0 else idx + 1}"
            self.tokens[service] = {
                "token": token,
                "created_at": datetime.now().isoformat(),
                "expires_at": None,
                "description": "",
                "last_used": None,
                "usage_count": 0,
            }
        self.log_info(f"Загружено VK токенов из vk_token.txt: {len(lines)}")
