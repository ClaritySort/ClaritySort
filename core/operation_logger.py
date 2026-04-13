# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""
Модуль журналирования операций.
Собирает детальную статистику сортировки и сохраняет JSON-логи в `data/logs`.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

from core.utils import get_base_dir

logger = logging.getLogger(__name__)

class OperationLogger:
    """Класс для ведения журнала операций."""
    
    # Создаём новую лог-сессию и базовую структуру будущего JSON-отчёта.
    def __init__(self, logs_dir: str = None, max_logs: int = 50):
        """Инициализирует лог-сессию и структуру накопления статистики."""
        if logs_dir is None:
            base = get_base_dir()
            logs_dir = os.path.join(base, "data", "logs")
        self.logs_dir = logs_dir
        self.max_logs = max_logs
        os.makedirs(self.logs_dir, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(self.logs_dir, f"sort_{self.session_id}.json")
        
        self.session_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "operations": [],
            "skipped_folders": [],
            "skipped_files": [],
            "large_files": [],
            "stats": {
                "total_folders": 0,
                "skipped_folders": 0,
                "total_files": 0,
                "processed_files": 0,
                "skipped_files": 0,
                "errors": 0,
                "by_category": {}
            }
        }
    
    # Записываем контекст запуска сортировки (источник/цель/настройки безопасности).
    def set_basic_info(self, source_dir: str, target_dir: str, safety_settings: Dict[str, Any]) -> None:
        """Устанавливает основную информацию о сессии."""
        self.session_data.update({
            "source_dir": source_dir,
            "target_dir": target_dir,
            "safety_settings": safety_settings
        })
    
    # Логируем итог обработки конкретного файла (успех/ошибка) + обновляем счётчики.
    def log_operation(self, src: str, dst: str, size_bytes: int, 
                     category: str, status: str = "success", 
                     error: str = None) -> None:
        """Записывает операцию перемещения файла."""
        operation = {
            "timestamp": datetime.now().isoformat(),
            "src": src,
            "dst": dst,
            "size_bytes": size_bytes,
            "size_gb": size_bytes / (1024**3),
            "category": category,
            "status": status
        }
        
        if error:
            operation["error"] = error
        
        self.session_data["operations"].append(operation)
        
        if status == "success":
            self.session_data["stats"]["processed_files"] += 1
            # Обновляем статистику по категориям
            if category not in self.session_data["stats"]["by_category"]:
                self.session_data["stats"]["by_category"][category] = 0
            self.session_data["stats"]["by_category"][category] += 1
        else:
            self.session_data["stats"]["errors"] += 1
    
    # Фиксируем папку, которую не сортируем (по текущей логике сортировка только по корню).
    def log_skipped_folder(self, folder_path: str) -> None:
        """Записывает пропущенную папку."""
        self.session_data["skipped_folders"].append({
            "path": folder_path,
            "timestamp": datetime.now().isoformat()
        })
        self.session_data["stats"]["skipped_folders"] += 1
    
    # Фиксируем файл, который не удалось обработать, и причину пропуска.
    def log_skipped_file(self, file_path: str, reason: str, 
                         size_bytes: int = 0, category: str = None) -> None:
        """Записывает пропущенный файл."""
        skipped_file = {
            "path": file_path,
            "reason": reason,
            "size_bytes": size_bytes,
            "size_gb": size_bytes / (1024**3) if size_bytes > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        if category:
            skipped_file["category"] = category
            
        self.session_data["skipped_files"].append(skipped_file)
        self.session_data["stats"]["skipped_files"] += 1
    
    # Отдельный список для "больших" файлов: удобно для итогового отчёта пользователю.
    def log_large_file(self, file_path: str, size_bytes: int, 
                       action: str, category: str = None) -> None:
        """Записывает большой файл и действие с ним."""
        large_file = {
            "path": file_path,
            "size_bytes": size_bytes,
            "size_gb": size_bytes / (1024**3),
            "action": action,  # "sorted" или "skipped"
            "timestamp": datetime.now().isoformat()
        }
        
        if category:
            large_file["category"] = category
            
        self.session_data["large_files"].append(large_file)
    
    # Сохраняем выбор пользователя в диалоге обработки больших файлов.
    def set_user_choice(self, choice: str) -> None:
        """Устанавливает выбор пользователя."""
        self.session_data["user_choice"] = choice
    
    # Технические сеттеры итоговых счётчиков.
    def set_total_folders(self, count: int) -> None:
        """Устанавливает общее количество папок."""
        self.session_data["stats"]["total_folders"] = count
    
    def set_total_files(self, count: int) -> None:
        """Устанавливает общее количество файлов."""
        self.session_data["stats"]["total_files"] = count
    
    # Пишем финальный JSON-отчёт на диск и запускаем очистку старых логов.
    def save(self) -> bool:
        """Сохраняет журнал в файл."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
            
            # Очищаем старые логи если превышен лимит
            self._cleanup_old_logs()
            
            logger.info(f"Журнал операции сохранен: {self.log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Не удалось сохранить журнал: {e}")
            return False
    
    # Поддерживаем лимит числа логов в папке, чтобы она не росла бесконечно.
    def _cleanup_old_logs(self) -> None:
        """Удаляет старые логи, оставляя только max_logs последних."""
        try:
            # Получаем все файлы логов
            logs = []
            for filename in os.listdir(self.logs_dir):
                if filename.startswith("sort_") and filename.endswith(".json"):
                    filepath = os.path.join(self.logs_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    logs.append((mtime, filepath))
            
            # Сортируем по времени (новые вперед)
            logs.sort(reverse=True)
            
            # Удаляем старые
            for i in range(self.max_logs, len(logs)):
                try:
                    os.remove(logs[i][1])
                    logger.info(f"Удален старый лог: {os.path.basename(logs[i][1])}")
                except Exception as e:
                    logger.warning(
                        f"Не удалось удалить старый лог {os.path.basename(logs[i][1])}: {e}"
                    )
                    
        except Exception as e:
            logger.error(f"Ошибка при очистке логов: {e}")
    
    # Утилита для возврата пути к текущему лог-файлу.
    def get_log_path(self) -> str:
        """Возвращает путь к файлу журнала."""
        return self.log_file
    
    # Утилита для краткой сводки, которую показывает интерфейс после сортировки.
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по операции."""
        return {
            "session_id": self.session_id,
            "total_folders": self.session_data["stats"]["total_folders"],
            "skipped_folders": self.session_data["stats"]["skipped_folders"],
            "total_files": self.session_data["stats"]["total_files"],
            "processed": self.session_data["stats"]["processed_files"],
            "skipped": self.session_data["stats"]["skipped_files"],
            "errors": self.session_data["stats"]["errors"],
            "by_category": self.session_data["stats"]["by_category"],
            "large_files_count": len(self.session_data["large_files"]),
            "log_file": self.log_file
        }
