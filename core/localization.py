# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""
Модуль локализации интерфейса.
Поддерживает русский и английский языки с автоопределением по системной локали.
Содержит словари переводов и функцию `_()` для получения строк по ключу.
"""
import locale
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_effective_app_lang() -> str:
    """
    Язык интерфейса и шаблона категорий по умолчанию: ru / en.
    Сначала переменная окружения CLARITY_LANG, иначе системная локаль (ru → ru), иначе en.
    """
    forced = os.environ.get("CLARITY_LANG", "").strip().lower()
    if forced in ("ru", "en"):
        return forced
    try:
        loc = locale.getdefaultlocale()[0]
        if loc and loc.startswith("ru"):
            return "ru"
    except Exception:
        pass
    return "en"


class LocaleManager:
    """
    Синглтон для управления локализацией.
    Использование:
        from core.localization import _
        label = tk.Label(text=_("settings"))
    """
    _instance: Optional['LocaleManager'] = None
    _current_lang: str = "en"
    _translations: Dict[str, Dict[str, str]] = {}

    # Синглтон: гарантируем один общий экземпляр локализации на всё приложение.
    def __new__(cls):
        """Возвращает единственный экземпляр менеджера локализации."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_translations()
            cls._instance._detect_system_lang()
        return cls._instance

    # Загружаем словари переводов в память при первом создании менеджера.
    def _load_translations(self):
        """Загружает словари переводов."""
        self._translations = {
            "ru": {
                # Главное окно
                "title_main": "Clarity",
                "dir_frame_title": " СЕКТОРА ",
                "source_label": "Сектор зачистки:",
                "target_label": "Сектор результатов:",
                "browse_btn": "Обзор...",
                "create_in_place": "Создать папку «Отсортированное» внутри сектора-источника",
                "check_size": "Проверять большие файлы (>{size} МБ)",
                "settings_btn": "⚙️ Настройки",
                "sort_btn": "⚡ Запустить",
                "cancel_btn": "⛔ Остановить",
                "progress_ready": "Готов к работе",
                "log_frame_title": " Журнал ",

                # Сообщения (для журнала и диалогов) – НЕ ТРОГАЕМ
                "system_activated": "СИСТЕМА: Приложение запущено.",
                "loaded_categories": "Загружено категорий: {count}",
                "theme_loaded": "Тема интерфейса: {theme}",
                "size_check_status": "Проверка больших файлов: {status} (>{size} МБ)",
                "source_set": "Сектор-источник: {path}",
                "target_set": "Сектор-назначение: {path}",
                "in_place_on": "Сортировка внутри сектора",
                "in_place_off": "Сортировка во внешний сектор",
                "size_check_on": "активирована",
                "size_check_off": "отключена",
                "theme_changed": "Тема изменена на {theme}",
                "sorting_in_progress": "Сортировка уже выполняется",
                "select_source_error": "Ошибка",
                "select_source_msg": "Сначала выберите сектор-источник!",
                "folder_not_exist": "Папка не существует:\n{path}",
                "select_target_error": "Ошибка",
                "select_target_msg": "Выберите сектор-назначение или активируйте 'Создать внутри'!",
                "target_not_exist": "Папка назначения не существует:\n{path}\n\nСоздать?",
                "create_folder_error": "Не удалось создать папку:\n{error}",
                "scanning_large": "Поиск файлов >{size} МБ...",
                "large_files_found": "Обнаружены большие файлы",
                "large_files_header": "Найдено {count} файлов размером >{size} МБ\nОбщий размер: {total:.2f} ГБ\nВсего файлов в папке: {total_files} | Папок обнаружено: {skipped}",
                "sort_all": "Сортировать ВСЕ файлы (включая большие)",
                "skip_large": "Пропустить большие файлы (оставить на месте)",
                "continue_btn": "ПРОДОЛЖИТЬ",
                "cancel_btn_dialog": "ОТМЕНА",
                "cancelled_by_user": "Сортировка отменена",
                "will_skip_large": "Пропущено больших файлов: {count}",
                "will_sort_all": "Обработано больших файлов: {count}",
                "no_large_files": "Файлов >{size} МБ не найдено",
                "found_files_info": "Файлов: {files}, папок: {folders}",
                "processed_progress": "Обработано {current} из {total}",
                "finishing": "Завершение...",
                "operation_success": "Успех",
                "operation_completed": "Операция завершена!",
                "summary_total": "Всего файлов в папке: {total}",
                "summary_processed": "Успешно обработано: {processed}",
                "summary_folders": "Папок обнаружено (не сортируются): {folders}",
                "summary_errors": "Ошибок: {errors}",
                "summary_large_skipped": "Больших файлов пропущено: {count}",
                "summary_large_processed": "Больших файлов обработано: {count}",
                "categories_summary": "Распределение по категориям:",
                "operation_finished": "Сортировка завершена",
                "large_files_log_skipped": "Пропущено больших файлов: {count}",
                "large_files_log_processed": "Обработано больших файлов: {count}",
                "folders_log": "Папок пропущено: {count}",
                "stop_requested": "Остановка...",
                "finishing_operation": "СИСТЕМА: Завершение операции...",
                "no_active_operation": "Нет активной сортировки",
                "error_in_thread": "ОШИБКА в потоке: {error}\nТип ошибки: {type}",
                "error_occurred": "Ошибка",
                "operation_error": "Операция завершилась с ошибкой:\n{error}",
                "log_cleared": "Журнал очищен.",
                "log_copy_menu": "Копировать",
                "log_select_all_menu": "Выделить все",
                "clear_log_menu": "Очистить журнал",
                "same_source_target": "Сектор-источник и сектор назначения совпадают. Укажите другую папку или включите «Создать папку внутри источника».",
                "prescan_cancelled": "Проверка больших файлов прервана.",
                "sorted_output_folder_name": "Отсортированное",
                "size_unit_gib": " ГБ",
                "log_sort_files_queue": "К обработке файлов: {count}",
                "log_sort_file_line": "{name} → {category}",
                "sort_stopped_title": "Сортировка остановлена",
                "sort_stopped_body": "Операция прервана по запросу. Уже перемещённые файлы остаются в папках категорий; необработанные — в исходной папке.\n\nОбработано: {processed} из {total}.",
                "sort_stopped_log": "СИСТЕМА: остановка пользователем. Обработано {processed} из {total} файлов.",
                "cancel_sort_consequence": "Уже перемещённые файлы не возвращаются; остальные остаются на месте до следующего запуска.",
                "closing_with_sort": "Операция выполняется",
                "closing_message": "Сортировка все еще выполняется!\n\nВыберите действие:\n• Да - остановить и закрыть\n• Нет - продолжить работу в окне\n• Отмена - вернуться в программу",
                "tray_minimized": "СИСТЕМА: Программа свернута в трей. Сортировка продолжается.",

                # Окно настроек
                "settings_title": "Настройки",
                "categories_frame": " Категории ",
                "new_category_label": "Новая категория:",
                "add_btn": "Добавить",
                "rename_btn": "Переименовать",
                "delete_btn": "Удалить",
                "category_settings": " Параметры категории ",
                "select_category": "Категория не выбрана",
                "category_selected": "Категория: {name}",
                "keywords_frame": " Ключевые слова ",
                "new_keyword": "Новое слово:",
                "add_keyword_btn": "Добавить",
                "delete_keyword_btn": "Удалить",
                "extensions_frame": " Расширения ",
                "new_extension": "Новое расширение:",
                "add_extension_btn": "Добавить",
                "delete_extension_btn": "Удалить",
                "safety_frame": " Безопасность ",
                "check_size_cb": "Проверять размер файлов перед сортировкой",
                "max_size_label": "Порог размера:",
                "mb_unit": "МБ",
                "safety_note": "Файлы больше указанного порога будут показаны перед сортировкой.",
                "save_close_btn": "💾 Сохранить и закрыть",
                "cancel_btn_settings": "Отмена",

                # Диалоги и ошибки настроек
                "warning": "Внимание",
                "enter_category_name": "Введите название категории!",
                "name_too_long": "Название слишком длинное (макс. 50 символов)!",
                "forbidden_char": "Название содержит запрещённый символ: '{char}'",
                "category_exists": "Категория '{name}' уже существует!",
                "select_to_delete": "Выберите категорию для удаления!",
                "cannot_delete_misc": "Служебную категорию нельзя удалить!",
                "confirm_delete": "Подтверждение удаления",
                "confirm_delete_msg": "Удалить категорию '{name}'?\n\nВсе её правила будут удалены.\nНовые файлы пойдут в '{misc}'.",
                "success": "Успех",
                "category_deleted": "Категория успешно удалена!",
                "select_to_rename": "Выберите категорию для переименования!",
                "cannot_rename_misc": "Служебную категорию нельзя переименовать!",
                "rename_title": "Переименование",
                "rename_prompt": "Введите новое название для '{name}':",
                "enter_keyword": "Введите ключевое слово!",
                "keyword_too_long": "Ключевое слово слишком длинное!",
                "keyword_exists": "Это ключевое слово уже есть в списке!",
                "select_keyword": "Выберите ключевое слово для удаления!",
                "enter_extension": "Введите расширение файла!",
                "extension_too_long": "Расширение слишком длинное!",
                "extension_invalid": "Некорректный формат расширения!",
                "extension_exists": "Это расширение уже есть в списке!",
                "select_extension": "Выберите расширение для удаления!",
                "min_size_error": "Порог должен быть не менее 1 МБ!",
                "max_size_error": "Порог не должен превышать 102400 МБ (100 ГБ)!",
                "saved": "Сохранено",
                "settings_saved": "Настройки успешно сохранены!",

                # Темы
                "theme_light": "Светлая",
                "theme_dark": "Тёмная",

                # Прочее
                "misc_category": "Разное",
                "auto_target_text": "Автоматически создаётся в папке «Отсортированное»",
                "default_target_text": "Укажите папку для результатов...",
                "default_source_text": "Укажите папку для сортировки...",
            },
            "en": {
                # Main window
                "title_main": "Clarity",
                "dir_frame_title": " SECTORS ",
                "source_label": "Source sector:",
                "target_label": "Destination sector:",
                "browse_btn": "Browse...",
                "create_in_place": "Create 'Sorted' folder inside source sector",
                "check_size": "Check large files (>{size} MB)",
                "settings_btn": "⚙️ Settings",
                "sort_btn": "⚡ Start",
                "cancel_btn": "⛔ Stop",
                "progress_ready": "Ready to work",
                "log_frame_title": " Log ",

                # Messages
                "system_activated": "SYSTEM: Application started.",
                "loaded_categories": "Loaded categories: {count}",
                "theme_loaded": "Interface theme: {theme}",
                "size_check_status": "Large files check: {status} (>{size} MB)",
                "source_set": "Source sector: {path}",
                "target_set": "Destination sector: {path}",
                "in_place_on": "Sorting inside sector",
                "in_place_off": "Sorting to external sector",
                "size_check_on": "enabled",
                "size_check_off": "disabled",
                "theme_changed": "Theme changed to {theme}",
                "sorting_in_progress": "Sorting already in progress",
                "select_source_error": "Error",
                "select_source_msg": "Please select a source sector first!",
                "folder_not_exist": "Folder does not exist:\n{path}",
                "select_target_error": "Error",
                "select_target_msg": "Select a destination sector or enable 'Create inside'!",
                "target_not_exist": "Destination folder does not exist:\n{path}\n\nCreate it?",
                "create_folder_error": "Could not create folder:\n{error}",
                "scanning_large": "Scanning for files >{size} MB...",
                "large_files_found": "Large Files Detected",
                "large_files_header": "Found {count} files larger than {size} MB\nTotal size: {total:.2f} GB\nTotal files in folder: {total_files} | Folders found: {skipped}",
                "sort_all": "Sort ALL files (including large ones)",
                "skip_large": "Skip large files (leave in place)",
                "continue_btn": "CONTINUE",
                "cancel_btn_dialog": "CANCEL",
                "cancelled_by_user": "Sorting cancelled",
                "will_skip_large": "Skipped large files: {count}",
                "will_sort_all": "Processed large files: {count}",
                "no_large_files": "No files >{size} MB found",
                "found_files_info": "Files: {files}, folders: {folders}",
                "processed_progress": "Processed {current} of {total}",
                "finishing": "Finishing...",
                "operation_success": "Success",
                "operation_completed": "Operation completed!",
                "summary_total": "Total files in folder: {total}",
                "summary_processed": "Successfully processed: {processed}",
                "summary_folders": "Folders detected (not sorted): {folders}",
                "summary_errors": "Errors: {errors}",
                "summary_large_skipped": "Large files skipped: {count}",
                "summary_large_processed": "Large files processed: {count}",
                "categories_summary": "Distribution by category:",
                "operation_finished": "Sorting completed",
                "large_files_log_skipped": "Large files skipped: {count}",
                "large_files_log_processed": "Large files processed: {count}",
                "folders_log": "Folders skipped: {count}",
                "stop_requested": "Stopping...",
                "finishing_operation": "SYSTEM: Finishing operation...",
                "no_active_operation": "No active sorting",
                "error_in_thread": "ERROR in thread: {error}\nError type: {type}",
                "error_occurred": "Error",
                "operation_error": "Operation finished with error:\n{error}",
                "log_cleared": "Log cleared.",
                "log_copy_menu": "Copy",
                "log_select_all_menu": "Select all",
                "clear_log_menu": "Clear log",
                "same_source_target": "Source and destination folders are the same. Choose another folder or enable «Create folder inside source».",
                "prescan_cancelled": "Large file scan cancelled.",
                "sorted_output_folder_name": "Sorted",
                "size_unit_gib": " GB",
                "log_sort_files_queue": "Files to process: {count}",
                "log_sort_file_line": "{name} → {category}",
                "sort_stopped_title": "Sorting stopped",
                "sort_stopped_body": "The operation was cancelled. Files already moved stay in category folders; the rest remain in the source folder.\n\nProcessed: {processed} of {total}.",
                "sort_stopped_log": "SYSTEM: stopped by user. Processed {processed} of {total} files.",
                "cancel_sort_consequence": "Already moved files are not reverted; others stay in place until the next run.",
                "closing_with_sort": "Operation in progress",
                "closing_message": "Sorting is still in progress!\n\nChoose an action:\n• Yes - stop and close\n• No - keep working in this window\n• Cancel - return to program",
                "tray_minimized": "SYSTEM: Program minimized to tray. Sorting continues.",

                # Settings window
                "settings_title": "Settings",
                "categories_frame": " Categories ",
                "new_category_label": "New category:",
                "add_btn": "Add",
                "rename_btn": "Rename",
                "delete_btn": "Delete",
                "category_settings": " Category Settings ",
                "select_category": "No category selected",
                "category_selected": "Category: {name}",
                "keywords_frame": " Keywords ",
                "new_keyword": "New word:",
                "add_keyword_btn": "Add",
                "delete_keyword_btn": "Delete",
                "extensions_frame": " Extensions ",
                "new_extension": "New extension:",
                "add_extension_btn": "Add",
                "delete_extension_btn": "Delete",
                "safety_frame": " Safety ",
                "check_size_cb": "Check file size before sorting",
                "max_size_label": "Size threshold:",
                "mb_unit": "MB",
                "safety_note": "Files larger than the specified threshold will be shown before sorting.",
                "save_close_btn": "💾 Save and close",
                "cancel_btn_settings": "Cancel",

                # Dialogs and errors
                "warning": "Warning",
                "enter_category_name": "Enter category name!",
                "name_too_long": "Name too long (max 50 characters)!",
                "forbidden_char": "Name contains forbidden character: '{char}'",
                "category_exists": "Category '{name}' already exists!",
                "select_to_delete": "Select a category to delete!",
                "cannot_delete_misc": "The service category cannot be deleted!",
                "confirm_delete": "Confirm deletion",
                "confirm_delete_msg": "Delete category '{name}'?\n\nAll its rules will be removed.\nNew files will go to '{misc}'.",
                "success": "Success",
                "category_deleted": "Category successfully deleted!",
                "select_to_rename": "Select a category to rename!",
                "cannot_rename_misc": "The service category cannot be renamed!",
                "rename_title": "Rename",
                "rename_prompt": "Enter new name for '{name}':",
                "enter_keyword": "Enter a keyword!",
                "keyword_too_long": "Keyword too long!",
                "keyword_exists": "This keyword is already in the list!",
                "select_keyword": "Select a keyword to delete!",
                "enter_extension": "Enter a file extension!",
                "extension_too_long": "Extension too long!",
                "extension_invalid": "Invalid extension format!",
                "extension_exists": "This extension is already in the list!",
                "select_extension": "Select an extension to delete!",
                "min_size_error": "Threshold must be at least 1 MB!",
                "max_size_error": "Threshold cannot exceed 102400 MB (100 GB)!",
                "saved": "Saved",
                "settings_saved": "Settings saved successfully!",

                # Themes
                "theme_light": "Light",
                "theme_dark": "Dark",

                # Misc
                "misc_category": "Miscellaneous",
                "auto_target_text": "Automatically created in 'Sorted' folder",
                "default_target_text": "Select destination folder...",
                "default_source_text": "Select source sector...",
            }
        }

    # Автоматически подбираем язык по CLARITY_LANG или системной локали.
    def _detect_system_lang(self):
        """Определяет язык (ru/en), не русский и не английский системный → en."""
        self._current_lang = get_effective_app_lang()
        if self._current_lang == "ru":
            logger.info(f"Определён язык приложения: {self._current_lang}")
        else:
            logger.info(f"Detected application language: {self._current_lang}")

    # Основной метод получения перевода по ключу + подстановка параметров.
    def get(self, key: str, **kwargs) -> str:
        """
        Возвращает переведённую строку по ключу.
        Поддерживает форматирование с именованными аргументами.
        """
        trans = self._translations.get(self._current_lang, {}).get(key)
        if trans is None:
            trans = self._translations["en"].get(key, key)
        if kwargs:
            try:
                return trans.format(**kwargs)
            except KeyError:
                return trans
        return trans

    # Ручная установка языка (например, для отладки или фиксированного режима).
    def set_lang(self, lang_code: str) -> None:
        """Устанавливает язык (ru/en) и синхронизирует CLARITY_LANG с шаблоном конфига."""
        if lang_code in self._translations:
            self._current_lang = lang_code
            os.environ["CLARITY_LANG"] = lang_code
            logger.info(f"Language set to: {lang_code}")

    @property
    def current_lang(self) -> str:
        """Текущий активный язык интерфейса."""
        return self._current_lang


# Глобальная функция для удобства
def _(key: str, **kwargs) -> str:
    """Короткий доступ к переводу строки по ключу."""
    return LocaleManager().get(key, **kwargs)
