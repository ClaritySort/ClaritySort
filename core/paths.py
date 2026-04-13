# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""Пути к ресурсам: режим скрипта и PyInstaller (_MEIPASS)."""
import os
import sys


def resource_path(relative_path: str) -> str:
    """Абсолютный путь к файлу рядом с проектом или внутри распакованного onefile-бандла."""
    try:
        base = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
