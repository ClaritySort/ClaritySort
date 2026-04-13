# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""Общие утилиты: базовая директория приложения (скрипт / frozen EXE)."""
import os
import sys


def get_base_dir() -> str:
    """Каталог, где лежит EXE или корень проекта при запуске из исходников."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
