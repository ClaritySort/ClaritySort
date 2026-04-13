# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""
Главное окно GUI.
Отвечает за выбор папок, запуск/остановку сортировки, отображение прогресса
и журнал действий пользователя.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import logging
import threading
import os
import shutil
from datetime import datetime
from core.config_manager import config_agent
from core.sorter_engine import ChaosSorter
from core.localization import _
from ui.theme_styles import get_palette, get_ui_font

class MainWindow:
    """Главное окно приложения."""

    def __init__(self, master):
        """Инициализирует состояние главного окна и создаёт все элементы интерфейса."""
        self.master = master
        
        # Загружаем тему из конфига
        self.current_theme = config_agent.get_theme()
        
        # Загружаем настройки безопасности
        safety_settings = config_agent.get_safety_settings()
        
        # ИНИЦИАЛИЗИРУЕМ ЦВЕТА ПЕРВЫМ ДЕЛОМ
        self._setup_theme_colors()
        
        # НЕ СКРЫВАЕМ ОКНО! Настраиваем сразу
        master.title(_("title_main"))
        master.minsize(600, 500)
        
        # Устанавливаем цвет рамки окна
        master.configure(bg=self.colors['bg'], highlightbackground=self.colors['bg'])
        # Иконка задаётся в main.py (resource_path), здесь не дублируем

        # Переменные состояния
        self.source_dir = tk.StringVar(value=_("default_source_text"))
        self.target_dir = tk.StringVar(value=_("default_target_text"))
        self.create_in_place = tk.BooleanVar(value=True)
        
        # ИСПРАВЛЕНО: Загружаем настройки безопасности
        self.check_size = tk.BooleanVar(value=safety_settings["check_file_size"])
        self.current_max_size = safety_settings["max_size_mb"]  # Храним текущее значение
        
        # НОВЫЕ АТРИБУТЫ для управления операцией
        self.current_sorter = None
        self.sorting_thread = None
        self.is_sorting = False
        self.progress_var = tk.DoubleVar()
        
        # НОВОЕ: для хранения больших файлов
        self.large_files = []
        self.skip_large_files = False

        self._prescanning = False
        self._prescan_cancel = threading.Event()
        self._prescan_thread = None
        self._pending_sort_source = None
        self._pending_sort_target = None
        
        # Настройка логгера для вывода в GUI
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Настраиваем стили
        self._setup_styles()
        self._init_fonts()
        
        # Инициализация интерфейса
        self._create_widgets()
        self._load_config()
        
        # Важно: сразу применить состояние галочки!
        self._toggle_target_entry()
        
        # Устанавливаем протокол закрытия окна
        master.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Тестовый вывод в лог
        self.log("=" * 60)
        self.log(_("system_activated"))
        self.log(_("loaded_categories", count=len(self.categories)))
        theme_name = _("theme_light") if self.current_theme == "light" else _("theme_dark")
        self.log(_("theme_loaded", theme=theme_name))
        size_status = _("size_check_on") if self.check_size.get() else _("size_check_off")
        self.log(_("size_check_status", status=size_status, size=self.current_max_size))
        self.log("=" * 60)
        
        # Поднимаем окно на передний план и фокусируем
        master.lift()
        master.focus_force()
        
        # Создаём окно настроек один раз и скрываем
        from ui.settings_window import SettingsWindow
        self.settings_window = SettingsWindow(self.master, self)
        self.settings_window.withdraw()

    def center_window(self, window):
        """Центрирует окно на экране."""
        # Обновляем информацию о размерах
        window.update_idletasks()
        
        # Получаем текущие размеры окна
        width = window.winfo_width()
        height = window.winfo_height()
        
        # Если размеры не определились (окно еще не отображено), используем дефолтные
        if width <= 1 or height <= 1:
            # Получаем заданную геометрию
            geometry = window.geometry()
            if geometry and 'x' in geometry:
                # Извлекаем размеры из строки геометрии (формат: "800x600+0+0")
                size_part = geometry.split('+')[0]
                if 'x' in size_part:
                    width, height = map(int, size_part.split('x'))
                else:
                    width, height = 800, 600
            else:
                width, height = 800, 600
        
        # Получаем размеры экрана
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Вычисляем координаты для центрирования
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Устанавливаем новую геометрию
        window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Обновляем для применения изменений
        window.update_idletasks()

    def _setup_theme_colors(self):
        """Устанавливает цвета в зависимости от темы (единая палитра в theme_styles)."""
        self.light_colors = get_palette("light")
        self.dark_colors = get_palette("dark")
        self.colors = self.light_colors if self.current_theme == "light" else self.dark_colors
        self.master.configure(bg=self.colors['bg'])

    def _init_fonts(self):
        """Переносимые шрифты Tk (TkDefaultFont / TkFixedFont)."""
        m = self.master
        self.font_title = get_ui_font(m, "default", 18, bold=True)
        self.font_subtitle = get_ui_font(m, "default", 12)
        self.font_ui_bold = get_ui_font(m, "default", 10, bold=True)
        self.font_small = get_ui_font(m, "default", 9)
        self.font_small_bold = get_ui_font(m, "default", 9, bold=True)
        self.font_tiny = get_ui_font(m, "default", 8)
        self.font_log = get_ui_font(m, "fixed", 9)
        self.font_log_small = get_ui_font(m, "fixed", 8)
        self.font_dialog_bold = get_ui_font(m, "default", 10, bold=True)
        self.font_dialog_normal = get_ui_font(m, "default", 9)

    def _on_closing(self):
        """Обработчик закрытия окна."""
        if self.is_sorting or self._prescanning:
            response = messagebox.askyesnocancel(
                _("closing_with_sort"),
                _("closing_message")
            )
        
            if response is None:
                return
            elif response:
                self._cancel_operation()
                self._wait_then_destroy()
            else:
                return
        else:
            self.master.destroy()

    def _wait_then_destroy(self):
        """Закрывает окно после фактической остановки потоков (без фиксированной задержки 1 с)."""
        if self._prescanning or (self._prescan_thread is not None and self._prescan_thread.is_alive()):
            self.master.after(50, self._wait_then_destroy)
            return
        if self.is_sorting:
            self.master.after(50, self._wait_then_destroy)
            return
        if self.sorting_thread is not None and self.sorting_thread.is_alive():
            self.sorting_thread.join(timeout=0.2)
            self.master.after(50, self._wait_then_destroy)
            return
        self.master.destroy()

    def _setup_styles(self):
        """Настраивает ttk-стили прогрессбара и скроллбаров для светлой/тёмной темы."""
        style = ttk.Style()
    
        # ОБНОВЛЕНО: Сбрасываем старые стили
        style.theme_use('default')  # Используем стандартную тему
    
        # Стиль для светлой темы
        style.configure(
            "Light.Horizontal.TProgressbar",
            thickness=20,
            troughcolor='#E0E0E0',  # Светло-серый для светлой темы
            background='#FF6B00',   # Оранжевый для заполнения
            bordercolor='#FFFFFF',
            lightcolor='#FF6B00',
            darkcolor='#FF6B00'
        )
    
        # Стиль для темной темы
        style.configure(
            "Dark.Horizontal.TProgressbar",
            thickness=20,
            troughcolor='#2A2A2A',  # Темно-серый для темной темы
            background='#FF6B00',   # Оранжевый для заполнения
            bordercolor='#1A1A1A',
            lightcolor='#FF6B00',
            darkcolor='#FF6B00'
        )
    
        # Стиль для неактивного состояния
        style.map(
            'Dark.Horizontal.TProgressbar',
            troughcolor=[('disabled', '#2A2A2A'), ('!disabled', '#2A2A2A')],
            background=[('disabled', '#2A2A2A'), ('!disabled', '#FF6B00')]
        )
    
        style.map(
            'Light.Horizontal.TProgressbar',
            troughcolor=[('disabled', '#E0E0E0'), ('!disabled', '#E0E0E0')],
            background=[('disabled', '#E0E0E0'), ('!disabled', '#FF6B00')]
        )
    
        # Стили для скроллбаров
        style.configure(
            "Dark.Vertical.TScrollbar",
            background='#404040',
            troughcolor='#2A2A2A',
            arrowcolor='#E0E0E0',
            bordercolor='#1A1A1A'
        )
    
        style.configure(
            "Light.Vertical.TScrollbar",
            background='#C0C0C0',
            troughcolor='#E0E0E0',
            arrowcolor='#000000',
            bordercolor='#FFFFFF'
        )
        
        style.map('Dark.Vertical.TScrollbar',
          background=[('disabled', '#404040'), ('active', '#505050'), ('pressed', '#606060')],
          troughcolor=[('disabled', '#2A2A2A')])

        style.map('Light.Vertical.TScrollbar',
          background=[('disabled', '#C0C0C0'), ('active', '#D0D0D0'), ('pressed', '#A0A0A0')],
          troughcolor=[('disabled', '#E0E0E0')])

    def _apply_theme(self):
        """Применяет текущую тему ко всем виджетам."""
        # Обновляем цвета
        self.colors = self.light_colors if self.current_theme == "light" else self.dark_colors

        # Обновляем главное окно
        self.master.configure(bg=self.colors['bg'])

        # Устанавливаем цвет заголовка окна через стиль
        style = ttk.Style()
        if self.current_theme == "dark":
            # Для темной темы - темный фон
            self.master.configure(bg=self.colors['bg'])
            # Попробуем изменить цвет бордюра окна
            self.master.configure(highlightbackground=self.colors['bg'])
        else:
            # Для светлой темы - светлый фон
            self.master.configure(bg=self.colors['bg'])
            self.master.configure(highlightbackground=self.colors['bg'])

        # Обновляем стили
        self._setup_styles()

        if hasattr(self, 'progress_bar'):
            self.progress_bar.configure(
                style="Dark.Horizontal.TProgressbar"
                if self.current_theme == "dark"
                else "Light.Horizontal.TProgressbar"
            )

        # Переключаем стиль scrollbar
        if hasattr(self, 'scrollbar'):
            self.scrollbar.configure(
                style="Dark.Vertical.TScrollbar"
                if self.current_theme == "dark"
                else "Light.Vertical.TScrollbar"
            )

        # Обновляем все виджеты
        self._update_widget_colors()

        # Обязательно обновляем состояние поля цели, но БЕЗ логирования
        self._toggle_target_entry(silent=True, preserve_target=True)
        self._notify_settings_theme()

    def _notify_settings_theme(self):
        """Синхронизирует тему окна настроек с главным (на случай снятия модальности в будущем)."""
        sw = getattr(self, "settings_window", None)
        if not sw:
            return
        try:
            sw.apply_theme(self.current_theme)
        except tk.TclError:
            pass

    def _update_widget_colors(self):
        """Обновляет цвета всех виджетов."""
        # Обновляем заголовок (один лейбл Clarity)
        if hasattr(self, 'header_label'):
            self.header_label.configure(bg=self.colors['bg'], fg=self.colors['accent'])
        
        # Обновляем фоновую полосу заголовка
        if hasattr(self, 'header_frame'):
            self.header_frame.configure(bg=self.colors['bg'])
            
        # Обновляем filler
        if hasattr(self, 'filler'):
            self.filler.configure(bg=self.colors['bg'])
        
        # Обновляем кнопку темы
        if hasattr(self, 'theme_btn'):
            theme_icon = "🌙" if self.current_theme == "light" else "💡"
            self.theme_btn.configure(
                text=theme_icon,
                bg=self.colors['button_bg'],
                fg=self.colors['button_fg']
            )
        
        # Обновляем фрейм папок и его содержимое
        if hasattr(self, 'dir_frame'):
            self.dir_frame.configure(bg=self.colors['bg'], fg=self.colors['fg'])
            
        # Обновляем все дочерние виджеты dir_frame
        if hasattr(self, 'dir_frame'):
            for child in self.dir_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=self.colors['bg'], fg=self.colors['fg'])
                elif isinstance(child, tk.Entry):
                    child.configure(bg=self.colors['entry_bg'], fg=self.colors['entry_fg'])
                elif isinstance(child, tk.Button):
                    child.configure(bg=self.colors['button_bg'], fg=self.colors['button_fg'])
                elif isinstance(child, tk.Checkbutton):
                    # Обновляем цвета чекбокса
                    check_color = self.colors['check_active']
                    child.configure(
                        bg=self.colors['bg'], 
                        fg=self.colors['fg'],
                        selectcolor=check_color,
                        activebackground=self.colors['bg']
                    )
        
        # Обновляем кнопки управления
        if hasattr(self, 'control_frame'):
            self.control_frame.configure(bg=self.colors['bg'])
            
        if hasattr(self, 'settings_btn_frame'):
            self.settings_btn_frame.configure(bg=self.colors['bg'])
            
        if hasattr(self, 'sort_btn_frame'):
            self.sort_btn_frame.configure(bg=self.colors['bg'])
            
        if hasattr(self, 'cancel_btn_frame'):
            self.cancel_btn_frame.configure(bg=self.colors['bg'])
        
        # Обновляем кнопки
        if hasattr(self, 'settings_btn'):
            self.settings_btn.configure(bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        
        if hasattr(self, 'sort_btn'):
            self.sort_btn.configure(bg=self.colors['accent'], fg='white')
        
        # ИСПРАВЛЕНО: Увеличиваем ширину кнопки ОСТАНОВИТЬ
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(
                bg=self.colors['button_bg'], 
                fg=self.colors['button_fg'],
                width=14  # Увеличили ширину
            )
        
        # Обновляем прогресс-бар
        if hasattr(self, 'progress_frame'):
            self.progress_frame.configure(bg=self.colors['bg'])
        
        if hasattr(self, 'progress_label'):
            self.progress_label.configure(bg=self.colors['bg'], fg=self.colors['fg'])
        
        # Обновляем лог-панель
        if hasattr(self, 'log_frame'):
            self.log_frame.configure(bg=self.colors['bg'], fg=self.colors['fg'])
        
        if hasattr(self, 'log_text'):
            self.log_text.configure(
                bg=self.colors['log_bg'],
                fg=self.colors['log_fg'],
                insertbackground=self.colors['fg']
            )
        
        # Обновляем кнопку обзора целевой папки
        if hasattr(self, 'target_browse_btn'):
            # Проверяем, включена ли галочка
            if self.create_in_place.get():
                # Неактивное состояние
                self.target_browse_btn.config(
                    bg=self.colors['button_disabled_bg'], 
                    fg=self.colors['button_disabled_fg'], 
                    state="disabled"
                )
            else:
                # Активное состояние
                self.target_browse_btn.config(
                    bg=self.colors['button_bg'], 
                    fg=self.colors['button_fg'],
                    state="normal"
                )

        # Обновляем поле ввода целевой папки
        if hasattr(self, 'target_entry'):
            if self.create_in_place.get():
                # В неактивном состоянии
                self.target_entry.config(
                    state="disabled",
                    bg=self.colors['entry_disabled_bg'],
                    fg=self.colors['entry_disabled_fg'],
                    disabledbackground=self.colors['entry_disabled_bg'],
                    disabledforeground=self.colors['entry_disabled_fg']
                )
            else:
                # В активном состоянии
                self.target_entry.config(
                    state="normal",
                    bg=self.colors['entry_bg'], 
                    fg=self.colors['entry_fg'],
                    disabledbackground=self.colors['entry_bg'],
                    disabledforeground=self.colors['entry_fg']
                )
        
        # Обновляем чекбокс проверки размера
        if hasattr(self, 'check_size_check'):
            check_color = self.colors['check_active']
            self.check_size_check.configure(
                bg=self.colors['bg'], 
                fg=self.colors['fg'],
                selectcolor=check_color,
                activebackground=self.colors['bg']
            )
        
        ## Обновляем статусную строку
        #if hasattr(self, 'status_bar'):
        #    self.status_bar.configure(bg=self.colors['bg'], fg=self.colors['fg'])

    def _setup_logging(self):
        """Настройка вывода логов в текстовое поле."""
        class TextHandler(logging.Handler):
            """Лог-хендлер для перенаправления сообщений стандартного логгера в виджет Text."""

            def __init__(self, text_widget):
                """Создаёт хендлер и задаёт формат строк в GUI-журнале."""
                super().__init__()
                self.text_widget = text_widget
                self.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

            def emit(self, record):
                """Добавляет новую запись логгера в конец текстового виджета."""
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)

        handler = TextHandler(None)  # Будет установлен после создания виджета
        self.log_handler = handler
        self.logger.addHandler(handler)

    def _create_widgets(self):
        """Создание и размещение всех элементов интерфейса."""
        # Верхняя панель: Заголовок с цветным акцентом
        self.header_frame = tk.Frame(self.master, bg=self.colors['bg'])
        self.header_frame.pack(pady=15, padx=10, fill="x")
        
        # Один лейбл с названием Clarity оранжевым цветом
        self.header_label = tk.Label(
            self.header_frame,
            text="Clarity",
            font=self.font_title,
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        self.header_label.pack(side="left")
        
        # Заполнитель чтобы отодвинуть кнопку темы вправо
        self.filler = tk.Frame(self.header_frame, bg=self.colors['bg'])
        self.filler.pack(side="left", expand=True, fill="x")
        
        # Переключатель темы справа
        theme_frame = tk.Frame(self.header_frame, bg=self.colors['bg'])
        theme_frame.pack(side="right", padx=(20, 0))

        # Простая кнопка переключения темы
        self.theme_btn = tk.Button(
            theme_frame,
            text="💡" if self.current_theme == "light" else "🌙",
            width=3,
            height=1,
            command=self._toggle_theme,
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg'],
            font=self.font_subtitle,
            relief="flat",
            borderwidth=1,
            padx=0,
            pady=0
        )
        self.theme_btn.pack()

        # Фрейм выбора папок
        self.dir_frame = tk.LabelFrame(self.master, 
                                  text=_("dir_frame_title"),
                                  font=self.font_small_bold,
                                  bg=self.colors['bg'],
                                  fg=self.colors['fg'],
                                  padx=10,
                                  pady=10)
        self.dir_frame.pack(fill="x", padx=10, pady=5)

        # Исходная папка
        tk.Label(self.dir_frame, 
                text=_("source_label"),
                bg=self.colors['bg'],
                fg=self.colors['fg']).grid(row=0, column=0, sticky="w", pady=2)
        
        source_entry = tk.Entry(self.dir_frame, 
                               textvariable=self.source_dir, 
                               width=50,
                               bg=self.colors['entry_bg'],
                               fg=self.colors['entry_fg'],
                               insertbackground=self.colors['fg'])
        source_entry.grid(row=0, column=1, padx=5)
        
        tk.Button(self.dir_frame, 
                 text=_("browse_btn"), 
                 command=self._browse_source,
                 bg=self.colors['button_bg'],
                 fg=self.colors['button_fg']).grid(row=0, column=2)

        # Целевая папка
        tk.Label(self.dir_frame, 
                text=_("target_label"),
                bg=self.colors['bg'],
                fg=self.colors['fg']).grid(row=1, column=0, sticky="w", pady=2)
        
        self.target_entry = tk.Entry(self.dir_frame, 
                                    textvariable=self.target_dir, 
                                    width=50, 
                                    state="normal",
                                    bg=self.colors['entry_bg'],
                                    fg=self.colors['entry_fg'],
                                    insertbackground=self.colors['fg'])
        self.target_entry.grid(row=1, column=1, padx=5)
        
        self.target_browse_btn = tk.Button(self.dir_frame, 
             text=_("browse_btn"), 
             command=self._browse_target,
             bg=self.colors['button_bg'],
             fg=self.colors['button_fg'])
        self.target_browse_btn.grid(row=1, column=2)

        # Чекбокс для создания папки внутри источника
        check_color = self.colors['check_active']
        
        self.in_place_check = tk.Checkbutton(
            self.dir_frame,
            text=_("create_in_place"),
            variable=self.create_in_place,
            command=self._toggle_target_entry,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=check_color,
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg']
        )
        self.in_place_check.grid(row=2, column=0, columnspan=3, pady=5, sticky="w")

        # НОВЫЙ ЧЕКБОКС для проверки размера файлов
        self.check_size_check = tk.Checkbutton(
            self.dir_frame,
            text=_("check_size", size=self.current_max_size),
            variable=self.check_size,
            command=self._toggle_check_size,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=check_color,
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg']
        )
        self.check_size_check.grid(row=3, column=0, columnspan=3, pady=5, sticky="w")

        # Фрейм управления
        self.control_frame = tk.Frame(self.master, bg=self.colors['bg'])
        self.control_frame.pack(fill="x", padx=10, pady=10)
        
        # Создаем отдельные фреймы для каждой кнопки
        self.settings_btn_frame = tk.Frame(self.control_frame, bg=self.colors['bg'])
        self.settings_btn_frame.pack(side="left", padx=5)
        
        self.sort_btn_frame = tk.Frame(self.control_frame, bg=self.colors['bg'])
        self.sort_btn_frame.pack(side="left", padx=5)
        
        self.cancel_btn_frame = tk.Frame(self.control_frame, bg=self.colors['bg'])
        self.cancel_btn_frame.pack(side="right", padx=5)
        
        # Кнопки в отдельных фреймах
        self.settings_btn = tk.Button(self.settings_btn_frame, 
                 text=_("settings_btn"),
                 command=self._open_settings, 
                 width=15,
                 bg=self.colors['button_bg'],
                 fg=self.colors['button_fg'])
        self.settings_btn.pack()
        
        self.sort_btn = tk.Button(self.sort_btn_frame, 
                 text=_("sort_btn"), 
                 command=self._run_sort, 
                 width=12,
                 bg=self.colors['accent'],
                 fg='white',
                 font=self.font_ui_bold)
        self.sort_btn.pack()
        
        # ИСПРАВЛЕНО: Увеличили ширину кнопки ОСТАНОВИТЬ
        self.cancel_btn = tk.Button(self.cancel_btn_frame, 
                 text=_("cancel_btn"),
                 command=self._cancel_operation, 
                 width=14,
                 bg=self.colors['button_bg'],
                 fg=self.colors['button_fg'])
        self.cancel_btn.pack()
        
        # ПРОГРЕСС-БАР (перед лог-панелью)
        self.progress_frame = tk.Frame(self.master, bg=self.colors['bg'])
        self.progress_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=100,
            mode='determinate',
            style="Dark.Horizontal.TProgressbar" if self.current_theme == "dark" else "Light.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", expand=True)
        
        self.progress_label = tk.Label(
            self.progress_frame, 
            text=_("progress_ready"),
            font=self.font_tiny,
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        self.progress_label.pack()

        # Лог-панель
        self.log_frame = tk.LabelFrame(self.master, 
                                 text=_("log_frame_title"),
                                 font=self.font_small_bold,
                                 bg=self.colors['bg'],
                                 fg=self.colors['fg'],
                                 padx=10,
                                 pady=10)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Текстовое поле
        self.log_text = tk.Text(
            self.log_frame, 
            height=15, 
            wrap="word", 
            bg=self.colors['log_bg'],          # Фон из текущей темы
            fg=self.colors['log_fg'],          # Текст из текущей темы
            insertbackground=self.colors['fg'], # Цвет курсора
            font=self.font_log
        )
        self.scrollbar = ttk.Scrollbar(
            self.log_frame,
            orient="vertical",
            command=self.log_text.yview,
            style="Dark.Vertical.TScrollbar" if self.current_theme == "dark" else "Light.Vertical.TScrollbar"
        )
        self.log_text.configure(yscrollcommand=self.scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Привязка логгера к текстовому виджету
        self.log_handler.text_widget = self.log_text

        # ========== ДОБАВЛЕНО: НАСТРОЙКА КОПИРОВАНИЯ ТЕКСТА ==========
        # Разрешаем выделение и копирование текста
        self.log_text.configure(exportselection=True)
        
        # Привязываем Ctrl+C для копирования
        self.log_text.bind("<Control-KeyPress>", self._on_key_press)
        
        # Создаем контекстное меню для копирования
        self._create_log_context_menu()
        
        # Привязываем контекстное меню к правой кнопке мыши
        self.log_text.bind("<Button-3>", self._show_log_context_menu)
        # ========== КОНЕЦ ДОБАВЛЕННОГО КОДА ==========

        ## Строка состояния
        #self.status_var = tk.StringVar(value=_("status_ready"))
        #self.status_bar = tk.Label(self.master, 
        #                     textvariable=self.status_var, 
        #                     relief="sunken", 
        #                     anchor="w",
        #                    bg=self.colors['bg'],
        #                    fg=self.colors['fg'])
        #self.status_bar.pack(side="bottom", fill="x")
        
        # Настройка весов для главного окна
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=0)  # Заголовок - не растягивается
        self.master.rowconfigure(1, weight=0)  # Фрейм папок - не растягивается
        self.master.rowconfigure(2, weight=0)  # Фрейм управления - не растягивается
        self.master.rowconfigure(3, weight=0)  # Прогресс-бар - не растягивается
        self.master.rowconfigure(4, weight=1)  # Лог-панель - растягивается

    def _on_key_press(self, event):
        """Обрабатывает Ctrl+C независимо от раскладки клавиатуры."""
        # Проверяем, что зажат Ctrl (маска 0x4) и нажата клавиша с кодом 67 (латинская 'c' / русская 'с')
        if (event.state & 0x4) and event.keycode == 67:
            self._copy_log_text()
            return "break"

    def _center_window_on_parent(self, child_window, parent_window):
        """Центрирует дочернее окно относительно родительского."""
        # Ждем, пока окно обновится
        child_window.update_idletasks()
        
        # Получаем размеры дочернего окна
        child_width = child_window.winfo_width()
        child_height = child_window.winfo_height()
        
        # Если размеры не определились (окно еще не отображено), используем дефолтные
        if child_width <= 1 or child_height <= 1:
            # Получаем заданную геометрию
            geometry = child_window.geometry()
            if geometry and 'x' in geometry:
                # Извлекаем размеры из строки геометрии (формат: "800x600+0+0")
                size_part = geometry.split('+')[0]
                if 'x' in size_part:
                    child_width, child_height = map(int, size_part.split('x'))
                else:
                    child_width, child_height = 700, 500  # Размеры по умолчанию для окна настроек
            else:
                child_width, child_height = 700, 500
        
        # Получаем позицию и размеры родительского окна
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        # Вычисляем координаты для центрирования
        x = parent_x + (parent_width - child_width) // 2
        y = parent_y + (parent_height - child_height) // 2
        
        # Устанавливаем позицию окна
        child_window.geometry(f"+{x}+{y}")

    def _toggle_theme(self):
        """Переключает тему между светлой и темной."""
        if self.current_theme == "light":
            self.current_theme = "dark"
            theme_icon = "🌙"
        else:
            self.current_theme = "light"
            theme_icon = "💡"
        
        # Сохраняем тему в конфиг
        config_agent.set_theme(self.current_theme)
        
        # Применяем тему
        self._apply_theme()
        
        # ОБНОВЛЯЕМ КНОПКУ ТЕМЫ СРАЗУ
        self.theme_btn.configure(text=theme_icon)
        
        theme_name = _("theme_dark") if self.current_theme == "dark" else _("theme_light")
        self.log(_("theme_changed", theme=theme_name))

    def _load_config(self):
        """Загружает категории из конфига."""
        self.categories = config_agent.get_categories()

    def _update_check_size_text(self):
        """Обновляет текст чекбокса проверки размера файлов."""
        safety_settings = config_agent.get_safety_settings()
        max_size = safety_settings.get("max_size_mb", 500)
        self.current_max_size = max_size  # Обновляем текущее значение
        self.check_size_check.config(text=_("check_size", size=max_size))
        self.check_size.set(safety_settings["check_file_size"])

    def _update_safety_settings_from_config(self):
        """Обновляет настройки безопасности из конфига."""
        safety_settings = config_agent.get_safety_settings()
    
        # Обновляем переменные
        self.check_size.set(safety_settings["check_file_size"])
        self.current_max_size = safety_settings["max_size_mb"]
    
        # Обновляем текст чекбокса
        self.check_size_check.config(text=_("check_size", size=self.current_max_size))
    
        # Логируем полным сообщением
        size_status = _("size_check_on") if self.check_size.get() else _("size_check_off")
        self.log(_("size_check_status", status=size_status, size=self.current_max_size))

    # --- Обработчики событий ---
    def _browse_source(self):
        """Открывает диалог выбора исходной папки и записывает выбор в интерфейс."""
        dir_path = filedialog.askdirectory(title=_("source_label").rstrip(':'))
        if dir_path:
            self.source_dir.set(dir_path)
            self.log(_("source_set", path=dir_path))

    def _browse_target(self):
        """Открывает диалог выбора целевой папки и записывает выбор в интерфейс."""
        dir_path = filedialog.askdirectory(title=_("target_label").rstrip(':'))
        if dir_path:
            self.target_dir.set(dir_path)
            self.log(_("target_set", path=dir_path))

    def _toggle_target_entry(self, silent=False, preserve_target=False):
        """Включает/выключает поле целевой папки в зависимости от галочки."""
        if self.create_in_place.get():
            disabled_bg = self.colors['entry_disabled_bg']
            disabled_fg = self.colors['entry_disabled_fg']
            self.target_entry.config(
                state="disabled",
                disabledbackground=disabled_bg,
                disabledforeground=disabled_fg,
                bg=disabled_bg,
                fg=disabled_fg
            )
            self.target_browse_btn.config(
                state="disabled",
                bg=self.colors['button_disabled_bg'],
                fg=self.colors['button_disabled_fg']
            )
            if not preserve_target:
                self.target_dir.set(_("auto_target_text"))
            if not silent:
                self.log(_("in_place_on"))
        else:
            self.target_entry.config(
                state="normal",
                bg=self.colors['entry_bg'],
                fg=self.colors['entry_fg'],
                disabledbackground=self.colors['entry_bg'],
                disabledforeground=self.colors['entry_fg']
            )
            self.target_browse_btn.config(
                state="normal",
                bg=self.colors['button_bg'],
                fg=self.colors['button_fg']
            )
            if not preserve_target:
                self.target_dir.set(_("default_target_text"))
            if not silent:
                self.log(_("in_place_off"))

    def _toggle_check_size(self):
        """Включает/выключает проверку размера файлов."""
        # Обновляем настройки в конфиге с текущим значением размера
        safety_settings = config_agent.get_safety_settings()
        config_agent.set_safety_settings(
            check_file_size=self.check_size.get(),
            max_size_mb=safety_settings["max_size_mb"]
        )
        
        # Обновляем текст чекбокса
        self._update_check_size_text()
        
        size_status = _("size_check_on") if self.check_size.get() else _("size_check_off")
        self.log(_("size_check_status", status=size_status, size=self.current_max_size))

    def _open_settings(self):
        """Открывает окно настройки категорий."""
        try:
            # Синхронизируем тему с главным окном
            self.settings_window.apply_theme(self.current_theme)
            # Обновляем категории из конфига (на случай изменений вне окна)
            self.settings_window.categories = config_agent.get_categories()
            self.settings_window._populate_categories_list()
            # Сбрасываем выбор категории
            self.settings_window.selected_category = None
            self.settings_window.category_name_label.config(text=_("select_category"))
            self.settings_window.keywords_listbox.delete(0, tk.END)
            self.settings_window.extensions_listbox.delete(0, tk.END)

            # Показываем окно
            self.settings_window._fade_in()
            self.settings_window.lift()
            self.settings_window.focus_set()
            self.settings_window.grab_set()
        except Exception as e:
            self.log(f"ОШИБКА: Не удалось открыть настройки: {e}", "ERROR")
            messagebox.showerror("Ошибка", f"Не удалось открыть настройки:\n{str(e)}")

    # --- Проверка размера файлов и сортировка ---

    @staticmethod
    def _paths_equivalent(a, b):
        """Сравнение путей с учётом регистра и нормализации (Windows/Linux)."""
        try:
            return os.path.normcase(os.path.normpath(os.path.abspath(a))) == os.path.normcase(
                os.path.normpath(os.path.abspath(b)))
        except OSError:
            return False

    def _prescan_worker(self, directory, threshold_mb, cancel_event):
        """Фоновое сканирование корня папки (не блокирует GUI)."""
        large_files = []
        total_files = 0
        skipped_folders = 0
        try:
            items = os.listdir(directory)
            for item in items:
                if cancel_event.is_set():
                    self.master.after(0, self._on_prescan_complete, ("cancelled",))
                    return
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    skipped_folders += 1
                    continue
                if os.path.isfile(item_path):
                    total_files += 1
                    try:
                        size = os.path.getsize(item_path)
                        size_mb = size / (1024 * 1024)
                        if size_mb > threshold_mb:
                            size_gb = size / (1024 ** 3)
                            large_files.append({
                                "path": item_path,
                                "size_bytes": size,
                                "size_gb": size_gb,
                                "name": os.path.basename(item_path),
                            })
                    except (OSError, PermissionError):
                        continue
            self.master.after(
                0, self._on_prescan_complete,
                ("ok", large_files, total_files, skipped_folders),
            )
        except Exception as e:
            self.master.after(0, self._on_prescan_complete, ("error", str(e)))

    def _on_prescan_complete(self, payload):
        """Завершение предварительного сканирования (главный поток)."""
        self._prescanning = False
        self._prescan_thread = None
        try:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
        except tk.TclError:
            pass

        def _prescan_ui_idle():
            try:
                self.sort_btn.config(state="normal")
                self.settings_btn.config(state="normal")
            except tk.TclError:
                pass

        if not payload:
            _prescan_ui_idle()
            return
        kind = payload[0]
        if kind == "cancelled":
            self.progress_label.config(text=_("progress_ready"))
            self.log(_("prescan_cancelled"), "WARNING")
            _prescan_ui_idle()
            return
        if kind == "error":
            self.progress_label.config(text=_("error_occurred"))
            self.log(f"ОШИБКА при сканировании: {payload[1]}", "ERROR")
            _prescan_ui_idle()
            return

        _prescan_status, large_files, total_files, skipped_folders = payload
        self.progress_label.config(
            text=_("found_files_info", files=total_files, folders=skipped_folders)
        )

        source = self._pending_sort_source
        target = self._pending_sort_target
        threshold_mb = config_agent.get_safety_settings()["max_size_mb"]

        self.large_files = []
        self.skip_large_files = False

        if large_files:
            self.large_files = large_files
            choice = self._show_large_files_dialog(
                large_files, threshold_mb, total_files, skipped_folders
            )
            if choice is None:
                self.log(_("cancelled_by_user"))
                self.progress_label.config(text=_("progress_ready"))
                _prescan_ui_idle()
                return
            if choice == 0:
                self.skip_large_files = True
                self.log(_("will_skip_large", count=len(large_files)))
            else:
                self.skip_large_files = False
                self.log(_("will_sort_all", count=len(large_files)))
        else:
            self.log(_("no_large_files", size=threshold_mb))
            self.log(_("found_files_info", files=total_files, folders=skipped_folders))

        self._launch_sort_thread(source, target)

    def _launch_sort_thread(self, source, target):
        """Запускает поток сортировки после проверок и диалогов."""
        self.is_sorting = True
        self._update_ui_for_sorting(True)
        self.sorting_thread = threading.Thread(
            target=self._run_sorting_thread,
            args=(source, target),
            daemon=True,
        )
        self.sorting_thread.start()

    def _show_large_files_dialog(self, large_files, threshold_mb, total_files, skipped_folders):
        """Показывает диалог с большими файлами и возвращает выбор пользователя."""
        if not large_files:
            return True  # Сортировать все
        
        # Создаем диалоговое окно
        dialog = tk.Toplevel(self.master)
        dialog.title(_("large_files_found"))
        dialog.geometry("650x500")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        if hasattr(self.master, 'icon_path') and self.master.icon_path:
            try:
                dialog.iconbitmap(self.master.icon_path)
            except Exception:
                pass
        
        # Центрируем диалог
        self._center_window_on_parent(dialog, self.master)
        
        # Заголовок
        total_size_gb = sum(f['size_gb'] for f in large_files)
        header_text = _("large_files_header", 
                        count=len(large_files), size=threshold_mb,
                        total=total_size_gb, total_files=total_files, skipped=skipped_folders)
        
        header = tk.Label(
            dialog,
            text=header_text,
            font=self.font_dialog_bold,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            pady=10,
            justify="center"
        )
        header.pack()
        
        # Список файлов
        list_frame = tk.LabelFrame(dialog, text=_("large_files_found"), 
                                  bg=self.colors['bg'], fg=self.colors['fg'],
                                  font=self.font_dialog_normal, padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Текст с прокруткой
        text_widget = scrolledtext.ScrolledText(
            list_frame,
            height=10,
            font=self.font_log_small,
            bg=self.colors['listbox_bg'],
            fg=self.colors['listbox_fg'],
            wrap=tk.WORD
        )
        text_widget.pack(fill="both", expand=True)
        
        # Заполняем список
        for i, file_info in enumerate(large_files, 1):
            filename = file_info['name']
            size_text = f"{file_info['size_gb']:.2f}{_('size_unit_gib')}"
            text_widget.insert(tk.END, f"{i:3}. {filename:<50} - {size_text:>10}\n")
        
        text_widget.configure(state='disabled')
        
        # Радиокнопки выбора
        choice_var = tk.IntVar(value=1)  # 1 = сортировать все, 0 = пропустить большие
        
        choice_frame = tk.Frame(dialog, bg=self.colors['bg'])
        choice_frame.pack(pady=10)
        
        tk.Radiobutton(
            choice_frame,
            text=_("sort_all"),
            variable=choice_var,
            value=1,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['radio_active'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg']
        ).pack(anchor="w", padx=20, pady=(0, 5))
        
        tk.Radiobutton(
            choice_frame,
            text=_("skip_large"),
            variable=choice_var,
            value=0,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['radio_active'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg']
        ).pack(anchor="w", padx=20)
        
        # Кнопки
        buttons_frame = tk.Frame(dialog, bg=self.colors['bg'])
        buttons_frame.pack(pady=10)
        
        result = {'choice': None}
        
        def on_ok():
            # Пользователь подтвердил выбор режима обработки больших файлов.
            result['choice'] = choice_var.get()
            dialog.destroy()
        
        def on_cancel():
            # Пользователь отменил диалог и прервал запуск сортировки.
            result['choice'] = None
            dialog.destroy()
        
        tk.Button(
            buttons_frame,
            text=_("continue_btn"),
            command=on_ok,
            bg='#FF6B00',
            fg='white',
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            buttons_frame,
            text=_("cancel_btn_dialog"),
            command=on_cancel,
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg'],
            width=12
        ).pack(side="left", padx=5)
        
        # Ждем закрытия диалога
        dialog.wait_window(dialog)
        
        return result['choice']

    # --- Рабочие методы сортировки ---
    def _run_sort(self):
        """Запуск процесса сортировки."""
        if self.is_sorting or self._prescanning:
            self.log(_("sorting_in_progress"), "WARNING")
            return
        
        # Получаем параметры
        source = self.source_dir.get()
        if not source or _("default_source_text") in source:
            messagebox.showerror(_("select_source_error"), _("select_source_msg"))
            return
        
        # Проверяем существование папки
        if not os.path.exists(source):
            messagebox.showerror(_("select_source_error"), _("folder_not_exist", path=source))
            return
        
        # Определяем целевую папку
        if self.create_in_place.get():
            target = source  # Создаст "Отсортированное" внутри
        else:
            target = self.target_dir.get()
            if not target or _("default_target_text") in target:
                messagebox.showerror(_("select_target_error"), _("select_target_msg"))
                return
            
            # Проверяем существование целевой папки
            if not os.path.exists(target):
                create = messagebox.askyesno(_("warning"), _("target_not_exist", path=target))
                if not create:
                    return
                try:
                    os.makedirs(target, exist_ok=True)
                except Exception as e:
                    messagebox.showerror(_("select_target_error"), _("create_folder_error", error=str(e)))
                    return

        if not self.create_in_place.get() and self._paths_equivalent(source, target):
            messagebox.showwarning(_("warning"), _("same_source_target"))
            return
        
        self.large_files = []
        self.skip_large_files = False
        self._pending_sort_source = source
        self._pending_sort_target = target

        if self.check_size.get():
            safety_settings = config_agent.get_safety_settings()
            threshold_mb = safety_settings["max_size_mb"]
            self.log(_("scanning_large", size=threshold_mb))
            self.progress_label.config(
                text=_("scanning_large", size=threshold_mb).split(":")[0] + "..."
            )
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self._prescanning = True
            self._prescan_cancel.clear()
            try:
                self.sort_btn.config(state="disabled")
                self.settings_btn.config(state="disabled")
            except tk.TclError:
                pass
            self._prescan_thread = threading.Thread(
                target=self._prescan_worker,
                args=(source, threshold_mb, self._prescan_cancel),
                daemon=True,
            )
            self._prescan_thread.start()
            return

        self._launch_sort_thread(source, target)
    
    def _run_sorting_thread(self, source, target):
        """Поток для выполнения сортировки."""
        try:
            # Создаем движок
            self.current_sorter = ChaosSorter(config_agent.config)
            
            # Определяем, нужно ли создавать подпапку "Отсортированное"
            create_sorted_subfolder = self.create_in_place.get()
            
            # Подготавливаем список больших файлов для пропуска
            large_files_set = set()
            if self.skip_large_files and self.large_files:
                large_files_set = {f['path'] for f in self.large_files}
            
            # Запускаем сортировку
            sorted_name = _("sorted_output_folder_name")
            stats = self.current_sorter.run_sorting(
                source_dir=source,
                target_dir=target,
                mode="move",
                log_callback=self._thread_safe_log,
                progress_callback=self._update_progress,
                create_sorted_subfolder=create_sorted_subfolder,
                check_size=self.check_size.get(),
                skip_large_files=self.skip_large_files,
                large_files_set=large_files_set,
                sorted_subfolder_name=sorted_name if create_sorted_subfolder else None,
            )
            
            # Завершение операции
            self.master.after(0, self._on_sorting_finished, stats)
            
        except Exception as e:
            error_msg = _("error_in_thread", error=str(e), type=type(e).__name__)
            self._thread_safe_log(error_msg, "ERROR")
            self.master.after(0, self._on_sorting_finished, {"error": error_msg})
    
    def _thread_safe_log(self, message, level="INFO"):
        """Безопасное логирование из другого потока."""
        self.master.after(0, self.log, message, level)
    
    def _update_progress(self, current, total):
        """Обновление прогресса из другого потока."""
        if total > 0:
            percent = (current / total) * 100
            self.master.after(0, self.progress_var.set, percent)
        
            # Текст без дублирования
            status_text = _("processed_progress", current=current, total=total)
            if percent >= 99:
                status_text = _("finishing")
        
            self.master.after(0, self.progress_label.config, {"text": status_text})
    
    def _update_ui_for_sorting(self, sorting):
        """Обновление интерфейса в зависимости от состояния."""
        state = "disabled" if sorting else "normal"
        
        # Блокируем/разблокируем элементы управления
        try:
            self.target_entry.config(state=state)
        except (AttributeError, tk.TclError):
            pass
        
        try:
            self.sort_btn.config(state=state)
        except (AttributeError, tk.TclError):
            pass

        self.settings_btn.config(state=state)
    
    def _on_sorting_finished(self, stats):
        """Действия по завершении сортировки."""
        self.is_sorting = False
        self.current_sorter = None
        self._update_ui_for_sorting(False)
        
        if "error" in stats:
            messagebox.showerror(_("error_occurred"), _("operation_error", error=stats['error']))
            self.log(_("operation_error", error=stats['error']), "ERROR")
        elif stats.get("stopped_by_user"):
            messagebox.showwarning(
                _("sort_stopped_title"),
                _("sort_stopped_body", processed=stats.get("processed", 0), total=stats.get("total_files", 0)),
            )
            self.log(
                _("sort_stopped_log", processed=stats.get("processed", 0), total=stats.get("total_files", 0)),
                "WARNING",
            )
            for cat, cnt in stats.get("by_category", {}).items():
                self.log(f"  {cat}: {cnt}")
            self.progress_var.set(0)
            self.progress_label.config(text=_("progress_ready"))
        else:
            # Более информативное сообщение
            categories_summary = "\n".join([f"  • {cat}: {cnt}" for cat, cnt in stats.get('by_category', {}).items()])
            
            # Добавляем информацию о больших файлах если есть
            large_files_info = ""
            if self.check_size.get() and self.large_files:
                if self.skip_large_files:
                    large_files_info = "\n" + _("summary_large_skipped", count=len(self.large_files))
                else:
                    large_files_info = "\n" + _("summary_large_processed", count=len(self.large_files))
            
            messagebox.showinfo(_("operation_success"), 
                _("operation_completed") + "\n\n" +
                _("summary_total", total=stats.get('total_files', 0)) + "\n" +
                _("summary_processed", processed=stats.get('processed', 0)) + "\n" +
                _("summary_folders", folders=stats.get('skipped_folders', 0)) + "\n" +
                _("summary_errors", errors=stats.get('errors', 0)) +
                large_files_info + "\n\n" +
                _("categories_summary") + "\n" + categories_summary)
            
            self.log("=" * 50)
            self.log(_("operation_finished"))
            for cat, cnt in stats.get('by_category', {}).items():
                self.log(f"  {cat}: {cnt}")
            
            if self.check_size.get() and self.large_files:
                if self.skip_large_files:
                    self.log(_("large_files_log_skipped", count=len(self.large_files)))
                else:
                    self.log(_("large_files_log_processed", count=len(self.large_files)))
            
            self.log(_("folders_log", count=stats.get('skipped_folders', 0)))
            self.log("=" * 50)

        if not stats.get("stopped_by_user"):
            self.progress_var.set(0)
            self.progress_label.config(text=_("progress_ready"))
        #self.status_var.set(_("status_ready"))
    
    def _cancel_operation(self):
        """Отмена текущей операции."""
        if self._prescanning:
            self._prescan_cancel.set()
            self.log(_("prescan_cancelled"), "WARNING")
            return
        if self.is_sorting and self.current_sorter:
            self.current_sorter.stop()
            self.log(_("stop_requested"), "WARNING")
            self.log(_("cancel_sort_consequence"), "WARNING")
        else:
            self.log(_("no_active_operation"), "INFO")

    # ========== ДОБАВЛЕННЫЕ МЕТОДЫ ДЛЯ КОПИРОВАНИЯ ТЕКСТА ==========
    
    def _create_log_context_menu(self):
        """Создает контекстное меню для лог-текста."""
        self.log_context_menu = tk.Menu(self.log_text, tearoff=0)
        self.log_context_menu.add_command(
            label=_("log_copy_menu"),
            command=self._copy_log_selection,
        )
        self.log_context_menu.add_separator()
        self.log_context_menu.add_command(
            label=_("log_select_all_menu"),
            command=self._select_all_log
        )
        self.log_context_menu.add_command(
            label=_("clear_log_menu"),
            command=self._clear_log
        )

    def _show_log_context_menu(self, event):
        """Показывает контекстное меню лог-текста."""
        try:
            self.log_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_context_menu.grab_release()

    def _copy_log_text(self, event=None):
        """Копирует выделенный текст из лога в буфер обмена."""
        try:
            # Проверяем, есть ли выделенный текст
            if not self.log_text.tag_ranges("sel"):
                return "break"  # ничего не выделено – выходим
            selected_text = self.log_text.get("sel.first", "sel.last")
            if not selected_text:
                return "break"
            # Копируем в системный буфер обмена
            self.master.clipboard_clear()
            self.master.clipboard_append(selected_text)
            return "break"
        except Exception:
            self.log("Не удалось скопировать текст из журнала", "WARNING")
        return "break"

    def _copy_log_selection(self):
        """Копирует выделенный текст по команде из меню."""
        self._copy_log_text()

    def _select_all_log(self):
        """Выделяет весь текст в логе."""
        self.log_text.tag_add("sel", "1.0", "end")
        self.log_text.focus_set()
        return "break"

    def _clear_log(self):
        """Очищает содержимое лог-текста."""
        self.log_text.delete(1.0, tk.END)
        self.log(_("log_cleared"), "INFO")

    # --- Утилиты ---
    def log(self, message: str, level: str = "INFO"):
        """Добавляет сообщение в лог."""
        self.logger.log(getattr(logging, level.upper()), message)
