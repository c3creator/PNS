
# floating_widget.py
import tkinter as tk
from tkinter import ttk
import os
import json
import uuid

# Попытка импортировать Pillow компоненты
try:
    from PIL import Image, ImageTk
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("Pillow не установлен. Функции работы с изображениями будут отключены.")

class FloatingWidget(tk.Toplevel):
    """
    Виджет, отображающийся поверх всех окон, с вкладками кнопок в виде контекстных меню.
    """
    CONFIG_FILE = "floating_widget_config.json" # Файл для сохранения положения и размера виджета
    
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.app = app_instance # Ссылка на главный экземпляр приложения
        self.tabs_data = {} # Будет хранить копию данных вкладок из основного приложения
        self.filtered_buttons = {} # Отфильтрованные кнопки для отображения
        self.after_id = None # Для задержки обработки ввода в фильтре
        
        self.title("Floating Buttons Widget")
        self.overrideredirect(True) # Убирает заголовок окна
        self.attributes("-topmost", True) # Делает окно всегда поверх других

        # Устанавливаем размеры и позицию по умолчанию
        self.width = 300
        self.height = 400
        self.x = 100
        self.y = 100
        
        self.load_state() # Загружаем сохраненные положение и размер
        self.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")

        self.create_widgets()
        self.bind_drag_and_resize()
        self.update_widget_buttons() # Изначальная загрузка кнопок

        # Убедимся, что основное приложение знает об этом экземпляре
        self.app.floating_widget_instance = self
        
        # Обработка закрытия основного окна
        self.master.protocol("WM_DELETE_WINDOW", self.on_master_close)

    def on_master_close(self):
        """Обрабатывает закрытие основного окна приложения."""
        self.destroy()
        self.app.master.destroy() # Закрывает также и основное приложение

    def create_widgets(self):
        # Верхний фрейм управления (закрыть, обновить, фильтр)
        self.control_frame = tk.Frame(self, bg="#333", relief=tk.RAISED, bd=1)
        self.control_frame.pack(side=tk.TOP, fill=tk.X)

        # Кнопка закрытия (справа)
        self.close_button = tk.Button(self.control_frame, text="✖", command=self.destroy,
                                      font=("Arial", 10), bg="#ff6666", fg="white", relief=tk.FLAT)
        self.close_button.pack(side=tk.RIGHT, padx=2, pady=2)

        # Кнопка обновления (справа, рядом с кнопкой закрытия)
        self.refresh_button = tk.Button(self.control_frame, text="↻", command=self.update_widget_buttons,
                                       font=("Arial", 10), bg="#666", fg="white", relief=tk.FLAT)
        self.refresh_button.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # Поле для фильтра (слева во фрейме управления)
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(self.control_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        self.filter_entry.bind("<KeyRelease>", self.debounce_filter) # Задержка для фильтра

        # Кнопка, которая будет открывать основное меню с вкладками
        self.open_tabs_button = tk.Button(self, text="Открыть меню вкладок", command=self.show_main_tabs_menu,
                                         bg="#555", fg="white", relief=tk.FLAT)
        self.open_tabs_button.pack(pady=10) # Располагаем по центру
        
        # Нижний правый угол для изменения размера
        self.resize_grip = tk.Frame(self, bg="#777", width=12, height=12, cursor="sizing")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor=tk.SE)
        self.resize_grip.bind("<Button-1>", self._on_resize_start)
        self.resize_grip.bind("<B1-Motion>", self._on_resize_motion)
        self.resize_grip.bind("<ButtonRelease-1>", self._on_resize_end)

    def debounce_filter(self, event=None):
        """Задерживает вызов apply_filter для улучшения производительности."""
        if self.after_id:
            self.after_cancel(self.after_id)
        self.after_id = self.after(300, self.apply_filter) # Ждем 300мс после последнего нажатия клавиши

    def apply_filter(self):
        """Применяет фильтр к кнопкам на основе введенного текста."""
        search_term = self.filter_var.get().lower().strip()
        self.filtered_buttons = {}

        if not search_term:
            # Если нет поискового запроса, показываем все кнопки
            self.filtered_buttons = {tid: tab_data["buttons"] for tid, tab_data in self.tabs_data.items()}
        else:
            for tab_id, tab_data in self.tabs_data.items():
                filtered_tab_buttons = {}
                for button_id, button_data in tab_data["buttons"].items():
                    # Фильтруем по тексту кнопки или по тексту вывода
                    if search_term in button_data.get("text", "").lower() or \
                       search_term in button_data.get("output", "").lower():
                        filtered_tab_buttons[button_id] = button_data
                if filtered_tab_buttons:
                    self.filtered_buttons[tab_id] = filtered_tab_buttons
        
        self.after_id = None # Сбрасываем ID задержки

    def update_widget_buttons(self):
        """Загружает данные кнопок из основного приложения и применяет фильтр."""
        # Делаем глубокую копию, чтобы избежать прямого изменения app.tabs во время фильтрации
        self.tabs_data = {
            tid: {
                "name": tdata["name"],
                "buttons": {bid: {k: v for k, v in bdata.items()} for bid, bdata in tdata["buttons"].items()}
            }
            for tid, tdata in self.app.tabs.items()
        }
        self.apply_filter() # Повторно применяем фильтр к новым данным

    def show_main_tabs_menu(self):
        """Открывает первое контекстное меню с названиями вкладок."""
        main_menu = tk.Menu(self, tearoff=0)
        
        # Показываем только те вкладки, у которых есть отфильтрованные кнопки
        visible_tab_ids = [tid for tid in self.tabs_data if tid in self.filtered_buttons and self.filtered_buttons[tid]]
        
        if not visible_tab_ids:
            main_menu.add_command(label="Кнопок не найдено или отфильтровано.")
        else:
            for tab_id in visible_tab_ids:
                tab_name = self.tabs_data[tab_id]["name"]
                # Создаем каскадное меню для каждой вкладки
                tab_cascade_menu = tk.Menu(main_menu, tearoff=0)
                
                # Добавляем кнопки в каскадное меню
                tab_buttons = self.filtered_buttons.get(tab_id, {})
                if not tab_buttons:
                    tab_cascade_menu.add_command(label="В этой вкладке нет кнопок.")
                else:
                    for button_id in tab_buttons:
                        button_data = tab_buttons[button_id]
                        text = button_data.get("text", f"Кнопка {button_id[:4]}")
                        tab_cascade_menu.add_command(label=text, command=lambda bd=button_data: self._on_button_click(bd))
                
                main_menu.add_cascade(label=tab_name, menu=tab_cascade_menu)

        # Позиционируем меню относительно кнопки "Open Tabs Menu"
        self.update_idletasks() # Убедимся, что геометрия кнопки актуальна
        btn_x = self.open_tabs_button.winfo_rootx()
        btn_y = self.open_tabs_button.winfo_rooty() + self.open_tabs_button.winfo_height()
        main_menu.tk_popup(btn_x, btn_y)

    def _on_button_click(self, button_data):
        """Копирует текст из кнопки в буфер обмена."""
        output_text = button_data.get("output", "")
        self.clipboard_clear()
        self.clipboard_append(output_text)
        
        # Опционально: можно добавить всплывающее уведомление о копировании
        # print(f"Copied: {output_text}")

    # --- Перемещение окна ---
    def bind_drag_and_resize(self):
        # Разрешаем перетаскивание из фрейма управления
        self.control_frame.bind("<Button-1>", self._on_drag_start)
        self.control_frame.bind("<B1-Motion>", self._on_drag_motion)
        self.control_frame.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Также разрешаем перетаскивание из основного окна, если не кликаем на другие виджеты
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)

    def _on_drag_start(self, event):
        self._drag_data = {"x": event.x_root, "y": event.y_root}
        self.x = self.winfo_x()
        self.y = self.winfo_y()
        return "break" # Предотвращаем распространение события на другие виджеты

    def _on_drag_motion(self, event):
        delta_x = event.x_root - self._drag_data["x"]
        delta_y = event.y_root - self._drag_data["y"]
        new_x = self.x + delta_x
        new_y = self.y + delta_y
        self.geometry(f"+{new_x}+{new_y}")
        return "break"

    def _on_drag_end(self, event):
        self.x = self.winfo_x()
        self.y = self.winfo_y()
        self.save_state()
        self._drag_data = None
        return "break"

    # --- Изменение размера окна ---
    def _on_resize_start(self, event):
        self._resize_data = {"x": event.x_root, "y": event.y_root,
                             "width": self.winfo_width(), "height": self.winfo_height()}
        return "break" # Предотвращаем событие перетаскивания, если нажата ручка изменения размера

    def _on_resize_motion(self, event):
        delta_x = event.x_root - self._resize_data["x"]
        delta_y = event.y_root - self._resize_data["y"]

        new_width = max(150, self._resize_data["width"] + delta_x)
        new_height = max(100, self._resize_data["height"] + delta_y)

        self.geometry(f"{new_width}x{new_height}")
        self.width = new_width
        self.height = new_height
        return "break"

    def _on_resize_end(self, event):
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.save_state()
        self._resize_data = None
        return "break"

    def save_state(self):
        """Сохраняет текущее положение и размер окна в JSON-файл."""
        config_data = {
            "x": self.winfo_x(),
            "y": self.winfo_y(),
            "width": self.winfo_width(),
            "height": self.winfo_height()
        }
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(config_data, f)
        except Exception as e:
            print(f"Ошибка сохранения состояния плавающего виджета: {e}")

    def load_state(self):
        """Загружает положение и размер окна из JSON-файла."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    config_data = json.load(f)
                    self.x = config_data.get("x", self.x)
                    self.y = config_data.get("y", self.y)
                    self.width = config_data.get("width", self.width)
                    self.height = config_data.get("height", self.height)
            except Exception as e:
                print(f"Ошибка загрузки состояния плавающего виджета: {e}")

    def destroy(self):
        """Переопределяет destroy для корректной очистки и сохранения состояния."""
        self.save_state()
        # Удаляем ссылку в основном приложении
        if hasattr(self.app, 'floating_widget_instance') and self.app.floating_widget_instance is self:
            self.app.floating_widget_instance = None
        super().destroy()

