# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""
Модуль конфигурации.
Отвечает за чтение/запись `data/config.json` и предоставляет единый API
для тем, категорий и настроек безопасности.
"""
import os
import json
import logging
import shutil
import time
import copy
from typing import Dict, Any

from core.localization import get_effective_app_lang
from core.utils import get_base_dir

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class ConfigHandler:
    """Класс для работы с конфигурационным файлом."""
    
    _DEFAULT_CONFIG_RU = {
        "theme": "light",
        "safety": {"check_file_size": True, "max_size_mb": 500},
        "categories": {
            "Изображения": {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"],
                "keywords": []
            },
            "Видео": {
                "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
                "keywords": []
            },
            "Аудио": {
                "extensions": [".mp3", ".wav", ".ogg", ".m4a", ".mid", ".midi"],
                "keywords": []
            },
            "Документы": {
                "extensions": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
                "keywords": []
            },
            "Архивы": {
                "extensions": [".zip", ".rar", ".7z", ".tar", ".gz"],
                "keywords": []
            },
            "Программы": {
                "extensions": [".exe", ".msi", ".iso", ".bat", ".cmd", ".ps1", ".sh"],
                "keywords": []
            },
            "Торренты": {
                "extensions": [".torrent"],
                "keywords": []
            },
            "Разное": {"extensions": [], "keywords": []}
        }
    }
    
    _DEFAULT_CONFIG_EN = {
        "theme": "light",
        "safety": {"check_file_size": True, "max_size_mb": 500},
        "categories": {
            "Images": {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"],
                "keywords": []
            },
            "Videos": {
                "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
                "keywords": []
            },
            "Audio": {
                "extensions": [".mp3", ".wav", ".ogg", ".m4a", ".mid", ".midi"],
                "keywords": []
            },
            "Documents": {
                "extensions": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
                "keywords": []
            },
            "Archives": {
                "extensions": [".zip", ".rar", ".7z", ".tar", ".gz"],
                "keywords": []
            },
            "Programs": {
                "extensions": [".exe", ".msi", ".iso", ".bat", ".cmd", ".ps1", ".sh"],
                "keywords": []
            },
            "Torrents": {
                "extensions": [".torrent"],
                "keywords": []
            },
            "Miscellaneous": {"extensions": [], "keywords": []}
        }
    }

    def _get_default_config_by_system_lang(self):
        """Шаблон конфига RU или EN — тот же выбор, что и у интерфейса (get_effective_app_lang)."""
        lang = get_effective_app_lang()
        return copy.deepcopy(self._DEFAULT_CONFIG_RU if lang == "ru" else self._DEFAULT_CONFIG_EN)
    
    # Инициализация менеджера: определяем путь и сразу загружаем конфиг в память.
    def __init__(self, config_path: str = None):
        """Создаёт экземпляр менеджера и подготавливает in-memory конфигурацию."""
        if config_path is None:
            base = get_base_dir()
            self.config_path = os.path.join(base, "data", "config.json")
        else:
            self.config_path = config_path
        self.config = self._load_or_create_config()

    # Внутренний метод: пытаемся загрузить конфиг, при отсутствии создаём дефолтный.
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Загружает или создаёт конфиг."""
        try:
            if not os.path.exists(self.config_path):
                return self._create_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                return self._merge_with_defaults(loaded_config)
                
        except (json.JSONDecodeError, PermissionError, OSError) as e:
            logger.error(f"КРИТИЧЕСКИЙ СБОЙ при работе с конфигом: {e}")
            default_config = self._get_default_config_by_system_lang()
            if os.path.exists(self.config_path):
                try:
                    broken = f"{self.config_path}.broken.{int(time.time())}"
                    shutil.move(self.config_path, broken)
                    logger.warning(f"Повреждённый конфиг сохранён как {broken}, записан новый по умолчанию.")
                except OSError as move_err:
                    logger.error(f"Не удалось переименовать повреждённый конфиг: {move_err}")
            try:
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
            except OSError as werr:
                logger.error(f"Не удалось записать новый конфиг: {werr}")
            return default_config

    # Внутренний метод: первичное создание config.json на диске.
    def _create_default_config(self):
        """Создаёт новый конфиг из шаблона, учитывая язык системы."""
        logger.warning(f"Конфиг не найден по пути {self.config_path}. Создаю новый.")
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        default_config = self._get_default_config_by_system_lang()
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config

    # Внутренний метод: мягко дополняем старые/неполные конфиги новыми ключами.
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Дополняет загруженный конфиг значениями по умолчанию."""
        # Получаем эталонный конфиг для текущей системной локали
        default_config = self._get_default_config_by_system_lang()
        
        # Устанавливаем тему, если её нет
        loaded_config.setdefault("theme", default_config["theme"])
        
        # Дополняем настройки безопасности
        loaded_config.setdefault("safety", default_config["safety"])
        for key in default_config["safety"]:
            loaded_config["safety"].setdefault(key, default_config["safety"][key])

        # Убеждаемся, что секция категорий существует и содержит служебную категорию.
        loaded_config.setdefault("categories", copy.deepcopy(default_config["categories"]))
        
        # Определяем имя служебной категории из дефолтного конфига
        misc_category_name = list(default_config["categories"].keys())[-1]  # "Разное" или "Miscellaneous"
        loaded_config["categories"].setdefault(misc_category_name, {"extensions": [], "keywords": []})
        
        logger.info(f"Конфиг успешно загружен из {self.config_path}")
        return loaded_config

    # Публичный метод: сохраняем текущее состояние self.config в файл.
    def save_config(self) -> bool:
        """Сохраняет текущую конфигурацию в файл."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Конфиг успешно сохранён в {self.config_path}")
            return True
        except (PermissionError, OSError) as e:
            logger.error(f"Не удалось сохранить конфиг: {e}")
            return False

    # --- Публичный API категорий ---
    def get_categories(self) -> Dict[str, Any]:
        """Возвращает словарь категорий."""
        return self.config.get("categories", {})

    def update_categories(self, new_categories: Dict[str, Any]) -> None:
        """Полностью обновляет словарь категорий."""
        self.config["categories"] = new_categories
        self.save_config()
    
    # --- Публичный API темы ---
    def get_theme(self) -> str:
        """Возвращает текущую тему."""
        return self.config.get("theme", "light")
    
    def set_theme(self, theme: str) -> None:
        """Устанавливает тему (light или dark)."""
        if theme in ["light", "dark"]:
            self.config["theme"] = theme
            self.save_config()
        else:
            logger.warning(f"Некорректная тема: {theme}")

    # --- Публичный API настроек безопасности ---
    def get_safety_settings(self) -> Dict[str, Any]:
        """Возвращает настройки безопасности."""
        return self.config.get("safety", {"check_file_size": True, "max_size_mb": 500})
    
    def set_safety_settings(self, check_file_size: bool, max_size_mb: int) -> None:
        """Обновляет настройки безопасности."""
        # Корректируем размер
        if max_size_mb < 1:
            max_size_mb = 1
            logger.warning(f"Некорректный размер: установлено 1 МБ")
        elif max_size_mb > 102400:
            max_size_mb = 102400
            logger.warning(f"Слишком большой размер: установлено 102400 МБ")
        
        self.config["safety"] = {"check_file_size": check_file_size, "max_size_mb": max_size_mb}
        self.save_config()
        logger.info(f"Настройки безопасности обновлены")

# Глобальный экземпляр для доступа из других модулей
config_agent = ConfigHandler()
