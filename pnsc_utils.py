# pnsc_utils.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import uuid
import os
import json
import time
from datetime import datetime
from tkinter import font as tkFont
import csv

# --- ИМПОРТ И ПРОВЕРКА PILLOW ---
try:
    from PIL import Image, ImageTk
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    # print("Внимание: Библиотека Pillow не установлена. Функционал иконок и фоновых изображений будет недоступен.")
    # print("Для установки: pip install Pillow")

# --- КОНСТАНТЫ ДЛЯ ИКОНОК УПРАВЛЕНИЯ ---
# ВНИМАНИЕ: Замените эти пути на реальные пути к вашим иконкам (PNG, JPG и т.д.)
CONTROL_ICONS = {
    "create_note": "icons/note.png",
    "create_timer": "icons/timer.png",
    "work_table": "icons/table.png",
    "copy_text": "icons/copy.png",
    "clear_text": "icons/clear.png",
    "create_tab": "icons/add_tab.png",
    "create_button": "icons/add_button.png",
    "edit_mode": "icons/edit.png",
    "main_app_icon_png": "icons/pnsc_icon.png", # Основная иконка (PNG)
    "main_app_icon_ico": "icons/pnsc_icon.ico",  # Резервная иконка (ICO для Windows)
    "settings": "icons/123.png",      # Иконка для кнопки настроек NoteWidget
    "note_manager": "icons/123.png", # Иконка для кнопки "Менеджер заметок"
    "clear_notes": "icons/123.png"  # Иконка для кнопки "Очистить все заметки"
}