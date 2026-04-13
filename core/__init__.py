# -*- coding: utf-8 -*-
# Copyright (c) 2026 ClaritySort
# SPDX-License-Identifier: MIT
"""Пакет `core`: конфиг, локализация, логирование и движок сортировки."""
from .config_manager import ConfigHandler, config_agent
from .sorter_engine import ChaosSorter
from .operation_logger import OperationLogger
