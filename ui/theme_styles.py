# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""
Модуль ttk-стилей.
Содержит базовые стили для стандартных ttk-виджетов под светлую/тёмную тему.
"""
import tkinter as tk
from tkinter import ttk

def configure_styles(theme_colors):
    """Настраивает стили ttk в зависимости от темы."""
    style = ttk.Style()
    style.theme_use('clam')
    
    # Основные цвета
    bg = theme_colors['bg']
    fg = theme_colors['fg']
    btn_bg = theme_colors['button_bg']
    btn_fg = theme_colors['button_fg']
    entry_bg = theme_colors['entry_bg']
    entry_fg = theme_colors['entry_fg']
    accent = theme_colors['accent']
    
    # Общие стили для всех виджетов
    style.configure('.', background=bg, foreground=fg, fieldbackground=entry_bg)
    
    # Словарь стилей для виджетов
    # Каждый ключ - имя виджета ttk, значение - словарь с параметрами стиля
    styles = {
        # Фреймы
        'TFrame': {'background': bg},  # Обычный фрейм
        
        # Фреймы с заголовком
        'TLabelframe': {'background': bg, 'foreground': fg},  # Основной фрейм
        'TLabelframe.Label': {'background': bg, 'foreground': fg},  # Заголовок фрейма
        
        # Метки (текст)
        'TLabel': {'background': bg, 'foreground': fg},  # Текстовые метки
        
        # Кнопки
        'TButton': {
            'background': btn_bg,      # Цвет фона кнопки
            'foreground': btn_fg,      # Цвет текста кнопки
            'borderwidth': 1,          # Толщина границы
            'relief': 'raised'         # Стиль 3D-эффекта (приподнятый)
        },
        
        # Поля ввода
        'TEntry': {
            'fieldbackground': entry_bg,  # Цвет фона поля ввода
            'foreground': entry_fg,       # Цвет текста в поле
            'insertcolor': fg             # Цвет курсора вставки
        },
        
        # Чекбоксы
        'TCheckbutton': {'background': bg, 'foreground': fg},  # Флажки
        
        # Прогресс-бары
        'TProgressbar': {
            'background': accent,     # Цвет заполнения
            'troughcolor': bg,        # Цвет фона (дорожки)
            'bordercolor': bg,        # Цвет границы
            'lightcolor': accent,     # Цвет светлой части (3D эффект)
            'darkcolor': accent       # Цвет темной части (3D эффект)
        },
        
        # Скроллбары
        'TScrollbar': {
            'background': btn_bg,     # Цвет ползунка
            'troughcolor': bg,        # Цвет фона (дорожки)
            'bordercolor': bg,        # Цвет границы
            'arrowcolor': fg          # Цвет стрелок
        },
        
        # Выпадающие списки
        'TCombobox': {
            'fieldbackground': entry_bg,  # Цвет фона поля
            'background': btn_bg,         # Цвет фона списка
            'foreground': fg              # Цвет текста
        }
    }
    
    # Применение всех стилей ко всем виджетам
    for widget, config in styles.items():
        style.configure(widget, **config)
    
    return style


# Единые палитры для главного окна и настроек (не дублировать в нескольких файлах).
LIGHT_PALETTE = {
    "bg": "#FFFFFF",
    "fg": "#000000",
    "accent": "#FF6B00",
    "log_bg": "#F5F5F5",
    "log_fg": "#333333",
    "entry_bg": "white",
    "entry_fg": "black",
    "listbox_bg": "white",
    "listbox_fg": "black",
    "listbox_select": "#FF6B00",
    "button_bg": "#F0F0F0",
    "button_fg": "#000000",
    "frame_bg": "#F5F5F5",
    "label_bg": "#FFFFFF",
    "scrollbar_bg": "#C0C0C0",
    "scrollbar_trough": "#E0E0E0",
    "progress_trough": "#E0E0E0",
    "progress_bg": "#FF6B00",
    "progress_fg": "#FF6B00",
    "check_active": "#FF6B00",
    "check_inactive": "#FFFFFF",
    "check_inactive_dark": "#1A1A1A",
    "entry_disabled_bg": "#E6E6E6",
    "entry_disabled_fg": "#888888",
    "button_disabled_bg": "#E6E6E6",
    "button_disabled_fg": "#888888",
    "radio_active": "#FF6B00",
    "radio_bg": "#FFFFFF",
}

DARK_PALETTE = {
    "bg": "#1A1A1A",
    "fg": "#E0E0E0",
    "accent": "#FF6B00",
    "log_bg": "#2A2A2A",
    "log_fg": "#E0E0E0",
    "entry_bg": "#2A2A2A",
    "entry_fg": "#E0E0E0",
    "listbox_bg": "#2A2A2A",
    "listbox_fg": "#E0E0E0",
    "listbox_select": "#FF6B00",
    "button_bg": "#333333",
    "button_fg": "#E0E0E0",
    "frame_bg": "#2A2A2A",
    "label_bg": "#1A1A1A",
    "scrollbar_bg": "#404040",
    "scrollbar_trough": "#2A2A2A",
    "progress_trough": "#2A2A2A",
    "progress_bg": "#FF6B00",
    "progress_fg": "#FF6B00",
    "check_active": "#FF6B00",
    "check_inactive": "#1A1A1A",
    "check_inactive_dark": "#1A1A1A",
    "entry_disabled_bg": "#1F1F1F",
    "entry_disabled_fg": "#777777",
    "button_disabled_bg": "#1F1F1F",
    "button_disabled_fg": "#777777",
    "radio_active": "#FF6B00",
    "radio_bg": "#1A1A1A",
}


def get_palette(theme: str) -> dict:
    """Возвращает копию палитры для темы 'light' или 'dark'."""
    if theme == "dark":
        return dict(DARK_PALETTE)
    return dict(LIGHT_PALETTE)


def get_ui_font(master, role="default", size=10, bold=False):
    """
    Шрифт на базе TkDefaultFont / TkFixedFont — переносимо на Windows/Linux/macOS.
    role: 'default' | 'fixed'
    """
    import tkinter.font as tkfont

    logical = "TkFixedFont" if role == "fixed" else "TkDefaultFont"
    try:
        base = tkfont.nametofont(logical, root=master)
        fam = base.actual("family")
    except Exception:
        fam = logical
    if bold:
        return (fam, size, "bold")
    return (fam, size)
