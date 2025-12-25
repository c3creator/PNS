
# module_buttons_tabs.py

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import uuid
import os
import json

# Попытка импортировать Pillow компоненты
try:
    from PIL import Image, ImageTk
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("Pillow не установлен. Функции работы с изображениями будут отключены.")

import tkinter.font as tkFont

# Импортируем новый модуль плавающего виджета
from floating_widget import FloatingWidget # Предполагается, что floating_widget.py находится в той же директории

class App: # Основной класс приложения
    CONFIG_FILE = "config.json"
    
    def __init__(self, master):
        self.master = master
        self.master.title("PNSc - Buttons & Tabs")
        self.master.geometry("800x600")

        self.tabs = {}  # Хранит вкладки и их кнопки
        self.selected_tab_id = None
        self.active_button_widgets = {} # Хранит экземпляры ButtonWidget для текущей вкладки
        self.column_frames = [] # Для отслеживания фреймов, содержащих содержимое вкладок
        self.tab_widgets = {} # Для хранения виджетов Tkinter, связанных с вкладками
        
        self.default_button_color = "#e0e0e0"

        self.edit_mode_active = tk.BooleanVar(value=False)

        # Инициализируем ссылку на экземпляр плавающего виджета
        self.floating_widget_instance = None 

        self._load_config()
        self._create_main_ui()
        
        # Создаем менеджер вкладок
        self.button_tab_manager = ButtonTabManager(self) # Передаем себя (экземпляр App)

        self.button_tab_manager.update_tab_display() # Изначальное отображение вкладок
        
        # Обработка закрытия окна
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """Обрабатывает событие закрытия главного окна."""
        if self.floating_widget_instance and self.floating_widget_instance.winfo_exists():
            self.floating_widget_instance.destroy() # Убедимся, что плавающий виджет сохраняет свое состояние
        self.save_config(show_message=False) # Сохраняем основную конфигурацию
        self.master.destroy()

    def _create_main_ui(self):
        """Создает основной пользовательский интерфейс приложения."""
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Область для вкладок (где кнопки вкладок и холст будут управляться ButtonTabManager)
        self.tabs_pane = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)
        self.tabs_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Текстовая область для вывода
        text_area_frame = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)
        text_area_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.text_area = tk.Text(text_area_frame, wrap=tk.WORD, undo=True)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_scroll = tk.Scrollbar(text_area_frame, command=self.text_area.yview)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=text_scroll.set)

        # Панель управления для глобальных действий
        control_panel = tk.Frame(self.master, bd=2, relief=tk.RAISED)
        control_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        tk.Button(control_panel, text="Создать вкладку", command=self.button_tab_manager.create_tab_dialog).pack(side=tk.LEFT, padx=5, pady=2)
        
        self.edit_mode_button = tk.Button(control_panel, text="Режим редактирования",
                                         command=self.toggle_edit_mode)
        self.edit_mode_button.pack(side=tk.LEFT, padx=5, pady=2)
        
        tk.Button(control_panel, text="Сохранить", command=lambda: self.save_config(show_message=True)).pack(side=tk.RIGHT, padx=5, pady=2)

    # --- Методы, которые вызываются ButtonTabManager через self.app ---
    # Эти методы должны быть частью класса App.
    
    def toggle_edit_mode(self):
        """Переключает режим редактирования кнопок на холсте."""
        is_active = self.edit_mode_active.get()
        self.edit_mode_active.set(not is_active) # Переключаем состояние

        for widget in self.active_button_widgets.values():
            widget.update_edit_visibility()

        if self.edit_mode_active.get():
            self.edit_mode_button.config(relief=tk.SUNKEN)
        else:
            self.edit_mode_button.config(relief=tk.RAISED)

    def update_tab_display(self):
        self.button_tab_manager.update_tab_display()

    def switch_tab(self, tab_id):
        self.button_tab_manager.switch_tab(tab_id)

    def show_tab_context_menu(self, event, tab_id):
        self.button_tab_manager.show_tab_context_menu(event, tab_id)

    def settings_tab_dialog(self, tab_id):
        self.button_tab_manager.settings_tab_dialog(tab_id)

    def delete_tab_dialog(self, tab_id):
        self.button_tab_manager.delete_tab_dialog(tab_id)

    def create_button_dialog(self, initial_tab_id=None):
        self.button_tab_manager.create_button_dialog(initial_tab_id)

    def show_button_context_menu(self, event, tab_id, button_id):
        self.button_tab_manager.show_button_context_menu(event, tab_id, button_id)

    def edit_button_dialog(self, tab_id, button_id):
        self.button_tab_manager.edit_button_dialog(tab_id, button_id)

    def delete_button_dialog(self, tab_id, button_id):
        self.button_tab_manager.delete_button_dialog(tab_id, button_id)
        
    def toggle_floating_widget(self):
        """Открывает или закрывает плавающий виджет кнопок."""
        if self.floating_widget_instance and self.floating_widget_instance.winfo_exists():
            self.floating_widget_instance.destroy()
            self.floating_widget_instance = None
        else:
            self.floating_widget_instance = FloatingWidget(self.master, self)
            # update_widget_buttons вызывается в __init__ FloatingWidget, поэтому здесь не нужно

    # --- Вспомогательные методы ---
    def _show_messagebox(self, type, title, message):
        """Отображает стандартное диалоговое окно сообщения."""
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)
        elif type == "askyesno":
            return messagebox.askyesno(title, message)

    def center_window(self, window):
        """Центрирует дочернее окно относительно основного."""
        window.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (window.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (window.winfo_height() // 2)
        window.geometry(f"+{x}+{y}")

    def _choose_image(self, var):
        """Открывает диалог выбора файла изображения и обновляет StringVar."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")])
        if file_path:
            var.set(file_path)

    def _choose_color(self, var):
        """Открывает диалог выбора цвета и обновляет StringVar."""
        color_code = colorchooser.askcolor(title="Выбрать цвет")[1]
        if color_code:
            var.set(color_code)

    def save_config(self, show_message=True):
        """Сохраняет текущую конфигурацию вкладок и кнопок в файл."""
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tabs, f, indent=4, ensure_ascii=False)
            if show_message:
                self._show_messagebox("info", "Сохранение", "Конфигурация успешно сохранена.")
        except Exception as e:
            self._show_messagebox("error", "Ошибка сохранения", f"Не удалось сохранить конфигурацию: {e}")

    def _load_config(self):
        """Загружает конфигурацию вкладок и кнопок из файла."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.tabs = json.load(f)
            except json.JSONDecodeError as e:
                self._show_messagebox("error", "Ошибка загрузки", f"Не удалось прочитать файл конфигурации: {e}")
                self.tabs = {}
            except Exception as e:
                self._show_messagebox("error", "Ошибка загрузки", f"Не удалось загрузить конфигурацию: {e}")
                self.tabs = {}

# --- Класс ButtonWidget (без изменений от предоставленного) ---
class ButtonWidget:
    """Виджет кнопки, перетаскиваемый и изменяемый в размере на канвасе вкладки."""
    def __init__(self, app_instance, manager_instance, canvas, tab_id, button_id, button_data):
        self.app = app_instance
        self.manager = manager_instance # Ссылка на ButtonTabManager
        self.canvas = canvas
        self.tab_id = tab_id
        self.button_id = button_id
        self.data = button_data
        self.icon_photo = None

        self.data.setdefault('x', 10)
        self.data.setdefault('y', 10)
        self.data.setdefault('width', 100)
        self.data.setdefault('height', 30)
        self.data.setdefault('color', self.app.default_button_color)
        self.data.setdefault('text_color', 'black')
        self.data.setdefault('font_size', 10)
        self.data.setdefault('font_family', 'Arial')
        self.data.setdefault('font_style', '')
        self.data.setdefault('new_line', False)
        self.data.setdefault('clear_text', False)
        self.data.setdefault('icon', '')
        self.data.setdefault('output', '') # Убедимся, что 'output' всегда есть
        # Grid settings for the button itself, overriding tab settings if desired
        self.data.setdefault('snap_to_grid', True) 
        self.data.setdefault('grid_size_x', 10)
        self.data.setdefault('grid_size_y', 10)

        self.button = tk.Button(canvas,
                                command=self._handle_click_or_edit,
                                relief=tk.RAISED)

        self.canvas_item = canvas.create_window(self.data['x'], self.data['y'],
                                                window=self.button,
                                                anchor=tk.NW,
                                                width=self.data['width'],
                                                height=self.data['height'])

        self.update_style()
        self._bind_drag_events()
        self._bind_resize_events()
        self._bind_context_menu()

        self.update_edit_visibility()

    def _handle_click_or_edit(self):
        if not self.app.edit_mode_active.get():
            self._on_click()

    def _on_click(self):
        # Вызываем метод из главного приложения
        self.manager._on_button_click_internal(self.tab_id, self.button_id)

    def _bind_context_menu(self):
        self.button.bind("<Button-3>", lambda event: self.app.show_button_context_menu(event, self.tab_id, self.button_id))

    def _bind_drag_events(self):
        self._drag_data = {"x": 0, "y": 0}
        self.button.bind("<Button-1>", self._on_drag_start)
        self.button.bind("<B1-Motion>", self._on_drag_motion)
        self.button.bind("<ButtonRelease-1>", self._on_drag_end)

    def _on_drag_start(self, event):
        if not self.app.edit_mode_active.get():
            return
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        if not self.app.edit_mode_active.get():
            return
        
        x1, y1 = self.canvas.coords(self.canvas_item)
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        new_x = x1 + delta_x
        new_y = y1 + delta_y
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        current_width = self.data.get('width', 100)
        current_height = self.data.get('height', 30)

        # 1. Привязка к сетке (Grid Snapping)
        # Используем собственные настройки привязки кнопки, или дефолтные, если не заданы
        snap_enabled = self.data.get('snap_to_grid', True) 
        grid_x = self.data.get('grid_size_x', 10) if snap_enabled else 1
        grid_y = self.data.get('grid_size_y', 10) if snap_enabled else 1
        
        if snap_enabled and grid_x > 0 and grid_y > 0: # Убедимся, что размер сетки положительный
            new_x = round(new_x / grid_x) * grid_x
            new_y = round(new_y / grid_y) * grid_y

        # Ограничение по границам канваса
        new_x = max(0, min(new_x, canvas_width - current_width))
        new_y = max(0, min(new_y, canvas_height - current_height))
        
        self.canvas.coords(self.canvas_item, new_x, new_y)
        self.data['x'] = new_x
        self.data['y'] = new_y

    def _on_drag_end(self, event):
        if self.app.edit_mode_active.get():
            # Сохраняем настройки, включая новые координаты
            self.app.save_config(show_message=False)

    def _bind_resize_events(self):
        self._resize_handle = tk.Frame(self.button, bg="gray", width=8, height=8, cursor="sizing")
        self._resize_handle.place(relx=1.0, rely=1.0, anchor=tk.SE)
        self._resize_data = {"width": 0, "height": 0, "start_x": 0, "start_y": 0}
        self._resize_handle.bind("<Button-1>", self._on_resize_start)
        self._resize_handle.bind("<B1-Motion>", self._on_resize_motion)
        self._resize_handle.bind("<ButtonRelease-1>", self._on_resize_end)

    def _on_resize_start(self, event):
        if not self.app.edit_mode_active.get():
            return
        self._resize_data["start_x"] = event.x
        self._resize_data["start_y"] = event.y
        self._resize_data["width"] = self.data['width']
        self._resize_data["height"] = self.data['height']
        
        return "break"

    def _on_resize_motion(self, event):
        if not self.app.edit_mode_active.get():
            return
        
        delta_w = event.x - self._resize_data["start_x"]
        delta_h = event.y - self._resize_data["start_y"]
        min_width = 30
        min_height = 20
        
        new_width = max(min_width, self._resize_data["width"] + delta_w)
        new_height = max(min_height, self._resize_data["height"] + delta_h)
        
        # Привязка размера к сетке, если включено
        snap_enabled = self.data.get('snap_to_grid', True)
        grid_x = self.data.get('grid_size_x', 10) if snap_enabled else 1
        grid_y = self.data.get('grid_size_y', 10) if snap_enabled else 1
        
        if snap_enabled and grid_x > 0 and grid_y > 0:
            # Привязываем новую ширину/высоту к сетке
            new_width = round(new_width / grid_x) * grid_x
            new_height = round(new_height / grid_y) * grid_y
            new_width = max(min_width, new_width) # Убедимся, что не становится меньше минимума после привязки
            new_height = max(min_height, new_height) # Убедимся, что не становится меньше минимума после привязки


        self.data['width'] = new_width
        self.data['height'] = new_height
        self.canvas.itemconfig(self.canvas_item, width=new_width, height=new_height)
        self.button.update_idletasks()
        self._resize_handle.place(relx=1.0, rely=1.0, anchor=tk.SE)
        
    def _on_resize_end(self, event):
        if self.app.edit_mode_active.get():
            # После изменения размера, повторно применяем логику перетаскивания, чтобы убедиться, что координаты
            # привязаны к сетке, если это необходимо. Передаем фиктивное событие, чтобы оно рассматривалось как событие окончания.
            # Это важно для привязки верхнего левого угла после изменения размера.
            self._on_drag_motion(event) 
            self.app.save_config(show_message=False)

    def update_icon_and_text(self):
        icon_path = self.data.get('icon')

        if HAS_PILLOW and icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                btn_w = max(16, self.data['width'] - 10)
                btn_h = max(16, self.data['height'] - 10)
                size = min(btn_w, btn_h)
                img = img.resize((size, size), Image.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.button.config(image=self.icon_photo, text='', compound=tk.CENTER)
                return
            except Exception as e:
                print(f"Ошибка загрузки иконки {icon_path}: {e}")
                self.icon_photo = None

        self.icon_photo = None
        self.button.config(image='', text=self.data["text"])

    def update_style(self):
        self.update_icon_and_text()
        self.button.config(
            bg=self.data["color"],
            fg=self.data["text_color"],
            font=(self.data["font_family"], self.data["font_size"], self.data["font_style"])
        )
        
        # При обновлении стиля (например, после редактирования), убедимся, что координаты 
        # также привязаны к сетке, если это настройка кнопки.
        snap_enabled = self.data.get('snap_to_grid', True)
        grid_x = self.data.get('grid_size_x', 10) if snap_enabled else 1
        grid_y = self.data.get('grid_size_y', 10) if snap_enabled else 1

        if snap_enabled and grid_x > 0 and grid_y > 0:
            x = round(self.data['x'] / grid_x) * grid_x
            y = round(self.data['y'] / grid_y) * grid_y
            
            self.data['x'] = x
            self.data['y'] = y
            self.canvas.coords(self.canvas_item, x, y)
        else:
            self.canvas.coords(self.canvas_item, self.data['x'], self.data['y'])
            
        self.canvas.itemconfig(self.canvas_item, width=self.data['width'], height=self.data['height'])
        self.update_edit_visibility()

    def update_edit_visibility(self):
        if hasattr(self, '_resize_handle'):
            if self.app.edit_mode_active.get():
                self._resize_handle.place(relx=1.0, rely=1.0, anchor=tk.SE)
                self.button.config(cursor="fleur")
            else:
                self._resize_handle.place_forget()
                self.button.config(cursor="")

    def destroy(self):
        self.canvas.delete(self.canvas_item)
        self.button.destroy()


# --- Класс ButtonTabManager (с изменениями для интеграции FloatingWidget) ---

class ButtonTabManager:
    def __init__(self, app):
        self.app = app

    def toggle_edit_mode(self):
        """Вспомогательный метод для обновления видимости кнопок в режиме редактирования."""
        for widget in self.app.active_button_widgets.values():
            widget.update_edit_visibility()

    def create_tab_dialog(self):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Создание вкладки")
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()

        tk.Label(dialog, text="Название вкладки:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        tab_name_entry = tk.Entry(dialog)
        tab_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        tab_name_entry.focus_set()

        def add_tab():
            tab_name = tab_name_entry.get().strip()
            if tab_name and tab_name not in [data['name'] for data in self.app.tabs.values()]:
                tab_id = str(uuid.uuid4())
                self.app.tabs[tab_id] = {
                    "name": tab_name, 
                    "buttons": {},
                    "snap_to_grid": True, # Дефолтные настройки для новых вкладок
                    "grid_size_x": 10,
                    "grid_size_y": 10
                }
                self.app.update_tab_display()
                self.app.selected_tab_id = tab_id
                self.app.switch_tab(tab_id)
                self.app.save_config(show_message=False)
                # Если плавающий виджет открыт, обновляем его данные
                if self.app.floating_widget_instance and self.app.floating_widget_instance.winfo_exists():
                    self.app.floating_widget_instance.update_widget_buttons()
                dialog.destroy()
            elif not tab_name:
                self.app._show_messagebox("warning", "Предупреждение", "Название вкладки не может быть пустым.")
            else:
                self.app._show_messagebox("warning", "Предупреждение", "Вкладка с таким названием уже существует.")

        tk.Button(dialog, text="Создать", command=add_tab).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        dialog.bind("<Return>", lambda event: add_tab())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.columnconfigure(1, weight=1)
        dialog.wait_window()

    def update_tab_display(self):
        # Очищаем старые виджеты
        for frame in self.app.column_frames:
            frame.destroy()
        self.app.column_frames = []
        self.app.tab_widgets = {}
        self.app.active_button_widgets = {}

        if not self.app.tabs:
            return

        # Создаем новый главный фрейм для вкладки
        column_frame = tk.Frame(self.app.tabs_pane, bg="#e0e0e0")
        self.app.tabs_pane.add(column_frame)
        self.app.column_frames.append(column_frame)

        tab_buttons_frame = tk.Frame(column_frame, bg="#e0e0e0")
        tab_buttons_frame.pack(side=tk.TOP, fill=tk.X)

        # ДОБАВЛЯЕМ КНОПКУ ДЛЯ ВЫЗОВА ПЛАВАЮЩЕГО ВИДЖЕТА ЗДЕСЬ
        self.app.floating_widget_trigger_button = tk.Button(tab_buttons_frame, text="🌐", 
                                                            command=self.app.toggle_floating_widget,
                                                            relief=tk.FLAT, bg="#c0c0c0")
        self.app.floating_widget_trigger_button.pack(side=tk.RIGHT, padx=5, pady=2)
        # КОНЕЦ ДОБАВЛЕНИЯ

        # Создаем Canvas для кнопок в каждой вкладке
        buttons_canvas = tk.Canvas(column_frame, bg="#f0f0f0", highlightthickness=0)
        buttons_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        for tab_id, tab_data in self.app.tabs.items():
            tab_button = tk.Button(tab_buttons_frame, text=tab_data["name"],
                                   command=lambda tid=tab_id: self.app.switch_tab(tid),
                                   bg="#d0d0d0")
            tab_button.pack(side=tk.LEFT, padx=2, pady=2)
            tab_button.bind("<Button-3>", lambda event, tid=tab_id: self.app.show_tab_context_menu(event, tid))
            self.app.tab_widgets[tab_id] = {"button": tab_button, "buttons_canvas": buttons_canvas}

        if self.app.selected_tab_id and self.app.selected_tab_id in self.app.tabs:
            self.app.switch_tab(self.app.selected_tab_id)
        elif self.app.tabs:
            first_tab_id = list(self.app.tabs.keys())[0]
            self.app.switch_tab(first_tab_id)

    def switch_tab(self, tab_id):
        # Уничтожаем виджеты кнопок на старой вкладке
        for widget in self.app.active_button_widgets.values():
            widget.destroy()
        self.app.active_button_widgets = {}

        if self.app.selected_tab_id and self.app.selected_tab_id in self.app.tab_widgets:
            self.app.tab_widgets[self.app.selected_tab_id]["button"].config(relief=tk.RAISED, bg="#d0d0d0")

        self.app.selected_tab_id = tab_id
        self.app.tab_widgets[self.app.selected_tab_id]["button"].config(relief=tk.SUNKEN, bg="#a0a0a0")

        current_buttons_canvas = self.app.tab_widgets[self.app.selected_tab_id]["buttons_canvas"]

        # Получаем настройки сетки для текущей вкладки (с дефолтами, если не заданы)
        tab_settings = self.app.tabs[tab_id]
        tab_snap_to_grid = tab_settings.get('snap_to_grid', True)
        tab_grid_size_x = tab_settings.get('grid_size_x', 10)
        tab_grid_size_y = tab_settings.get('grid_size_y', 10)

        for button_id, button_data in self.app.tabs[tab_id]["buttons"].items():
            # Если у кнопки нет собственных настроек сетки, используем настройки вкладки
            button_data.setdefault('snap_to_grid', tab_snap_to_grid)
            button_data.setdefault('grid_size_x', tab_grid_size_x)
            button_data.setdefault('grid_size_y', tab_grid_size_y)
            widget = ButtonWidget(self.app, self, current_buttons_canvas, tab_id, button_id, button_data)
            self.app.active_button_widgets[button_id] = widget

        # Переключаемся в режим редактирования при смене вкладки, если он был активен
        if self.app.edit_mode_active.get():
            self.app.toggle_edit_mode() # Повторный вызов просто обновит режим, не меняя его состояния
        else:
            # Если мы не в режиме редактирования, просто обновляем видимость
            for widget in self.app.active_button_widgets.values():
                widget.update_edit_visibility()
                
        # Обновляем скролл
        current_buttons_canvas.update_idletasks()
        current_buttons_canvas.config(scrollregion=current_buttons_canvas.bbox("all"))


    def show_tab_context_menu(self, event, tab_id):
        context_menu = tk.Menu(self.app.master, tearoff=0)
        
        # Использование нового названия
        context_menu.add_command(label="Настройки вкладки", command=lambda: self.app.settings_tab_dialog(tab_id))
        context_menu.add_command(label="Удалить вкладку", command=lambda: self.app.delete_tab_dialog(tab_id))
        context_menu.add_separator()
        context_menu.add_command(label="Создать кнопку", command=lambda: self.app.create_button_dialog(initial_tab_id=tab_id))
        context_menu.tk_popup(event.x_root, event.y_root)

    def settings_tab_dialog(self, tab_id):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Настройки вкладки") # Изменение заголовка
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()

        current_data = self.app.tabs[tab_id]
        current_name = current_data["name"]
        
        # --- Основные настройки (Переименование) ---
        row = 0
        tk.Label(dialog, text="Название вкладки:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        name_entry = tk.Entry(dialog)
        name_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        name_entry.insert(0, current_name)
        name_entry.focus_set()
        row += 1
        
        # --- Настройки Сетки (Grid Settings) ---
        grid_frame = tk.LabelFrame(dialog, text="Настройки привязки к сетке для этой вкладки")
        grid_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky=tk.EW)
        row += 1
        
        # Дефолтные значения для настроек сетки, если их нет в current_data
        snap_var = tk.BooleanVar(value=current_data.get('snap_to_grid', True))
        grid_size_x_var = tk.IntVar(value=current_data.get('grid_size_x', 10))
        grid_size_y_var = tk.IntVar(value=current_data.get('grid_size_y', 10))
        
        tk.Checkbutton(grid_frame, text="Включить привязку к сетке", variable=snap_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        tk.Label(grid_frame, text="Размер ячейки X:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        tk.Spinbox(grid_frame, from_=1, to_=100, textvariable=grid_size_x_var, width=5).grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        tk.Label(grid_frame, text="Размер ячейки Y:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        tk.Spinbox(grid_frame, from_=1, to_=100, textvariable=grid_size_y_var, width=5).grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        
        # --- Действия ---
        
        def perform_settings_update():
            new_name = name_entry.get().strip()
            
            if not new_name:
                self.app._show_messagebox("warning", "Предупреждение", "Название вкладки не может быть пустым.")
                return
            
            if new_name != current_name and new_name in [data['name'] for tid, data in self.app.tabs.items() if tid != tab_id]:
                self.app._show_messagebox("warning", "Предупреждение", "Вкладка с таким названием уже существует.")
                return
                
            # Обновление имени
            current_data["name"] = new_name
            
            # Обновление настроек сетки
            current_data['snap_to_grid'] = snap_var.get()
            current_data['grid_size_x'] = grid_size_x_var.get()
            current_data['grid_size_y'] = grid_size_y_var.get()
            
            self.app.update_tab_display() # Это заново создаст виджеты кнопок и применит новые настройки сетки
            self.app.save_config(show_message=False)
            
            # Если плавающий виджет открыт, обновляем его данные
            if self.app.floating_widget_instance and self.app.floating_widget_instance.winfo_exists():
                self.app.floating_widget_instance.update_widget_buttons()

            dialog.destroy()

        tk.Button(dialog, text="Сохранить настройки", command=perform_settings_update).grid(row=row, column=0, columnspan=2, padx=5, pady=10)
        
        dialog.bind("<Return>", lambda event: perform_settings_update())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.columnconfigure(1, weight=1)
        dialog.wait_window()

    def delete_tab_dialog(self, tab_id):
        if self.app._show_messagebox("askyesno", "Удаление вкладки", f"Вы уверены, что хотите удалить вкладку '{self.app.tabs[tab_id]['name']}' и все ее кнопки?"):
            del self.app.tabs[tab_id]
            self.app.selected_tab_id = None
            self.app.update_tab_display()
            self.app.save_config(show_message=False)
            
            # Если плавающий виджет открыт, обновляем его данные
            if self.app.floating_widget_instance and self.app.floating_widget_instance.winfo_exists():
                self.app.floating_widget_instance.update_widget_buttons()


    def create_button_dialog(self, initial_tab_id=None):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Создание кнопки")
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()

        tab_names = [data["name"] for data in self.app.tabs.values()]
        tab_ids_map = {data["name"]: tid for tid, data in self.app.tabs.items()}

        tk.Label(dialog, text="Вкладка:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        tab_name_var = tk.StringVar()
        tab_combo = ttk.Combobox(dialog, textvariable=tab_name_var, values=tab_names, state="readonly")
        tab_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        current_tab_id = initial_tab_id or self.app.selected_tab_id
        if current_tab_id and current_tab_id in self.app.tabs:
            tab_name_var.set(self.app.tabs[current_tab_id]["name"])
        elif tab_names:
            tab_name_var.set(tab_names[0])
        else:
            self.app._show_messagebox("warning", "Предупреждение", "Для создания кнопки сначала создайте вкладку.")
            dialog.destroy()
            return

        row = 1
        tk.Label(dialog, text="Текст кнопки:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        button_text_entry = tk.Entry(dialog)
        button_text_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        button_text_entry.focus_set()
        row += 1

        tk.Label(dialog, text="Текст для вывода:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.NW)
        
        output_text_frame = tk.Frame(dialog)
        output_text_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)

        output_text_entry = tk.Text(output_text_frame, wrap=tk.WORD, height=5, width=40)
        output_text_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        output_text_scrollbar = tk.Scrollbar(output_text_frame, command=output_text_entry.yview)
        output_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text_entry.config(yscrollcommand=output_text_scrollbar.set)
        
        row += 1

        tk.Label(dialog, text="Путь к иконке:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        icon_var = tk.StringVar(value="")
        icon_entry = tk.Entry(dialog, textvariable=icon_var)
        icon_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        tk.Button(dialog, text="Обзор...", command=lambda: self.app._choose_image(icon_var)).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Цвет кнопки:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        color_var = tk.StringVar(value=self.app.default_button_color)
        color_entry = tk.Entry(dialog, textvariable=color_var)
        color_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        tk.Button(dialog, text="Выбрать цвет", command=lambda: self.app._choose_color(color_var)).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Цвет текста:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        text_color_var = tk.StringVar(value="black")
        text_color_entry = tk.Entry(dialog, textvariable=text_color_var)
        text_color_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        tk.Button(dialog, text="Выбрать цвет", command=lambda: self.app._choose_color(text_color_var)).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Размер шрифта:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        font_size_var = tk.IntVar(value=10)
        font_size_spinbox = tk.Spinbox(dialog, from_=8, to_=72, textvariable=font_size_var)
        font_size_spinbox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        tk.Label(dialog, text="Шрифт:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        font_family_var = tk.StringVar(value="Arial")
        font_family_combobox = ttk.Combobox(dialog, textvariable=font_family_var, values=sorted(tkFont.families()), state="readonly")
        font_family_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        font_family_combobox.set("Arial")
        row += 1

        tk.Label(dialog, text="Стиль шрифта:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        font_style_var = tk.StringVar(value="")
        font_style_combobox = ttk.Combobox(dialog, textvariable=font_style_var, values=["", "bold", "italic", "bold italic"], state="readonly")
        font_style_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        new_line_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dialog, text="Вставить с новой строки", variable=new_line_var).grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        row += 1

        clear_text_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dialog, text="Стирать текст перед вставкой", variable=clear_text_var).grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        row += 1
        
        # Добавляем настройки сетки для кнопки (по умолчанию наследуются от вкладки)
        grid_create_frame = tk.LabelFrame(dialog, text="Настройки привязки (по умолчанию: настройки вкладки)")
        grid_create_frame.grid(row=row, column=0, columnspan=3, padx=10, pady=5, sticky=tk.EW)
        row += 1
        
        # Получаем дефолтные настройки сетки из выбранной вкладки
        if current_tab_id and current_tab_id in self.app.tabs:
            tab_settings = self.app.tabs[current_tab_id]
            default_snap = tab_settings.get('snap_to_grid', True)
            default_grid_x = tab_settings.get('grid_size_x', 10)
            default_grid_y = tab_settings.get('grid_size_y', 10)
        else: # Fallback, если вкладка не выбрана или не имеет настроек
            default_snap = True
            default_grid_x = 10
            default_grid_y = 10

        snap_create_var = tk.BooleanVar(value=default_snap) 
        grid_size_x_create_var = tk.IntVar(value=default_grid_x)
        grid_size_y_create_var = tk.IntVar(value=default_grid_y)
        
        tk.Checkbutton(grid_create_frame, text="Привязка к сетке", variable=snap_create_var).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        tk.Label(grid_create_frame, text="Размер ячейки X:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        tk.Spinbox(grid_create_frame, from_=1, to_=100, textvariable=grid_size_x_create_var, width=5).grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(grid_create_frame, text="Размер ячейки Y:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        tk.Spinbox(grid_create_frame, from_=1, to_=100, textvariable=grid_size_y_create_var, width=5).grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)


        def add_button():
            selected_tab_name = tab_name_var.get()
            if not selected_tab_name:
                self.app._show_messagebox("warning", "Предупреждение", "Пожалуйста, выберите вкладку.")
                return

            tab_id = tab_ids_map.get(selected_tab_name)
            if not tab_id:
                self.app._show_messagebox("error", "Ошибка", "Не удалось найти выбранную вкладку.")
                return

            button_text = button_text_entry.get().strip()
            # Получаем текст из tk.Text виджета, исключая неявную последнюю новую строку Tkinter'а
            output_text = output_text_entry.get("1.0", "end-1c") 

            if not button_text and not icon_var.get():
                self.app._show_messagebox("warning", "Предупреждение", "Кнопка должна иметь текст или иконку.")
                return

            button_id = str(uuid.uuid4())
            self.app.tabs[tab_id]["buttons"][button_id] = {
                "text": button_text,
                "output": output_text,
                "color": color_var.get(),
                "text_color": text_color_var.get(),
                "font_size": font_size_var.get(),
                "font_family": font_family_combobox.get(),
                "font_style": font_style_combobox.get(),
                "new_line": new_line_var.get(),
                "clear_text": clear_text_var.get(),
                "icon": icon_var.get(),
                "x": 10, "y": 10, "width": 100, "height": 30,
                "snap_to_grid": snap_create_var.get(),
                "grid_size_x": grid_size_x_create_var.get(),
                "grid_size_y": grid_size_y_create_var.get()
            }
            self.app.switch_tab(tab_id)
            self.app.save_config(show_message=False)
            
            # Если плавающий виджет открыт, обновляем его данные
            if self.app.floating_widget_instance and self.app.floating_widget_instance.winfo_exists():
                self.app.floating_widget_instance.update_widget_buttons()

            dialog.destroy()

        tk.Button(dialog, text="Создать", command=add_button).grid(row=row, column=0, columnspan=3, padx=5, pady=5)
        
        dialog.bind("<Control-Return>", lambda event: add_button())
        dialog.bind("<Control-KP_Enter>", lambda event: add_button())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.columnconfigure(1, weight=1)
        dialog.wait_window()

    def _on_button_click_internal(self, tab_id, button_id):
        button_data = self.app.tabs[tab_id]["buttons"].get(button_id)
        if button_data:
            # Получаем output_text "как есть" из button_data 
            output_text = button_data.get("output", "") 

            # Копируем в буфер обмена
            self.app.master.clipboard_clear()
            self.app.master.clipboard_append(output_text)

            text_area = self.app.text_area
            
            if button_data.get("clear_text"):
                text_area.delete("1.0", tk.END)
                insert_position = tk.END
            else:
                insert_position = tk.INSERT
            
            final_text_to_insert = output_text

            if button_data.get("new_line"):
                # Если 'new_line' true, убедимся, что текст заканчивается ровно одной новой строкой.
                if not final_text_to_insert.endswith('\n'):
                    final_text_to_insert += "\n"
            else:
                # Если 'new_line' false, убедимся, что текст НЕ заканчивается новой строкой.
                if final_text_to_insert.endswith('\n'):
                    final_text_to_insert = final_text_to_insert[:-1]

            text_area.insert(insert_position, final_text_to_insert)
            
            # Настраиваем видимость курсора
            text_area.see(tk.INSERT)


    def show_button_context_menu(self, event, tab_id, button_id):
        context_menu = tk.Menu(self.app.master, tearoff=0)
        context_menu.add_command(label="Изменить кнопку", command=lambda: self.app.edit_button_dialog(tab_id, button_id))
        context_menu.add_command(label="Удалить кнопку", command=lambda: self.app.delete_button_dialog(tab_id, button_id))
        context_menu.tk_popup(event.x_root, event.y_root)

    def edit_button_dialog(self, tab_id, button_id):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Редактировать кнопку")
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()

        button_data = self.app.tabs[tab_id]["buttons"][button_id]

        row = 0
        tk.Label(dialog, text="Текст кнопки:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        button_text_entry = tk.Entry(dialog)
        button_text_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        button_text_entry.insert(0, button_data["text"])
        button_text_entry.focus_set()
        row += 1

        tk.Label(dialog, text="Текст для вывода:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.NW)

        output_text_frame = tk.Frame(dialog)
        output_text_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)

        output_text_entry = tk.Text(output_text_frame, wrap=tk.WORD, height=5, width=40)
        output_text_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        output_text_scrollbar = tk.Scrollbar(output_text_frame, command=output_text_entry.yview)
        output_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text_entry.config(yscrollcommand=output_text_scrollbar.set)
        
        # Вставляем существующий текст, не изменяя конечные пробелы/новые строки
        output_text_entry.insert("1.0", button_data.get("output", ""))
        row += 1

        tk.Label(dialog, text="Путь к иконке:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        icon_var = tk.StringVar(value=button_data.get("icon", ""))
        icon_entry = tk.Entry(dialog, textvariable=icon_var)
        icon_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        tk.Button(dialog, text="Обзор...", command=lambda: self.app._choose_image(icon_var)).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Цвет кнопки:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        color_var = tk.StringVar(value=button_data.get("color", self.app.default_button_color))
        color_entry = tk.Entry(dialog, textvariable=color_var)
        color_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        tk.Button(dialog, text="Выбрать цвет", command=lambda: self.app._choose_color(color_var)).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Цвет текста:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        text_color_var = tk.StringVar(value=button_data.get("text_color", "black"))
        text_color_entry = tk.Entry(dialog, textvariable=text_color_var)
        text_color_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        tk.Button(dialog, text="Выбрать цвет", command=lambda: self.app._choose_color(text_color_var)).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Размер шрифта:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        font_size_var = tk.IntVar(value=button_data.get("font_size", 10))
        font_size_spinbox = tk.Spinbox(dialog, from_=8, to_=72, textvariable=font_size_var)
        font_size_spinbox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        tk.Label(dialog, text="Шрифт:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        font_family_var = tk.StringVar(value=button_data.get("font_family", "Arial"))
        font_family_combobox = ttk.Combobox(dialog, textvariable=font_family_var, values=sorted(tkFont.families()), state="readonly")
        font_family_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        if button_data.get("font_family") in sorted(tkFont.families()):
            font_family_combobox.set(button_data.get("font_family", "Arial"))
        else:
            font_family_combobox.set("Arial")
        row += 1

        tk.Label(dialog, text="Стиль шрифта:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        font_style_var = tk.StringVar(value=button_data.get("font_style", ""))
        font_style_combobox = ttk.Combobox(dialog, textvariable=font_style_var, values=["", "bold", "italic", "bold italic"], state="readonly")
        font_style_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        new_line_var = tk.BooleanVar(value=button_data.get("new_line", False))
        tk.Checkbutton(dialog, text="Вставить с новой строки", variable=new_line_var).grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        row += 1

        clear_text_var = tk.BooleanVar(value=button_data.get("clear_text", False))
        tk.Checkbutton(dialog, text="Стирать текст перед вставкой", variable=clear_text_var).grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        row += 1
        
        # Настройки сетки для редактирования
        grid_edit_frame = tk.LabelFrame(dialog, text="Настройки привязки")
        grid_edit_frame.grid(row=row, column=0, columnspan=3, padx=10, pady=5, sticky=tk.EW)
        row += 1
        
        snap_edit_var = tk.BooleanVar(value=button_data.get('snap_to_grid', True))
        grid_size_x_edit_var = tk.IntVar(value=button_data.get('grid_size_x', 10))
        grid_size_y_edit_var = tk.IntVar(value=button_data.get('grid_size_y', 10))
        
        tk.Checkbutton(grid_edit_frame, text="Привязка к сетке", variable=snap_edit_var).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        tk.Label(grid_edit_frame, text="Размер ячейки X:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        tk.Spinbox(grid_edit_frame, from_=1, to_=100, textvariable=grid_size_x_edit_var, width=5).grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(grid_edit_frame, text="Размер ячейки Y:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        tk.Spinbox(grid_edit_frame, from_=1, to_=100, textvariable=grid_size_y_edit_var, width=5).grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)


        def apply_changes():
            new_text = button_text_entry.get().strip()
            new_icon = icon_var.get()

            if not new_text and not new_icon:
                self.app._show_messagebox("warning", "Предупреждение", "Кнопка должна иметь текст или иконку.")
                return

            button_data["text"] = new_text
            # Получаем текст из tk.Text виджета, исключая неявную последнюю новую строку Tkinter'а
            button_data["output"] = output_text_entry.get("1.0", "end-1c")
            button_data["icon"] = new_icon
            button_data["color"] = color_var.get()
            button_data["text_color"] = text_color_var.get()
            button_data["font_size"] = font_size_var.get()
            button_data["font_family"] = font_family_combobox.get()
            button_data["font_style"] = font_style_combobox.get()
            button_data["new_line"] = new_line_var.get()
            button_data["clear_text"] = clear_text_var.get()
            
            # Обновление настроек сетки
            button_data["snap_to_grid"] = snap_edit_var.get()
            button_data["grid_size_x"] = grid_size_x_edit_var.get()
            button_data["grid_size_y"] = grid_size_y_edit_var.get()

            if button_id in self.app.active_button_widgets:
                self.app.active_button_widgets[button_id].update_style()

            self.app.save_config(show_message=False)

            # Если плавающий виджет открыт, обновляем его данные
            if self.app.floating_widget_instance and self.app.floating_widget_instance.winfo_exists():
                self.app.floating_widget_instance.update_widget_buttons()
                
            dialog.destroy()

        tk.Button(dialog, text="Применить", command=apply_changes).grid(row=row, column=0, columnspan=3, padx=5, pady=5)
        
        dialog.bind("<Control-Return>", lambda event: apply_changes())
        dialog.bind("<Control-KP_Enter>", lambda event: apply_changes())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.columnconfigure(1, weight=1)
        dialog.wait_window()

    def delete_button_dialog(self, tab_id, button_id):
        if tab_id in self.app.tabs and button_id in self.app.tabs[tab_id]["buttons"]:
            button_name = self.app.tabs[tab_id]["buttons"][button_id]['text']
        else:
            button_name = "Неизвестная кнопка"
            
        if self.app._show_messagebox("askyesno", "Удаление кнопки", f"Вы уверены, что хотите удалить кнопку '{button_name}'?"):

            if button_id in self.app.active_button_widgets:
                self.app.active_button_widgets[button_id].destroy()
                del self.app.active_button_widgets[button_id]

            del self.app.tabs[tab_id]["buttons"][button_id]
            self.app.save_config(show_message=False)
            
            # Если плавающий виджет открыт, обновляем его данные
            if self.app.floating_widget_instance and self.app.floating_widget_instance.winfo_exists():
                self.app.floating_widget_instance.update_widget_buttons()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

