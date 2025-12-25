
# pnsc_main.py

from pnsc_utils import tk, ttk, filedialog, messagebox, colorchooser, uuid, os, json, time, datetime, tkFont, Image, ImageTk, HAS_PILLOW, CONTROL_ICONS
from module_notes import NoteWidget, NoteManager
from module_buttons_tabs import ButtonWidget, ButtonTabManager
from module_timers_worktable import TimerWorkTableManager

# Импортируем плавающий виджет
try:
    from floating_widget import FloatingWidget
except ImportError:
    print("Модуль floating_widget не найден. Плавающий виджет будет недоступен.")
    FloatingWidget = None

class PNSc:
    def __init__(self, master):
        self.master = master
        master.title("PNS - Personal Note System")
        master.geometry("1366x768")
        master.configure(bg="#f0f0f0")

        if HAS_PILLOW:
            app_icon_path_png = CONTROL_ICONS.get("main_app_icon_png")
            if app_icon_path_png and os.path.exists(app_icon_path_png):
                try:
                    img = Image.open(app_icon_path_png)
                    photo = ImageTk.PhotoImage(img)
                    self.master.iconphoto(True, photo)
                except Exception as e:
                    print(f"Ошибка загрузки PNG иконки приложения: {e}")
                    self._load_ico_icon()
            else:
                self._load_ico_icon()
        else:
            self._load_ico_icon()

        self.config_dir = "configs"
        self.current_config_path = None
        self.current_config_name = None
        self.tabs = {}
        self.notes = {}
        self.selected_tab_id = None
        self.default_button_color = "SystemButtonFace"
        self.active_button_widgets = {} 
        self.global_author = "" 
        self.show_dialogs_var = tk.BooleanVar(value=True)
        self.edit_mode_active = tk.BooleanVar(value=False)
        self.control_icons = {}
        
        # Экземпляр плавающего виджета
        self.floating_widget_instance = None

        # --- ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРОВ (МИКСИНОВ) ---
        self._setup_managers()

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        self._load_control_icons()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- GUI SETUP ---
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_main_layout()
        self._setup_tab_control_panel()
        self._setup_bottom_panel()
        
        # --- Инициализация данных ---
        self.device_types = []
        self.work_types = []
        self.active_timers = {}
        self.completed_jobs = []
        self.work_table_tree = None

        self.update_tab_display()
        self.load_default_config_if_needed()
        
    def _load_ico_icon(self):
        app_icon_path_ico = CONTROL_ICONS.get("main_app_icon_ico")
        if app_icon_path_ico and os.path.exists(app_icon_path_ico):
            try:
                self.master.iconbitmap(app_icon_path_ico)
            except Exception as e:
                print(f"Ошибка загрузки ICO иконки приложения: {e}")

    def _setup_managers(self):
        # Создаем менеджеры. ButtonTabManager создается один раз здесь для миксина.
        managers = [NoteManager(self), ButtonTabManager(self), TimerWorkTableManager(self)]
        
        for manager in managers:
            for name in dir(manager):
                if not name.startswith('_') and name not in dir(self):
                    setattr(self, name, getattr(manager, name))

    def _setup_menubar(self):
        self.menubar = tk.Menu(self.master)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Создать конфиг", command=self.create_config)
        self.filemenu.add_command(label="Сохранить конфиг", command=self.save_config)
        self.filemenu.add_command(label="Сохранить конфиг как...", command=self.save_config_as)
        self.filemenu.add_command(label="Загрузить конфиг", command=self.load_config_dialog)
        self.filemenu.add_separator()
        self.filemenu.add_checkbutton(label="Показывать диалоговые окна", onvalue=True, offvalue=False, variable=self.show_dialogs_var)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Пользователь", command=self.open_user_dialog) 
        self.filemenu.add_separator()
        self.filemenu.add_command(label="О программе", command=self.show_about)
        self.filemenu.add_command(label="Выход", command=self.on_closing)
        self.menubar.add_cascade(label="Файл", menu=self.filemenu)
        self.master.config(menu=self.menubar)

    def _setup_toolbar(self):
        self.top_toolbar = tk.Frame(self.master, bg="#e0e0e0")
        self.top_toolbar.pack(fill="x", padx=5, pady=2)

        self.create_note_button = self._create_control_button(self.top_toolbar, "Создать заметку", self.create_note_dialog, "create_note")
        self.create_note_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.create_timer_button = self._create_control_button(self.top_toolbar, "Создать таймер", self.open_create_timer_dialog, "create_timer")
        self.create_timer_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Используем уже существующий экземпляр менеджера из self
        self.work_table_button = self._create_control_button(self.top_toolbar, "Таблица работ", self.open_work_table_dialog, "work_table")
        self.work_table_button.pack(side=tk.LEFT, padx=5, pady=5)

    def _setup_main_layout(self):
        self.main_vertical_pane = ttk.PanedWindow(self.master, orient=tk.VERTICAL)
        self.main_vertical_pane.pack(fill="both", expand=True, padx=5, pady=5)

        self.notes_frame_container = tk.Frame(self.main_vertical_pane, bg="#f8f8f8", bd=2, relief="groove")
        self.main_vertical_pane.add(self.notes_frame_container, weight=1)
        self.notes_canvas = tk.Canvas(self.notes_frame_container, bg="#f8f8f8", highlightthickness=0)
        self.notes_canvas.pack(fill="both", expand=True)
        self.notes_frame_container.bind("<Configure>", self._on_notes_frame_configure)

        self.tabs_container_frame = tk.Frame(self.main_vertical_pane, bg="#e0e0e0")
        self.main_vertical_pane.add(self.tabs_container_frame, weight=3)
        self.tab_area_frame = tk.Frame(self.tabs_container_frame)
        self.tab_area_frame.pack(fill="both", expand=True)
        self.tabs_pane = ttk.PanedWindow(self.tab_area_frame, orient=tk.HORIZONTAL)
        self.tabs_pane.pack(side=tk.LEFT, fill="both", expand=True)

    def _setup_tab_control_panel(self):
        self.tab_control_panel = tk.Frame(self.tab_area_frame, width=150, bg="#d0d0d0", bd=1, relief=tk.RAISED)
        self.tab_control_panel.pack(side=tk.RIGHT, fill="y", padx=5, pady=5)
        self.tab_control_panel.pack_propagate(False)

        self.create_tab_button_panel = self._create_control_button(self.tab_control_panel, "Создать вкладку", self.create_tab_dialog, "create_tab")
        self.create_tab_button_panel.pack(fill="x", pady=5, padx=5)

        self.create_button_panel = self._create_control_button(self.tab_control_panel, "Создать кнопку", lambda: self.create_button_dialog(initial_tab_id=self._get_current_tab_id()), "create_button")
        self.create_button_panel.pack(fill="x", pady=5, padx=5)
        
        self.edit_mode_button = tk.Checkbutton(
            self.tab_control_panel, 
            text="Редактировать", 
            variable=self.edit_mode_active, 
            command=self.toggle_edit_mode,
            indicatoron=False,
            relief=tk.RAISED,
            selectcolor="#a0a0a0",
            image=self.control_icons.get("edit_mode"),
            compound=tk.LEFT
        )
        self.edit_mode_button.pack(fill="x", pady=5, padx=5)

        # Кнопка плавающего виджета
        self.float_widget_btn = self._create_control_button(self.tab_control_panel, "Плав. виджет", self.toggle_floating_widget, "main_app_icon_png")
        self.float_widget_btn.pack(fill="x", pady=5, padx=5)

        self.copy_button = self._create_control_button(self.tab_control_panel, "Копировать ТЕКСТ", self.copy_text_area_to_clipboard, "copy_text")
        self.copy_button.pack(fill="x", pady=5, padx=5)

        self.clear_button = self._create_control_button(self.tab_control_panel, "Очистить ТЕКСТ", self.clear_text, "clear_text")
        self.clear_button.pack(fill="x", pady=5, padx=5)

        self.column_frames = []
        self.tab_widgets = {}

    def _setup_bottom_panel(self):
        self.bottom_pane = ttk.PanedWindow(self.main_vertical_pane, orient=tk.HORIZONTAL)
        self.main_vertical_pane.add(self.bottom_pane, weight=2)

        self.timers_frame_container = tk.Frame(self.bottom_pane, bg="#e0e0e0", bd=2, relief="groove")
        self.bottom_pane.add(self.timers_frame_container, weight=1)
        tk.Label(self.timers_frame_container, text="Таймеры", font=("Arial", 12, "bold"), bg="#d0d0d0", pady=5).pack(fill="x", padx=2, pady=2)
        
        self.timers_canvas = tk.Canvas(self.timers_frame_container, bg="#e0e0e0", highlightthickness=0)
        self.timers_canvas.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        self.timers_scrollbar = tk.Scrollbar(self.timers_frame_container, orient="vertical", command=self.timers_canvas.yview)
        self.timers_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.timers_canvas.configure(yscrollcommand=self.timers_scrollbar.set)
        self.timers_list_frame = tk.Frame(self.timers_canvas, bg="#e0e0e0")
        self.timers_canvas.create_window((0, 0), window=self.timers_list_frame, anchor=tk.NW, tags="timers_frame")
        self.timers_list_frame.bind("<Configure>", self._on_timers_frame_configure)
        self.timers_canvas.bind("<Configure>", self._on_timers_canvas_configure)

        self.text_input_frame = tk.Frame(self.bottom_pane, bg="#ffffff", bd=2, relief="groove")
        self.bottom_pane.add(self.text_input_frame, weight=3)

        self.text_area = tk.Text(self.text_input_frame, wrap="word", font=("Arial", 10), bg="#ffffff", fg="#000000")
        self.text_area.pack(side=tk.LEFT, fill="both", expand=True, padx=(5,0), pady=5)

        self.text_scrollbar = tk.Scrollbar(self.text_input_frame, command=self.text_area.yview)
        self.text_scrollbar.pack(side=tk.RIGHT, fill="y", padx=(0,5), pady=5)
        self.text_area["yscrollcommand"] = self.text_scrollbar.set
        self.text_area.bind("<Button-3>", self.show_text_area_context_menu)

    # --- МЕТОДЫ УПРАВЛЕНИЯ ПЛАВАЮЩИМ ВИДЖЕТОМ ---
    def toggle_floating_widget(self):
        """Открывает или закрывает плавающий виджет кнопок."""
        if FloatingWidget is None:
            self._show_messagebox("error", "Ошибка", "Модуль floating_widget не загружен.")
            return

        if self.floating_widget_instance and self.floating_widget_instance.winfo_exists():
            self.floating_widget_instance.destroy()
            self.floating_widget_instance = None
        else:
            self.floating_widget_instance = FloatingWidget(self.master, self)

    # --- УТИЛИТЫ И КОНФИГ ---
    def _load_control_icons(self):
        if not HAS_PILLOW: return
        for key, path in CONTROL_ICONS.items():
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img = img.resize((16, 16), Image.LANCZOS)
                    self.control_icons[key] = ImageTk.PhotoImage(img)
                except Exception as e:
                    self.control_icons[key] = None
            else:
                self.control_icons[key] = None

    def _create_control_button(self, parent, text, command, icon_key):
        icon = self.control_icons.get(icon_key)
        if icon:
            return tk.Button(parent, text=text, command=command, bg="#d0d0d0", image=icon, compound=tk.LEFT, padx=2, pady=2)
        else:
            return tk.Button(parent, text=text, command=command, bg="#d0d0d0", padx=5, pady=5)

    def _choose_color(self, color_var):
        color_code = colorchooser.askcolor(title="Выбрать цвет")[1]
        if color_code:
            color_var.set(color_code)

    def _choose_image(self, image_var, is_note_bg=False):
        if not HAS_PILLOW:
            self._show_messagebox("warning", "Отсутствует Pillow", "Для работы с изображениями установите библиотеку Pillow: pip install Pillow")
            return
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")],
            title="Выбрать файл изображения"
        )
        if file_path:
            image_var.set(file_path)

    def _get_current_tab_id(self):
        if self.selected_tab_id and self.selected_tab_id in self.tabs:
            return self.selected_tab_id
        return self._get_first_tab_id()

    def _show_messagebox(self, type, title, message):
        if type == "askyesno":
            return messagebox.askyesno(title, message)
        if self.show_dialogs_var.get():
            if type == "info": messagebox.showinfo(title, message)
            elif type == "warning": messagebox.showwarning(title, message)
            elif type == "error": messagebox.showerror(title, message)
        return True

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (width // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (height // 2)
        window.geometry(f"+{x}+{y}")

    def on_closing(self):
        # Закрываем плавающий виджет, если он открыт (для сохранения его настроек)
        if self.floating_widget_instance and self.floating_widget_instance.winfo_exists():
            self.floating_widget_instance.destroy()

        if self._show_messagebox("askyesno", "Выход", "Вы хотите сохранить конфиг перед выходом?"):
            self.save_config()
        
        self.stop_all_timers()
        self.master.destroy()

    def _get_first_tab_id(self):
        return list(self.tabs.keys())[0] if self.tabs else None

    def _on_notes_frame_configure(self, event):
        self.notes_canvas.config(scrollregion=self.notes_canvas.bbox("all"))

    def _on_timers_frame_configure(self, event):
        self.timers_canvas.config(scrollregion=self.timers_canvas.bbox("all"))

    def _on_timers_canvas_configure(self, event):
        self.timers_canvas.itemconfig("timers_frame", width=event.width)

    def show_about(self):
        messagebox.showinfo("О программе PNSc", "PNSc v1.0\n\nPNS - Personal Note System.\n\nРазработчик: Goncharuk Aleksandr\n\n tg: @sanyochekodin")

    def copy_text_area_to_clipboard(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if text:
            self.master.clipboard_clear()
            self.master.clipboard_append(text)
            self.master.update()
            self._show_messagebox("info", "Копирование", "Текст скопирован в буфер обмена.")
        else:
            self._show_messagebox("warning", "Копирование", "Поле ТЕКСТ пусто.")

    def clear_text(self):
        if self._show_messagebox("askyesno", "Очистка поля", "Вы уверены, что хотите очистить поле ТЕКСТ?"):
            self.text_area.delete("1.0", tk.END)
            
    def open_user_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Настройки пользователя")
        self.center_window(dialog)
        dialog.transient(self.master)
        dialog.grab_set()
        tk.Label(dialog, text="Автор:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        author_entry = tk.Entry(dialog)
        author_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        author_entry.insert(0, self.global_author)
        author_entry.focus_set()

        def save_author():
            self.global_author = author_entry.get().strip()
            self.save_config(show_message=False)
            dialog.destroy()

        tk.Button(dialog, text="Сохранить", command=save_author).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        dialog.wait_window()

    def show_text_area_context_menu(self, event):
        context_menu = tk.Menu(self.master, tearoff=0)
        context_menu.add_command(label="Вырезать", command=lambda: self.text_area.event_generate("<<Cut>>"))
        context_menu.add_command(label="Копировать", command=lambda: self.text_area.event_generate("<<Copy>>"))
        context_menu.add_command(label="Вставить", command=lambda: self.text_area.event_generate("<<Paste>>"))
        context_menu.add_separator()
        context_menu.add_command(label="Копировать всё", command=self.copy_text_area_to_clipboard)
        context_menu.add_command(label="Очистить", command=self.clear_text)
        context_menu.tk_popup(event.x_root, event.y_root)

    def create_config(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Создание нового конфига")
        self.center_window(dialog)
        dialog.transient(self.master)
        dialog.grab_set()
        tk.Label(dialog, text="Введите имя для нового конфига:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        name_entry = tk.Entry(dialog); name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        def save_new_config():
            config_name = name_entry.get().strip()
            if not config_name: return
            self.current_config_name = config_name
            self.current_config_path = os.path.join(self.config_dir, f"{config_name}.json")
            self.tabs = {}; self.notes = {}; self.completed_jobs = []
            self.clear_notes(); self.update_tab_display(); self.save_config()
            dialog.destroy()
        
        tk.Button(dialog, text="Создать", command=save_new_config).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        dialog.wait_window()

    def save_config(self, show_message=True):
        if not self.current_config_path:
            self.save_config_as()
            return
        notes_data_for_save = {nid: nw.data for nid, nw in self.notes.items()}
        config_data = {
            "tabs": self.tabs, "notes": notes_data_for_save,
            "device_types": self.device_types, "work_types": self.work_types,
            "completed_jobs": self.completed_jobs,
            "text_area_content": self.text_area.get("1.0", tk.END).strip(),
            "global_author": self.global_author 
        }
        try:
            with open(self.current_config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            if show_message: self._show_messagebox("info", "Сохранение", "Конфиг сохранен.")
        except Exception as e:
            self._show_messagebox("error", "Ошибка", f"Не удалось сохранить: {e}")

    def save_config_as(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Сохранить конфиг как...")
        self.center_window(dialog)
        tk.Label(dialog, text="Имя конфига:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(dialog); name_entry.grid(row=0, column=1, padx=5, pady=5)

        def perform_save_as():
            name = name_entry.get().strip()
            if name:
                self.current_config_name = name
                self.current_config_path = os.path.join(self.config_dir, f"{name}.json")
                self.save_config()
                dialog.destroy()
        
        tk.Button(dialog, text="Сохранить", command=perform_save_as).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        dialog.wait_window()

    def load_config_dialog(self):
        configs = [f.replace(".json", "") for f in os.listdir(self.config_dir) if f.endswith('.json')]
        if not configs: return
        dialog = tk.Toplevel(self.master)
        config_var = tk.StringVar(value=configs[0])
        ttk.Combobox(dialog, textvariable=config_var, values=configs).pack(padx=10, pady=10)

        def perform_load():
            self.current_config_name = config_var.get()
            self.current_config_path = os.path.join(self.config_dir, f"{self.current_config_name}.json")
            self.load_config()
            dialog.destroy()

        tk.Button(dialog, text="Загрузить", command=perform_load).pack(pady=5)
        dialog.wait_window()

    def load_config(self):
        if not self.current_config_path: return
        try:
            with open(self.current_config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            self.tabs = config_data.get("tabs", {})
            self.clear_notes()
            for nid, data in config_data.get("notes", {}).items():
                self.notes[nid] = NoteWidget(self, self.notes_canvas, nid, data)
            self.device_types = config_data.get("device_types", [])
            self.work_types = config_data.get("work_types", [])
            self.completed_jobs = config_data.get("completed_jobs", [])
            self.global_author = config_data.get("global_author", "") 
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, config_data.get("text_area_content", ""))
            self.update_tab_display()
            self.update_work_table_display()
        except Exception as e:
            self._show_messagebox("error", "Ошибка", f"Не удалось загрузить: {e}")

    def load_default_config_if_needed(self):
        configs = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
        if configs:
            self.current_config_path = os.path.join(self.config_dir, configs[0])
            self.current_config_name = configs[0].replace(".json", "")
            self.load_config()
        else:
            self.current_config_name = "default"
            self.current_config_path = os.path.join(self.config_dir, "default.json")
            self.save_config(show_message=False)

    def treeview_sort_column(self, tree, col, reverse):
        TimerWorkTableManager(self).treeview_sort_column(tree, col, reverse)
        
    def _find_job_by_id(self, job_id):
        return TimerWorkTableManager(self)._find_job_by_id(job_id)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    if not os.path.exists("configs"): os.makedirs("configs")
    app = PNSc(root)
    root.mainloop()
