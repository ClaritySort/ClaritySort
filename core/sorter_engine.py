# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""
Ядро сортировки файлов.
Определяет категорию файла по правилам и выполняет безопасное перемещение
с учётом ограничений по размеру и логированием результата.
"""
import os
import shutil
from collections import defaultdict
from typing import Dict, Any, Callable, Optional, Set
from core.operation_logger import OperationLogger
from core.localization import _


class ChaosSorter:
    """Движок сортировки: классифицирует файлы и выполняет их перемещение по категориям."""

    # Инициализируем движок сортировки и кэшируем правила из конфига.
    def __init__(self, config: Dict[str, Any]):
        """Подготавливает правила сортировки и служебные параметры сессии."""
        self.config = config
        self.categories = config.get("categories", {})
        self.safety_settings = config.get("safety", {})
        self.stop_requested = False
        self.current_operation = None

        # Предкомпилируем правила в быстрые структуры, чтобы не разбирать конфиг
        # заново для каждого файла при массовой сортировке.
        self._ext_map = {}
        self._keyword_map = defaultdict(list)

        for category, rules in self.categories.items():
            for ext in rules.get("extensions", []):
                self._ext_map[ext.lower()] = category
            for kw in rules.get("keywords", []):
                self._keyword_map[category].append(kw.lower())

        self._misc_category = self._resolve_misc_category()

    # Определяем имя fallback-категории с учётом текущей локализации конфигурации.
    def _resolve_misc_category(self) -> str:
        """Определяет служебную категорию для fallback-классификации."""
        if "Разное" in self.categories:
            return "Разное"
        if "Miscellaneous" in self.categories:
            return "Miscellaneous"
        return "Разное"

    # -------------------------------------------------

    # Категоризируем файл по имени: сначала keywords, затем extension, затем fallback.
    def _categorize_file(self, file_path: str) -> str:
        """Возвращает имя категории для файла на основе правил keywords/extensions."""
        filename = os.path.basename(file_path).lower()
        _, ext = os.path.splitext(filename)

        # Приоритет у ключевых слов: это позволяет "переопределить" категорию
        # конкретного файла даже при совпадающем расширении.
        for category, keywords in self._keyword_map.items():
            for kw in keywords:
                if kw in filename:
                    return category

        # Если по ключевым словам совпадений нет, используем карту расширений.
        if ext in self._ext_map:
            return self._ext_map[ext]

        return self._misc_category

    # -------------------------------------------------

    # Выполняем перемещение файла с защитой от коллизий и базовой пост-проверкой.
    def _safe_move_file(self, src: str, dst: str, logger: Optional[OperationLogger]):
        """Перемещает файл и возвращает результат в формате (ok, final_path, error_text)."""
        try:
            if not os.path.exists(src):
                return False, dst, "Файл не найден"

            size = os.path.getsize(src)

            if os.path.exists(dst):
                base, ext = os.path.splitext(dst)
                i = 1
                # Подбираем свободное имя, чтобы не перезаписывать существующий файл.
                while os.path.exists(f"{base} ({i}){ext}"):
                    i += 1
                dst = f"{base} ({i}){ext}"

            shutil.move(src, dst)

            # Базовая пост-проверка: файл должен существовать и иметь тот же размер.
            if os.path.exists(dst) and os.path.getsize(dst) == size:
                return True, dst, None

            return False, dst, "Ошибка проверки размера"

        except Exception as e:
            return False, dst, str(e)

    # -------------------------------------------------

    # Основной сценарий сортировки: проход по файлам, распределение по категориям, логирование.
    def run_sorting(
        self,
        source_dir: str,
        target_dir: str,
        mode: str = "move",
        log_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        create_sorted_subfolder: bool = True,
        check_size: bool = False,
        skip_large_files: bool = False,
        large_files_set: Optional[Set[str]] = None,
        sorted_subfolder_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Запускает сортировку и возвращает сводную статистику по результату операции."""

        self.stop_requested = False
        logger = OperationLogger()
        logger.set_basic_info(source_dir, target_dir, self.safety_settings)

        if create_sorted_subfolder:
            raw = (sorted_subfolder_name or _("sorted_output_folder_name")).strip()
            sub = os.path.basename(raw) or _("sorted_output_folder_name")
            target_dir = os.path.join(target_dir, sub)
            os.makedirs(target_dir, exist_ok=True)

        stats = {
            "total_files": 0,
            "processed": 0,
            "errors": 0,
            "skipped_folders": 0,
            "by_category": defaultdict(int),
            "large_files_processed": 0,
            "large_files_skipped": 0,
            "stopped_by_user": False,
        }

        threshold = self.safety_settings.get("max_size_mb", 500) * 1024 * 1024

        items = os.listdir(source_dir)
        files = []

        # По текущему ТЗ сортируем только корень исходной папки:
        # вложенные каталоги считаем пропущенными объектами.
        for item in items:
            path = os.path.join(source_dir, item)
            if os.path.isdir(path):
                stats["skipped_folders"] += 1
                logger.log_skipped_folder(path)
            else:
                files.append(path)

        stats["total_files"] = len(files)
        logger.set_total_files(stats["total_files"])
        logger.set_total_folders(stats["skipped_folders"])
        if log_callback:
            log_callback(_("log_sort_files_queue", count=stats["total_files"]))

        for i, file_path in enumerate(files, 1):
            if self.stop_requested:
                break

            try:
                size = os.path.getsize(file_path)
                # Режим skip_large_files использует список из pre-scan в UI,
                # чтобы пользователь явно решал судьбу больших файлов до старта.
                if check_size and skip_large_files and large_files_set and file_path in large_files_set:
                    logger.log_large_file(file_path, size, "skipped")
                    stats["large_files_skipped"] += 1
                    continue

                category = self._categorize_file(file_path)
                cat_dir = os.path.join(target_dir, category)
                os.makedirs(cat_dir, exist_ok=True)

                dst = os.path.join(cat_dir, os.path.basename(file_path))
                ok, final, err = self._safe_move_file(file_path, dst, logger)

                if ok:
                    stats["processed"] += 1
                    stats["by_category"][category] += 1
                    logger.log_operation(file_path, final, size, category, "success")
                    if check_size and size > threshold:
                        stats["large_files_processed"] += 1
                else:
                    stats["errors"] += 1
                    logger.log_skipped_file(file_path, "move_error", size, category)

                if log_callback:
                    log_callback(
                        _("log_sort_file_line", name=os.path.basename(file_path), category=category)
                    )

            except Exception:
                stats["errors"] += 1

            if progress_callback:
                progress_callback(i, stats["total_files"])

        stats["stopped_by_user"] = bool(self.stop_requested)
        stats["by_category"] = dict(stats["by_category"])
        logger.save()
        stats["log_file"] = logger.get_log_path()
        return stats

    # -------------------------------------------------

    # Публичный флаг остановки: вызывается из UI при нажатии кнопки "Остановить".
    def stop(self):
        """Запрашивает остановку текущего цикла сортировки."""
        self.stop_requested = True
