
# module_notes.py

from pnsc_utils import tk, ttk, filedialog, messagebox, colorchooser, os, Image, ImageTk, HAS_PILLOW, tkFont, uuid

class NoteWidget:
    """Виджет заметки, перетаскиваемый и изменяемый в размере."""
    def __init__(self, app_instance, canvas, note_id, note_data):
        self.app = app_instance
        self.canvas = canvas
        self.note_id = note_id
        self.data = note_data

        # Установка дефолтных значений, если их нет
        self.data.setdefault('text', 'Новая заметка')
        self.data.setdefault('x', 10)
        self.data.setdefault('y', 10)
        self.data.setdefault('width', 200)
        self.data.setdefault('height', 150)
        self.data.setdefault('bg_color', '#ffffcc')
        self.data.setdefault('text_color', '#000000')
        self.data.setdefault('font_size', 10)
        self.data.setdefault('font_family', 'Arial')
        self.data.setdefault('bg_image', '')
        self.data.setdefault('note_name', 'Заметка')

        self.available_fonts = sorted(tkFont.families())
        if self.data['font_family'] not in self.available_fonts:
            self.data['font_family'] = 'Arial'

        self.frame = tk.Frame(canvas, bd=2, relief="raised", bg=self.data['bg_color'])
        
        self.title_bar = tk.Frame(self.frame, bg=self.data['bg_color'], relief="flat", bd=0)
        self.title_bar.pack(side=tk.TOP, fill=tk.X)
        
        self.title_label = tk.Label(self.title_bar, text=self.data['note_name'], bg=self.data['bg_color'], fg=self.data['text_color'], anchor=tk.W)
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        self.title_label.bind("<Double-Button-1>", lambda e: self._make_title_editable())

        self.menu_button = tk.Button(self.title_bar, text="⚙", command=self.show_config_dialog, width=2, height=1, relief=tk.FLAT, bg=self.data['bg_color'], fg=self.data['text_color'], font=("Arial", 10))
        self.menu_button.pack(side=tk.RIGHT, padx=2, pady=2)

        self.text_container_frame = tk.Frame(self.frame, bg=self.data['bg_color'])
        self.text_container_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.text_area = tk.Text(self.text_container_frame, wrap="word",
                                 font=(self.data['font_family'], self.data['font_size']),
                                 bg=self.data['bg_color'],
                                 fg=self.data['text_color'],
                                 bd=0, highlightthickness=0)
        self.text_area.pack(side=tk.LEFT, fill="both", expand=True)
        self.text_area.insert(tk.END, self.data['text'])
        self.text_area.bind("<KeyRelease>", self._on_text_change)

        self.text_scrollbar = tk.Scrollbar(self.text_container_frame, command=self.text_area.yview)
        self.text_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.text_area["yscrollcommand"] = self.text_scrollbar.set

        self.canvas_item = canvas.create_window(self.data['x'], self.data['y'],
                                                window=self.frame,
                                                anchor=tk.NW,
                                                width=self.data['width'],
                                                height=self.data['height'])
        
        self.bg_image_tk = None

        self._bind_drag_events()
        self._bind_resize_events()
        self._apply_styles()

    def _on_text_change(self, event=None):
        self.data['text'] = self.text_area.get("1.0", tk.END).strip()
        self.app.save_config(show_message=False)

    def _bind_drag_events(self):
        self._drag_data = {"x": 0, "y": 0}
        self.title_bar.bind("<Button-1>", self._on_drag_start)
        self.title_bar.bind("<B1-Motion>", self._on_drag_motion)
        self.title_bar.bind("<ButtonRelease-1>", lambda e: self.app.save_config(show_message=False))
        self.title_label.bind("<Button-1>", self._on_drag_start)
        self.title_label.bind("<B1-Motion>", self._on_drag_motion)
        self.title_label.bind("<ButtonRelease-1>", lambda e: self.app.save_config(show_message=False))

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        x1, y1 = self.canvas.coords(self.canvas_item)
        new_x = x1 + delta_x
        new_y = y1 + delta_y
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.frame.update_idletasks()
        note_width = self.frame.winfo_width()
        note_height = self.frame.winfo_height()
        new_x = max(0, min(new_x, canvas_width - note_width))
        new_y = max(0, min(new_y, canvas_height - note_height))
        self.canvas.coords(self.canvas_item, new_x, new_y)
        self.data['x'] = new_x
        self.data['y'] = new_y
        if hasattr(self, 'bg_image_tk_id') and self.bg_image_tk_id:
            self.canvas.coords(self.bg_image_tk_id, new_x, new_y)

    def _bind_resize_events(self):
        self._resize_handle = tk.Frame(self.frame, bg="gray", width=10, height=10, cursor="sizing")
        self._resize_handle.place(relx=1.0, rely=1.0, anchor=tk.SE)
        self._resize_data = {"x": 0, "y": 0, "width": 0, "height": 0}
        self._resize_handle.bind("<Button-1>", self._on_resize_start)
        self._resize_handle.bind("<B1-Motion>", self._on_resize_motion)
        self._resize_handle.bind("<ButtonRelease-1>", lambda e: self.app.save_config(show_message=False))

    def _on_resize_start(self, event):
        self._resize_data["x"] = event.x
        self._resize_data["y"] = event.y
        self._resize_data["width"] = self.data['width']
        self._resize_data["height"] = self.data['height']

    def _on_resize_motion(self, event):
        delta_w = event.x - self._resize_data["x"]
        delta_h = event.y - self._resize_data["y"]
        min_width = 100
        min_height = 50
        new_width = max(min_width, self._resize_data["width"] + delta_w)
        new_height = max(min_height, self._resize_data["height"] + delta_h)
        self.data['width'] = new_width
        self.data['height'] = new_height
        self.canvas.itemconfig(self.canvas_item, width=new_width, height=new_height)
        self.frame.update_idletasks()
        self._resize_handle.place(relx=1.0, rely=1.0, anchor=tk.SE)
        self._apply_styles()

    def _apply_styles(self):
        self.frame.config(bg=self.data['bg_color'])
        self.title_bar.config(bg=self.data['bg_color'])
        self.title_label.config(bg=self.data['bg_color'], fg=self.data['text_color'], text=self.data['note_name'])
        self.menu_button.config(bg=self.data['bg_color'], fg=self.data['text_color'])
        self.text_container_frame.config(bg=self.data['bg_color'])
        self.text_area.config(bg=self.data['bg_color'], fg=self.data['text_color'],
                              font=(self.data['font_family'], self.data['font_size']))
        
        if hasattr(self, 'bg_image_tk_id') and self.bg_image_tk_id:
            self.canvas.delete(self.bg_image_tk_id)
            self.bg_image_tk_id = None
            self.bg_image_tk = None

        if HAS_PILLOW and self.data['bg_image'] and os.path.exists(self.data['bg_image']):
            try:
                img = Image.open(self.data['bg_image'])
                note_width = self.data['width']
                note_height = self.data['height']
                img = img.resize((note_width, note_height), Image.LANCZOS) 
                self.bg_image_tk = ImageTk.PhotoImage(img)
                x_note, y_note = self.canvas.coords(self.canvas_item)
                self.bg_image_tk_id = self.canvas.create_image(x_note, y_note, 
                                                               image=self.bg_image_tk, 
                                                               anchor=tk.NW,
                                                               tags=(f"note_bg_{self.note_id}"))
                self.canvas.tag_lower(self.bg_image_tk_id, self.canvas_item)
                self.canvas.coords(self.bg_image_tk_id, x_note, y_note)
            except Exception as e:
                self.app._show_messagebox("warning", "Ошибка изображения", f"Не удалось загрузить изображение: {e}. Будет использован цвет фона.")
                self.data['bg_image'] = ''
        
        self.canvas.itemconfig(self.canvas_item, width=self.data['width'], height=self.data['height'])
        if hasattr(self, '_resize_handle'):
            self._resize_handle.place(relx=1.0, rely=1.0, anchor=tk.SE)

        x_note, y_note = self.canvas.coords(self.canvas_item)
        if hasattr(self, 'bg_image_tk_id') and self.bg_image_tk_id:
            self.canvas.coords(self.bg_image_tk_id, x_note, y_note)

    def _make_title_editable(self):
        current_name = self.title_label.cget("text")
        self.title_label.pack_forget()
        self.edit_entry = tk.Entry(self.title_bar,
                                   bg=self.data['bg_color'],
                                   fg=self.data['text_color'],
                                   font=("Arial", 8, "bold"))
        self.edit_entry.insert(0, current_name)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus_set()
        self.edit_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        self.edit_entry.bind("<Return>", lambda e: self._finish_title_edit())
        self.edit_entry.bind("<FocusOut>", lambda e: self._finish_title_edit())
        
    def _finish_title_edit(self):
        new_name = self.edit_entry.get().strip()
        if not new_name:
            new_name = "Заметка"
        self.data['note_name'] = new_name
        self.title_label.config(text=new_name)
        self.edit_entry.pack_forget()
        self.edit_entry.destroy()
        self.edit_entry = None
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        self.app.save_config(show_message=False)

    def show_config_dialog(self):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Настройки заметки")
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()

        row = 0
        tk.Label(dialog, text="Имя заметки:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
        note_name_var = tk.StringVar(value=self.data.get('note_name', 'Заметка'))
        note_name_entry = tk.Entry(dialog, textvariable=note_name_var)
        note_name_entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
        row += 1

        tk.Label(dialog, text="Цвет фона:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
        bg_color_var = tk.StringVar(value=self.data['bg_color'])
        bg_color_entry = tk.Entry(dialog, textvariable=bg_color_var)
        bg_color_entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
        tk.Button(dialog, text="Выбрать цвет", command=lambda: self.app._choose_color(bg_color_var)).grid(row=row, column=2, padx=2, pady=2)
        row += 1

        tk.Label(dialog, text="Цвет текста:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
        text_color_var = tk.StringVar(value=self.data['text_color'])
        text_color_entry = tk.Entry(dialog, textvariable=text_color_var)
        text_color_entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
        tk.Button(dialog, text="Выбрать цвет", command=lambda: self.app._choose_color(text_color_var)).grid(row=row, column=2, padx=2, pady=2)
        row += 1

        tk.Label(dialog, text="Размер шрифта:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
        font_size_var = tk.IntVar(value=self.data['font_size'])
        font_size_spinbox = tk.Spinbox(dialog, from_=8, to_=72, textvariable=font_size_var)
        font_size_spinbox.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
        row += 1
        
        tk.Label(dialog, text="Шрифт:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
        font_family_var = tk.StringVar(value=self.data['font_family'])
        font_family_combobox = ttk.Combobox(dialog, textvariable=font_family_var, values=self.available_fonts, state="readonly")
        font_family_combobox.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
        if self.data['font_family'] in self.available_fonts:
            font_family_combobox.set(self.data['font_family'])
        else:
            font_family_combobox.set('Arial')
        row += 1

        tk.Label(dialog, text="Фоновое изображение:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
        bg_image_var = tk.StringVar(value=self.data['bg_image'])
        bg_image_entry = tk.Entry(dialog, textvariable=bg_image_var)
        bg_image_entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.EW)
        tk.Button(dialog, text="Обзор...", command=lambda: self.app._choose_image(bg_image_var, is_note_bg=True)).grid(row=row, column=2, padx=2, pady=2)
        row += 1

        def apply_changes():
            self.data['note_name'] = note_name_var.get().strip() or 'Заметка'
            self.data['bg_color'] = bg_color_var.get()
            self.data['text_color'] = text_color_var.get()
            self.data['font_size'] = font_size_var.get()
            self.data['font_family'] = font_family_combobox.get()
            self.data['bg_image'] = bg_image_var.get()

            self._apply_styles()
            self.app.save_config(show_message=False)
            dialog.destroy()

        save_button = tk.Button(dialog, text="Применить", command=apply_changes)
        save_button.grid(row=row, column=0, columnspan=3, padx=5, pady=5)
        row += 1

        delete_image_button = tk.Button(dialog, text="Удалить картинку", command=lambda: self._delete_background_image(bg_image_var))
        delete_image_button.grid(row=row, column=0, columnspan=3, padx=5, pady=2)
        row += 1

        delete_note_button = tk.Button(dialog, text="Удалить заметку", command=lambda: self._delete_note(dialog))
        delete_note_button.grid(row=row, column=0, columnspan=3, padx=5, pady=5)
        
        dialog.bind("<Return>", lambda event: apply_changes())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.columnconfigure(1, weight=1)
        dialog.wait_window()

    def _delete_background_image(self, image_var):
        image_var.set('')
        self.data['bg_image'] = ''
        self._apply_styles()
        self.app.save_config(show_message=False)

    def _delete_note(self, dialog):
        if self.app._show_messagebox("askyesno", "Удаление заметки", "Вы уверены, что хотите удалить эту заметку?"):
            self.canvas.delete(self.canvas_item)
            if hasattr(self, 'bg_image_tk_id') and self.bg_image_tk_id:
                self.canvas.delete(self.bg_image_tk_id)
            del self.app.notes[self.note_id]
            self.app.save_config(show_message=False)
            dialog.destroy()
            self.frame.destroy()

# --- Менеджер заметок для интеграции в PNSc ---

class NoteManager:
    def __init__(self, app):
        self.app = app

    def create_note_dialog(self):
        note_id = str(uuid.uuid4())
        note_data = {
            'text': 'Новая заметка',
            'x': 10,
            'y': 10,
            'width': 200,
            'height': 150,
            'bg_color': '#ffffcc',
            'text_color': '#000000',
            'font_size': 10,
            'font_family': 'Arial',
            'bg_image': '',
            'note_name': f'Заметка {len(self.app.notes) + 1}'
        }
        note_widget = NoteWidget(self.app, self.app.notes_canvas, note_id, note_data)
        self.app.notes[note_id] = note_widget
        self.app.save_config(show_message=False)
        self.app.notes_canvas.config(scrollregion=self.app.notes_canvas.bbox("all"))

    def clear_notes(self):
        for note_id, note_widget in list(self.app.notes.items()):
            if hasattr(note_widget, 'bg_image_tk_id') and note_widget.bg_image_tk_id:
                self.app.notes_canvas.delete(note_widget.bg_image_tk_id)
            self.app.notes_canvas.delete(note_widget.canvas_item)
            note_widget.frame.destroy()
            del self.app.notes[note_id]
