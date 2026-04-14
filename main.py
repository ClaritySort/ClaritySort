# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT

"""
Точка входа приложения.
Отвечает за старт Tkinter, установку иконки окна и запуск главного GUI-модуля.
"""
import sys
import os
import logging
import traceback as tb
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Принудительный язык интерфейса и шаблона категорий: None = авто (ru по системе, иначе en),
# либо строка "ru" / "en". Должно задаваться до импорта ui (см. начало main()).
FORCE_APP_LANG = None  # например: "en"
# Либо задайте язык здесь (выполняется при загрузке main.py, до импорта core/ui):
# os.environ["CLARITY_LANG"] = "en"

APP_VERSION = "1.0.0"


def _configure_startup_logging():
    """Лог в файл (виден и при --windowed); при консольном запуске дублируем в stdout."""
    base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base, "data", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    handlers = [fh]
    if getattr(sys, "stdout", None) and sys.stdout.isatty():
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        handlers.append(sh)
    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


# Главная функция запуска приложения.
def main():
    """Инициализирует GUI и запускает главный цикл приложения."""
    # До импорта модулей, создающих config_agent (иначе шаблон категорий возьмёт старый язык).
    if FORCE_APP_LANG in ("ru", "en"):
        os.environ["CLARITY_LANG"] = FORCE_APP_LANG

    _configure_startup_logging()
    log = logging.getLogger("clarity")

    if sys.platform == "win32":
        try:
            # AppUserModelID нужен для корректной иконки и группировки окна в Windows.
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ClaritySort.FileSorter.1")
        except Exception:
            # Ошибка не критична для работы программы, просто продолжаем запуск.
            pass

    log.info("=" * 52)
    log.info("Clarity: запуск")
    log.info("Версия: %s", APP_VERSION)
    log.info("=" * 52)

    try:
        from core.paths import resource_path
        from ui.main_window import MainWindow
        import tkinter as tk

        root = tk.Tk()
        # Сначала скрываем корневое окно, чтобы показать уже полностью инициализированный UI.
        root.withdraw()

        # Установка иконки окна
        try:
            icon_path = resource_path("app_icon.ico")
            if os.path.isfile(icon_path):
                root.iconbitmap(icon_path)
                root.icon_path = icon_path  # сохраняем для доступа из дочерних окон
            else:
                log.warning("Файл иконки не найден: %s", icon_path)
        except Exception as e:
            log.warning("Не удалось установить иконку: %s", e)

        app = MainWindow(root)

        # Центрируем главное окно
        root.update_idletasks()
        w = root.winfo_reqwidth()
        h = root.winfo_reqheight()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        root.geometry(f'{w}x{h}+{x}+{y}')

        root.deiconify()
        root.lift()
        root.focus_force()
        root.mainloop()

        log.info("[СИСТЕМА] Приложение закрыто. Операция завершена.")

    except ImportError as e:
        # Выделяем ошибку импорта отдельно: чаще всего это проблема структуры проекта.
        err_msg = f"\n[КРИТИЧЕСКИЙ СБОЙ] Не удалось загрузить модуль: {e}"
        err_type = "Проверьте структуру директорий и зависимости."
    except Exception as e:
        # Общий fallback для всех остальных непредвиденных ошибок старта.
        err_msg = f"\n[НЕИЗВЕСТНАЯ ОШИБКА] Произошла ошибка: {e}"
        err_type = "Проверьте правильность работы программы."
    else:
        return

    logging.getLogger("clarity").error("%s", err_msg)
    logging.getLogger("clarity").error("Подробная информация об ошибке:")
    tb.print_exc()
    logging.getLogger("clarity").error("%s", err_type)
    input("Нажмите Enter для выхода...")
    sys.exit(1)

if __name__ == "__main__":
    main()
