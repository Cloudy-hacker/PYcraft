# -*- coding: utf-8 -*-
"""
Конфигурация шрифтов для PYcraft
"""
import os

# Папка со шрифтами
FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Настройки шрифтов
# Формат: (путь_к_файлу.ttf, размер)
FONTS = {
    "small": ("arial-cyr.ttf", 10),
    "normal": ("arial-cyr.ttf", 14),
    "big": ("arial-cyr.ttf", 24),
}

# Резервный шрифт (если файл не найден)
FALLBACK_FONT = "arial"
