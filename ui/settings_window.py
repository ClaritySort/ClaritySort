# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT

"""
Окно настроек.
Отвечает за управление категориями, правилами сортировки
и параметрами безопасности.
"""
import tkinter as tk
import os
from tkinter import ttk, messagebox, simpledialog
from core.config_manager import config_agent
from core.localization import _
from ui.theme_styles import get_palette, get_ui_font


class SettingsWindow(tk.Toplevel):
    """Окно настройки категорий и правил."""

    def __init__(self, parent, main_window_ref):
        """Создаёт окно настроек и инициализирует элементы управления категориями/безопасностью."""
        super().__init__(parent)
        self.withdraw()  # Сразу скрываем окно, чтобы избежать мелькания

        # Установка иконки (такой же, как у главного окна)
        if hasattr(parent, 'icon_path') and parent.icon_path:
            try:
                self.iconbitmap(parent.icon_path)
            except Exception:
                pass  # не критично

        # Сохраняем параметры
        self.main_window = main_window_ref

        # Настраиваем тему
        self.current_theme = config_agent.get_theme()
        self._setup_theme_colors()
        self._configure_scrollbar_styles()
        self.configure(bg=self.colors['bg'])

        m = parent
        self._f9b = get_ui_font(m, "default", 9, bold=True)
        self._f9 = get_ui_font(m, "default", 9)
        self._f11b = get_ui_font(m, "default", 11, bold=True)
        self._f8 = get_ui_font(m, "default", 8)
        self._ff8 = get_ui_font(m, "fixed", 8)

        # Свойства окна
        self.title(_("settings_title"))
        self.resizable(False, False)

        # Загружаем данные из конфигурации
        self.categories = config_agent.get_categories()
        self.selected_category = None
        self.safety_settings = config_agent.get_safety_settings()

        # Переменные для виджетов
        self.new_category_var = tk.StringVar()
        self.keyword_var = tk.StringVar()
        self.extension_var = tk.StringVar()

        # Настройки безопасности
        self.check_size_var = tk.BooleanVar(value=self.safety_settings["check_file_size"])
        self.max_size_var = tk.IntVar(value=self.safety_settings["max_size_mb"])

        # Создаём интерфейс (окно всё ещё скрыто)
        self._create_widgets()
        self._populate_categories_list()

        # Даём Tkinter завершить компоновку и рассчитать размеры
        self.update_idletasks()

        # Центрируем окно по экрану
        self._center_on_screen()

        # Настраиваем модальность (без grab_set, чтобы не блокировать раньше времени)
        self.transient(parent)
        self.lift()

        # Перехватываем закрытие через крестик
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_on_screen(self):
        """Рассчитывает и устанавливает геометрию окна по центру экрана (по запрошенным размерам содержимого)."""
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_close(self):
        """Скрывает окно вместо уничтожения."""
        self.grab_release()
        self.withdraw()

    def _setup_theme_colors(self):
        """Устанавливает цвета в зависимости от темы."""
        self.colors = get_palette(self.current_theme)
    
    def apply_theme(self, theme_name):
        """Применяет тему к окну настроек."""
        self.current_theme = theme_name
        self._setup_theme_colors()
        self._configure_scrollbar_styles()
        self.configure(bg=self.colors['bg'])
        
        # Обновляем цвета всех дочерних виджетов рекурсивно
        self._update_widget_colors(self)
        
    def _update_widget_colors(self, parent):
        """Рекурсивно обновляет цвета виджетов."""
        for child in parent.winfo_children():
            if isinstance(child, (tk.Label, tk.Button, tk.Checkbutton, tk.Frame, tk.LabelFrame)):
                try:
                    child.configure(bg=self.colors['bg'])
                except Exception:
                    pass
            if isinstance(child, tk.LabelFrame):
                try:
                    child.configure(fg=self.colors['fg'])
                except Exception:
                    pass
            if isinstance(child, (tk.Label, tk.Button, tk.Checkbutton)):
                try:
                    child.configure(fg=self.colors['fg'])
                except Exception:
                    pass
            if isinstance(child, tk.Listbox):
                child.configure(
                    bg=self.colors['listbox_bg'],
                    fg=self.colors['listbox_fg'],
                    selectbackground=self.colors['listbox_select'],
                    selectforeground='white'
                )
            if isinstance(child, tk.Entry):
                child.configure(bg=self.colors['entry_bg'], fg=self.colors['entry_fg'])
            if isinstance(child, tk.Checkbutton):
                child.configure(
                    selectcolor=self.colors['check_active'],
                    activebackground=self.colors['bg'],
                    activeforeground=self.colors['fg']
                )
            if isinstance(child, ttk.Scrollbar):
                child.configure(style=self._get_scrollbar_style())

            # Сохраняем акцентные цвета, как в старой версии
            if child is getattr(self, 'category_name_label', None):
                child.configure(fg='#FF6B00')
            if child is getattr(self, 'save_button', None):
                child.configure(bg='#FF6B00', fg='white')

            # ... можно добавить другие типы по необходимости
            self._update_widget_colors(child)  # рекурсия

    def _configure_scrollbar_styles(self):
        """Настраивает стили скроллбаров для текущей темы."""
        style = ttk.Style(self)
        style_name = self._get_scrollbar_style()
        style.configure(
            style_name,
            background=self.colors['scrollbar_bg'],
            troughcolor=self.colors['scrollbar_trough'],
            bordercolor=self.colors['scrollbar_trough'],
            arrowcolor=self.colors['fg']
        )
        style.map(
            style_name,
            background=[('active', self.colors['listbox_select'])],
            arrowcolor=[('active', self.colors['fg'])]
        )
        
    def _get_scrollbar_style(self):
        """Возвращает имя стиля для скроллбара в зависимости от темы."""
        return "Dark.Vertical.TScrollbar" if self.current_theme == "dark" else "Light.Vertical.TScrollbar"
    
    def _create_widgets(self):
        """Создание интерфейса окна настроек (без общего скроллбара)."""
        # Основной контейнер
        main_container = tk.Frame(self, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вместо canvas используем обычный Frame, который вмещает всё содержимое
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- РАЗДЕЛ КАТЕГОРИЙ ---
        categories_frame = tk.LabelFrame(content_frame, text=_("categories_frame"), 
                                  bg=self.colors['bg'], fg=self.colors['fg'],
                                  font=self._f9b, padx=10, pady=10)
        categories_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Левая панель: список категорий
        left_frame = tk.Frame(categories_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Список категорий
        categories_list_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        categories_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.categories_listbox = tk.Listbox(
            categories_list_frame,
            font=self._f9,
            selectmode=tk.SINGLE,
            bg=self.colors['listbox_bg'],
            fg=self.colors['listbox_fg'],
            selectbackground=self.colors['listbox_select'],
            selectforeground='white',
            height=8
        )
        categories_scrollbar = ttk.Scrollbar(
            categories_list_frame, 
            orient="vertical", 
            command=self.categories_listbox.yview,
            style=self._get_scrollbar_style()
        )
        self.categories_listbox.configure(yscrollcommand=categories_scrollbar.set)
        
        self.categories_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        categories_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.categories_listbox.bind('<<ListboxSelect>>', self._on_category_select)
        
        # Управление категориями
        add_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        add_frame.pack(fill=tk.X, pady=(10, 5))
        
        tk.Label(add_frame, text=_("new_category_label"), 
                bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Entry(add_frame, textvariable=self.new_category_var, width=20,
                bg=self.colors['entry_bg'], fg=self.colors['entry_fg']).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(add_frame, text=_("add_btn"), command=self._add_category,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT)
        
        edit_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        edit_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Button(edit_frame, text=_("rename_btn"), command=self._rename_category,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(edit_frame, text=_("delete_btn"), command=self._delete_category,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT)
        
        # Правая панель: настройка выбранной категории
        right_frame = tk.LabelFrame(categories_frame, text=_("category_settings"),
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=self._f9b, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.category_name_label = tk.Label(
            right_frame, 
            text=_("select_category"),
            font=self._f11b,
            bg=self.colors['bg'],
            fg='#FF6B00'
        )
        self.category_name_label.pack(pady=(0, 10))
        
        # Ключевые слова
        keywords_frame = tk.LabelFrame(right_frame, text=_("keywords_frame"),
                                      bg=self.colors['bg'], fg=self.colors['fg'],
                                      font=self._f9, padx=8, pady=8)
        keywords_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        keywords_list_frame = tk.Frame(keywords_frame, bg=self.colors['bg'])
        keywords_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.keywords_listbox = tk.Listbox(
            keywords_list_frame,
            font=self._ff8,
            height=3,
            bg=self.colors['listbox_bg'],
            fg=self.colors['listbox_fg'],
            selectbackground=self.colors['listbox_select'],
            selectforeground='white'
        )
        keywords_scrollbar = ttk.Scrollbar(
            keywords_list_frame, 
            orient="vertical", 
            command=self.keywords_listbox.yview,
            style=self._get_scrollbar_style()
        )
        self.keywords_listbox.configure(yscrollcommand=keywords_scrollbar.set)
        
        self.keywords_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        keywords_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        keyword_input_frame = tk.Frame(keywords_frame, bg=self.colors['bg'])
        keyword_input_frame.pack(fill=tk.X, pady=(8, 0))
        
        input_frame = tk.Frame(keyword_input_frame, bg=self.colors['bg'])
        input_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(input_frame, text=_("new_keyword"), 
                bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Entry(input_frame, textvariable=self.keyword_var, width=22,
                bg=self.colors['entry_bg'], fg=self.colors['entry_fg']).pack(side=tk.LEFT, padx=(5, 0))
        
        buttons_frame = tk.Frame(keyword_input_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.X)
        tk.Button(buttons_frame, text=_("add_keyword_btn"), command=self._add_keyword,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(buttons_frame, text=_("delete_keyword_btn"), command=self._delete_keyword,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT)
        
        # Расширения файлов
        extensions_frame = tk.LabelFrame(right_frame, text=_("extensions_frame"),
                                        bg=self.colors['bg'], fg=self.colors['fg'],
                                        font=self._f9, padx=8, pady=8)
        extensions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        extensions_list_frame = tk.Frame(extensions_frame, bg=self.colors['bg'])
        extensions_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.extensions_listbox = tk.Listbox(
            extensions_list_frame,
            font=self._ff8,
            height=3,
            bg=self.colors['listbox_bg'],
            fg=self.colors['listbox_fg'],
            selectbackground=self.colors['listbox_select'],
            selectforeground='white'
        )
        extensions_scrollbar = ttk.Scrollbar(
            extensions_list_frame, 
            orient="vertical", 
            command=self.extensions_listbox.yview,
            style=self._get_scrollbar_style()
        )
        self.extensions_listbox.configure(yscrollcommand=extensions_scrollbar.set)
        
        self.extensions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        extensions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        extension_input_frame = tk.Frame(extensions_frame, bg=self.colors['bg'])
        extension_input_frame.pack(fill=tk.X, pady=(8, 0))
        
        ext_input_frame = tk.Frame(extension_input_frame, bg=self.colors['bg'])
        ext_input_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(ext_input_frame, text=_("new_extension"),
                bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        tk.Entry(ext_input_frame, textvariable=self.extension_var, width=22,
                bg=self.colors['entry_bg'], fg=self.colors['entry_fg']).pack(side=tk.LEFT, padx=(5, 0))
        
        ext_buttons_frame = tk.Frame(extension_input_frame, bg=self.colors['bg'])
        ext_buttons_frame.pack(fill=tk.X)
        tk.Button(ext_buttons_frame, text=_("add_extension_btn"), command=self._add_extension,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(ext_buttons_frame, text=_("delete_extension_btn"), command=self._delete_extension,
                 bg=self.colors['button_bg'], fg=self.colors['button_fg']).pack(side=tk.LEFT)
        
        # --- РАЗДЕЛ БЕЗОПАСНОСТИ ---
        safety_frame = tk.LabelFrame(content_frame, text=_("safety_frame"), 
                                  bg=self.colors['bg'], fg=self.colors['fg'],
                                  font=self._f9b, padx=10, pady=10)
        safety_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        check_size_frame = tk.Frame(safety_frame, bg=self.colors['bg'])
        check_size_frame.pack(fill=tk.X, pady=(3, 5))
        
        self.check_size_checkbutton = tk.Checkbutton(
            check_size_frame,
            text=_("check_size_cb"),
            variable=self.check_size_var,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            selectcolor=self.colors['check_active'],
            activebackground=self.colors['bg'],
            activeforeground=self.colors['fg']
        )
        self.check_size_checkbutton.pack(anchor="w")
        
        max_size_frame = tk.Frame(safety_frame, bg=self.colors['bg'])
        max_size_frame.pack(fill=tk.X, pady=(5, 5))
        
        tk.Label(max_size_frame, text=_("max_size_label"),
                bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=(0, 5))
        
        def validate_size_input(action, value_if_allowed):
            # Разрешаем только целые неотрицательные значения для поля порога.
            if action == '1':
                if value_if_allowed:
                    try:
                        int(value_if_allowed)
                        return True
                    except ValueError:
                        return False
                return True
            return True
        
        vcmd = (self.register(validate_size_input), '%d', '%P')
        self.max_size_entry = tk.Entry(max_size_frame, textvariable=self.max_size_var, width=8,
                                     bg=self.colors['entry_bg'], fg=self.colors['entry_fg'],
                                     validate='key', validatecommand=vcmd)
        self.max_size_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(max_size_frame, text=_("mb_unit"),
                bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT)
        
        note_frame = tk.Frame(safety_frame, bg=self.colors['bg'])
        note_frame.pack(fill=tk.X, pady=(5, 0))
        
        note_text = _("safety_note")
        tk.Label(note_frame, text=note_text, justify=tk.LEFT,
                bg=self.colors['bg'], fg=self.colors['fg'],
                font=self._f8).pack(anchor="w")
        
        # Кнопки сохранения/отмены
        buttons_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.save_button = tk.Button(
            buttons_frame,
            text=_("save_close_btn"),
            command=self._save_and_close,
            bg='#FF6B00',
            fg='white',
            font=self._f9b
        )
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            buttons_frame,
            text=_("cancel_btn_settings"),
            command=self._on_close,
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg']
        ).pack(side=tk.RIGHT, padx=5)
        
    def _populate_categories_list(self):
        """Заполняет список категорий."""
        self.categories_listbox.delete(0, tk.END)
        for category in sorted(self.categories.keys()):
            self.categories_listbox.insert(tk.END, category)

    def _get_misc_category_name(self):
        """Возвращает фактическое имя служебной категории в текущем конфиге."""
        if "Разное" in self.categories:
            return "Разное"

        localized_misc = _("misc_category")
        if localized_misc in self.categories:
            return localized_misc

        return "Разное"

    def _on_category_select(self, event):
        """Обработка выбора категории."""
        selection = self.categories_listbox.curselection()
        if not selection:
            return
        
        self.selected_category = self.categories_listbox.get(selection[0])
        self.category_name_label.config(text=_("category_selected", name=self.selected_category))
        
        # Заполняем ключевые слова
        self.keywords_listbox.delete(0, tk.END)
        keywords = self.categories[self.selected_category].get('keywords', [])
        for keyword in sorted(keywords):
            self.keywords_listbox.insert(tk.END, keyword)
        
        # Заполняем расширения
        self.extensions_listbox.delete(0, tk.END)
        extensions = self.categories[self.selected_category].get('extensions', [])
        for extension in sorted(extensions):
            self.extensions_listbox.insert(tk.END, extension)
    
    def _add_category(self):
        """Добавляет новую категорию."""
        new_name = self.new_category_var.get().strip()
        
        # ВАЛИДАЦИЯ:
        # 1. Не пустая строка
        if not new_name:
            messagebox.showwarning(_("warning"), _("enter_category_name"), parent=self)
            return
        
        # 2. Не слишком длинное
        if len(new_name) > 50:
            messagebox.showwarning(_("warning"), _("name_too_long"), parent=self)
            return
        
        # 3. Нет запрещенных символов
        forbidden_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in forbidden_chars:
            if char in new_name:
                messagebox.showwarning(_("warning"), _("forbidden_char", char=char), parent=self)
                return
        
        # 4. Не дублируется
        if new_name in self.categories:
            messagebox.showwarning(_("warning"), _("category_exists", name=new_name), parent=self)
            return
        
        # Добавляем новую категорию
        self.categories[new_name] = {"extensions": [], "keywords": []}
        self._populate_categories_list()
        self.new_category_var.set("")
        
        # Выбираем новую категорию
        index = list(sorted(self.categories.keys())).index(new_name)
        self.categories_listbox.selection_set(index)
        self._on_category_select(None)
    
    def _delete_category(self):
        """Удаляет выбранную категорию."""
        if not self.selected_category:
            messagebox.showwarning(_("warning"), _("select_to_delete"), parent=self)
            return
        
        misc_name = self._get_misc_category_name()
        if self.selected_category == misc_name:
            messagebox.showwarning(_("warning"), _("cannot_delete_misc"), parent=self)
            return
        
        # Подтверждение удаления ЛЮБОЙ категории
        response = messagebox.askyesno(
            _("confirm_delete"),
            _("confirm_delete_msg", name=self.selected_category, misc=misc_name),
            parent=self
        )
        
        if not response:
            return  # Отмена
        
        del self.categories[self.selected_category]
        self.selected_category = None
        self._populate_categories_list()
        self.category_name_label.config(text=_("select_category"))
        self.keywords_listbox.delete(0, tk.END)
        self.extensions_listbox.delete(0, tk.END)
        
        # Сообщение об успехе
        messagebox.showinfo(_("success"), _("category_deleted"), parent=self)
    
    def _rename_category(self):
        """Переименовывает выбранную категорию."""
        if not self.selected_category:
            messagebox.showwarning(_("warning"), _("select_to_rename"), parent=self)
            return
        
        misc_name = self._get_misc_category_name()
        if self.selected_category == misc_name:
            messagebox.showwarning(_("warning"), _("cannot_rename_misc"), parent=self)
            return
        
        new_name = simpledialog.askstring(
            _("rename_title"),
            _("rename_prompt", name=self.selected_category),
            parent=self
        )
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            
            # ВАЛИДАЦИЯ:
            if not new_name:
                return
            if len(new_name) > 50:
                messagebox.showwarning(_("warning"), _("name_too_long"), parent=self)
                return
            forbidden_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            for char in forbidden_chars:
                if char in new_name:
                    messagebox.showwarning(_("warning"), _("forbidden_char", char=char), parent=self)
                    return
            if new_name in self.categories:
                messagebox.showwarning(_("warning"), _("category_exists", name=new_name), parent=self)
                return
            
            # Переносим данные под новым именем
            self.categories[new_name] = self.categories.pop(self.selected_category)
            self.selected_category = new_name
            self._populate_categories_list()
            self.category_name_label.config(text=_("category_selected", name=new_name))
    
    def _add_keyword(self):
        """Добавляет ключевое слово."""
        if not self.selected_category:
            messagebox.showwarning(_("warning"), _("select_category"), parent=self)
            return
        
        keyword = self.keyword_var.get().strip().lower()
        
        # ВАЛИДАЦИЯ:
        if not keyword:
            messagebox.showwarning(_("warning"), _("enter_keyword"), parent=self)
            return
        if len(keyword) > 100:
            messagebox.showwarning(_("warning"), _("keyword_too_long"), parent=self)
            return
        
        keywords = self.categories[self.selected_category]['keywords']
        if keyword in keywords:
            messagebox.showwarning(_("warning"), _("keyword_exists"), parent=self)
            return
        
        keywords.append(keyword)
        self.keywords_listbox.insert(tk.END, keyword)
        self.keyword_var.set("")
    
    def _delete_keyword(self):
        """Удаляет выбранное ключевое слово."""
        if not self.selected_category:
            return
        
        selection = self.keywords_listbox.curselection()
        if not selection:
            messagebox.showwarning(_("warning"), _("select_keyword"), parent=self)
            return
        
        keyword = self.keywords_listbox.get(selection[0])
        self.categories[self.selected_category]['keywords'].remove(keyword)
        self.keywords_listbox.delete(selection[0])
    
    def _add_extension(self):
        """Добавляет расширение файла."""
        if not self.selected_category:
            messagebox.showwarning(_("warning"), _("select_category"), parent=self)
            return
        
        extension = self.extension_var.get().strip().lower()
        
        # ВАЛИДАЦИЯ:
        if not extension:
            messagebox.showwarning(_("warning"), _("enter_extension"), parent=self)
            return
        if len(extension) > 20:
            messagebox.showwarning(_("warning"), _("extension_too_long"), parent=self)
            return
        
        # Добавляем точку, если её нет
        if not extension.startswith('.'):
            extension = '.' + extension
        
        # Проверяем формат
        if len(extension) < 2 or extension.count('.') > 1:
            messagebox.showwarning(_("warning"), _("extension_invalid"), parent=self)
            return
        
        extensions = self.categories[self.selected_category]['extensions']
        if extension in extensions:
            messagebox.showwarning(_("warning"), _("extension_exists"), parent=self)
            return
        
        extensions.append(extension)
        self.extensions_listbox.insert(tk.END, extension)
        self.extension_var.set("")
    
    def _delete_extension(self):
        """Удаляет выбранное расширение."""
        if not self.selected_category:
            return
        
        selection = self.extensions_listbox.curselection()
        if not selection:
            messagebox.showwarning(_("warning"), _("select_extension"), parent=self)
            return
        
        extension = self.extensions_listbox.get(selection[0])
        self.categories[self.selected_category]['extensions'].remove(extension)
        self.extensions_listbox.delete(selection[0])
    
    def _fade_in(self):
        """Плавно увеличивает непрозрачность окна от 0.0 до 1.0."""
        self.attributes('-alpha', 0.0)  # Делаем окно полностью прозрачным
        self.deiconify()                # Показываем окно (но его не видно)
        
        # Запускаем анимацию появления
        self._animate_fade_in(alpha=0.0)

    def _animate_fade_in(self, alpha):
        """Рекурсивно увеличивает прозрачность окна."""
        alpha += 0.2  # Шаг увеличения прозрачности
        if alpha >= 1.0:
            self.attributes('-alpha', 1.0)  # Конец анимации: окно полностью видимо
            return
    
        self.attributes('-alpha', alpha)  # Применяем новую прозрачность
        # Планируем следующий шаг анимации через 20 мс
        self.after(20, self._animate_fade_in, alpha)
    
    def _save_and_close(self):
        """Сохраняет изменения и закрывает окно."""
        # Сохраняем настройки безопасности с ВАЛИДАЦИЕЙ
        max_size = self.max_size_var.get()
        
        # Проверяем минимальное значение
        if max_size < 1:
            messagebox.showwarning(_("warning"), _("min_size_error"), parent=self)
            self.max_size_entry.focus_set()
            return
        
        # Проверяем максимальное значение (100 ГБ = 102400 МБ)
        if max_size > 102400:
            messagebox.showwarning(_("warning"), _("max_size_error"), parent=self)
            self.max_size_entry.focus_set()
            return

        # Сохраняем категории только после успешной валидации
        config_agent.update_categories(self.categories)
        
        config_agent.set_safety_settings(
            check_file_size=self.check_size_var.get(),
            max_size_mb=max_size
        )
        
        if hasattr(self.main_window, '_update_safety_settings_from_config'):
            self.main_window._update_safety_settings_from_config()
        else:
            # Fallback на старый метод для совместимости
            self.main_window._update_check_size_text()
        
        messagebox.showinfo(_("saved"), _("settings_saved"), parent=self)
        self._on_close()
