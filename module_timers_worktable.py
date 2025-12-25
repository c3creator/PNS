
# module_timers_worktable.py

from pnsc_utils import tk, ttk, uuid, time, datetime, messagebox, csv, filedialog
import os
import sys

class TimerWorkTableManager:
    def __init__(self, app):
        self.app = app
        # Путь к звуковому файлу при срабатывании обратного таймера:
        # !!! ВАЖНО: Укажите здесь свой путь к файлу WAV, OGG или MP3.
        # Например: "C:/Windows/Media/Windows Notify System Generic.wav" (для Windows)
        # Если путь пуст, звук не проигрывается.
        self.sound_path = "" # <-- УКАЖИТЕ СВОЙ ПУТЬ К ЗВУКОВОМУ ФАЙЛУ ЗДЕСЬ
        # Интервал мигания в мс
        self.blink_interval = 500
        # Словарь для хранения after-id для мигания, чтобы можно было отменять
        self._blink_jobs = {}

    # Вспомогательная функция: проиграть звук (кроссплатформенно пытается разными способами)
    def _play_sound(self):
        path = self.sound_path
        if not path or not os.path.exists(path):
            return # Звуковой файл не указан или не найден

        try:
            if sys.platform.startswith("win"):
                import winsound
                # winsound.SND_ASYNC позволяет продолжить выполнение программы
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif sys.platform.startswith("darwin"): # macOS
                os.system(f'afplay "{path}" &')
            elif sys.platform.startswith("linux"): # Linux
                # Предпочтительнее paplay для PulseAudio, затем aplay для ALSA
                if os.system(f'command -v paplay >/dev/null 2>&1') == 0:
                    os.system(f'paplay "{path}" &')
                elif os.system(f'command -v aplay >/dev/null 2>&1') == 0:
                    os.system(f'aplay "{path}" &')
                else:
                    # Можно добавить mplayer или mpv как запасной вариант, если они установлены
                    pass
            else:
                # Другие платформы или не найдены команды, ничего не делаем
                pass
        except Exception as e:
            # Не критично, просто пропускаем при ошибках воспроизведения
            print(f"Ошибка воспроизведения звука: {e}")
            pass

    def open_create_timer_dialog(self):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Создание таймера")
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()

        row = 0

        # Режим таймера: основной (счёт вверх) или обратный (счёт вниз)
        tk.Label(dialog, text="Режим таймера:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        mode_var = tk.StringVar(value="up") # По умолчанию: основной таймер
        mode_frame = tk.Frame(dialog)
        mode_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        tk.Radiobutton(mode_frame, text="Основной (счёт вверх)", variable=mode_var, value="up").pack(side=tk.LEFT, padx=(0,10))
        tk.Radiobutton(mode_frame, text="Обратный (счёт вниз)", variable=mode_var, value="down").pack(side=tk.LEFT)
        row += 1

        tk.Label(dialog, text="Название устройства:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        device_name_entry = tk.Entry(dialog)
        device_name_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        device_name_entry.focus_set()
        row += 1

        tk.Label(dialog, text="Тип устройства:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        device_type_var = tk.StringVar()
        device_type_combo = ttk.Combobox(dialog, textvariable=device_type_var, values=self.app.device_types, state="readonly")
        device_type_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        if self.app.device_types:
            device_type_combo.set(self.app.device_types[0])
        
        def create_device_type_dialog():
            new_type_dialog = tk.Toplevel(dialog)
            new_type_dialog.title("Создать тип устройства")
            self.app.center_window(new_type_dialog)
            new_type_dialog.transient(dialog)
            new_type_dialog.grab_set()

            tk.Label(new_type_dialog, text="Новый тип устройства:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            new_type_entry = tk.Entry(new_type_dialog)
            new_type_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
            new_type_entry.focus_set()

            def save_new_device_type():
                new_type = new_type_entry.get().strip()
                if new_type and new_type not in self.app.device_types:
                    self.app.device_types.append(new_type)
                    self.app.device_types.sort()
                    device_type_combo['values'] = self.app.device_types
                    device_type_var.set(new_type)
                    self.app.save_config(show_message=False)
                    new_type_dialog.destroy()
                elif new_type in self.app.device_types:
                    self.app._show_messagebox("warning", "Предупреждение", "Такой тип устройства уже существует.")
                else:
                    self.app._show_messagebox("warning", "Предупреждение", "Пожалуйста, введите название типа устройства.")
            
            tk.Button(new_type_dialog, text="Создать", command=save_new_device_type).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
            new_type_dialog.bind("<Return>", lambda event: save_new_device_type())
            new_type_dialog.bind("<Escape>", lambda event: new_type_dialog.destroy())
            new_type_dialog.columnconfigure(1, weight=1)
            new_type_dialog.wait_window()
        
        tk.Button(dialog, text="Создать тип", command=create_device_type_dialog, width=12).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Тип работ:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        work_type_var = tk.StringVar()
        work_type_combo = ttk.Combobox(dialog, textvariable=work_type_var, values=self.app.work_types, state="readonly")
        work_type_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        if self.app.work_types:
            work_type_combo.set(self.app.work_types[0])
        
        def create_work_type_dialog():
            new_type_dialog = tk.Toplevel(dialog)
            new_type_dialog.title("Создать тип работ")
            self.app.center_window(new_type_dialog)
            new_type_dialog.transient(dialog)
            new_type_dialog.grab_set()

            tk.Label(new_type_dialog, text="Новый тип работ:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            new_type_entry = tk.Entry(new_type_dialog)
            new_type_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
            new_type_entry.focus_set()

            def save_new_work_type():
                new_type = new_type_entry.get().strip()
                if new_type and new_type not in self.app.work_types:
                    self.app.work_types.append(new_type)
                    self.app.work_types.sort()
                    work_type_combo['values'] = self.app.work_types
                    work_type_var.set(new_type)
                    self.app.save_config(show_message=False)
                    new_type_dialog.destroy()
                elif new_type in self.app.work_types:
                    self.app._show_messagebox("warning", "Предупреждение", "Такой тип работ уже существует.")
                else:
                    self.app._show_messagebox("warning", "Предупреждение", "Пожалуйста, введите название типа работ.")
            
            tk.Button(new_type_dialog, text="Создать", command=save_new_work_type).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
            new_type_dialog.bind("<Return>", lambda event: save_new_work_type())
            new_type_dialog.bind("<Escape>", lambda event: new_type_dialog.destroy())
            new_type_dialog.columnconfigure(1, weight=1)
            new_type_dialog.wait_window()
        
        tk.Button(dialog, text="Создать тип", command=create_work_type_dialog, width=12).grid(row=row, column=2, padx=2, pady=5)
        row += 1

        tk.Label(dialog, text="Заявленное время (сек):").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        declared_time_entry = tk.Entry(dialog)
        declared_time_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        # Блок для обратного таймера: часы, минуты, секунды (показывается/скрывается в зависимости от режима)
        down_frame = tk.Frame(dialog)
        down_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        tk.Label(down_frame, text="Установите время для обратного таймера (чч:мм:сс):").grid(row=0, column=0, columnspan=6, padx=2, pady=2, sticky=tk.W)
        tk.Label(down_frame, text="Часы:").grid(row=1, column=0, padx=2, sticky=tk.E)
        hours_entry = tk.Entry(down_frame, width=4)
        hours_entry.grid(row=1, column=1, padx=2)
        hours_entry.insert(0, "00")
        tk.Label(down_frame, text="Минуты:").grid(row=1, column=2, padx=2, sticky=tk.E)
        minutes_entry = tk.Entry(down_frame, width=4)
        minutes_entry.grid(row=1, column=3, padx=2)
        minutes_entry.insert(0, "00")
        tk.Label(down_frame, text="Секунды:").grid(row=1, column=4, padx=2, sticky=tk.E)
        seconds_entry = tk.Entry(down_frame, width=4)
        seconds_entry.grid(row=1, column=5, padx=2)
        seconds_entry.insert(0, "00")
        down_frame.columnconfigure(1, weight=1) # Расширяем колонку для полей ввода
        down_frame.columnconfigure(3, weight=1)
        down_frame.columnconfigure(5, weight=1)
        row += 1

        # Для основного таймера: опция включать мигающую подсветку при паузе и выбор цвета
        blink_option_frame = tk.Frame(dialog)
        blink_option_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        blink_enabled_var = tk.BooleanVar(value=False)
        tk.Checkbutton(blink_option_frame, text="Мигающая подсветка для основного таймера при паузе",
                       variable=blink_enabled_var).pack(side=tk.LEFT)
        tk.Label(blink_option_frame, text="Цвет:").pack(side=tk.LEFT, padx=(10,2))
        blink_color_var = tk.StringVar(value="orange") # Цвет по умолчанию
        blink_color_combo = ttk.Combobox(blink_option_frame, textvariable=blink_color_var,
                                         values=["red", "orange", "yellow", "green", "cyan", "magenta", "blue", "purple"],
                                         state="readonly", width=10)
        blink_color_combo.pack(side=tk.LEFT)
        row += 1

        # Функция для обновления видимости блока обратного таймера и опции мигания
        def _update_mode_visibility(*args):
            if mode_var.get() == "down":
                down_frame.grid(row=row-2, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5) # -2 потому что row уже увеличился
                blink_option_frame.grid_remove() # Скрываем опцию мигания для обратного таймера
            else:
                down_frame.grid_remove()
                blink_option_frame.grid(row=row-1, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5) # -1 потому что row уже увеличился
        mode_var.trace_add("write", lambda *args: _update_mode_visibility())
        _update_mode_visibility() # Вызываем при инициализации для установки начального состояния


        def start_timer():
            device_name = device_name_entry.get().strip()
            device_type = device_type_var.get()
            work_type = work_type_var.get()
            declared_time_str = declared_time_entry.get().strip()

            if not device_name:
                self.app._show_messagebox("warning", "Предупреждение", "Название устройства является обязательным.")
                return

            declared_time = 0
            if declared_time_str:
                try:
                    declared_time = int(declared_time_str)
                    if declared_time < 0:
                        raise ValueError("Время не может быть отрицательным.")
                except ValueError as e:
                    self.app._show_messagebox("warning", "Ошибка ввода", f"Некорректное значение для заявленного времени: {e}")
                    return

            timer_id = str(uuid.uuid4())
            
            is_countdown = (mode_var.get() == "down")
            duration = 0
            if is_countdown:
                try:
                    h = int(hours_entry.get() or 0)
                    m = int(minutes_entry.get() or 0)
                    s = int(seconds_entry.get() or 0)
                    if h < 0 or m < 0 or s < 0:
                        raise ValueError("Отрицательное значение")
                    duration = h*3600 + m*60 + s
                    if duration <= 0:
                        self.app._show_messagebox("warning", "Ошибка", "Укажите время больше нуля для обратного таймера.")
                        return
                except ValueError:
                    self.app._show_messagebox("warning", "Ошибка ввода", "Часы/Минуты/Секунды должны быть целыми числами.")
                    return
            
            self.app.active_timers[timer_id] = {
                "device_name": device_name,
                "device_type": device_type,
                "work_type": work_type,
                "declared_time": declared_time,
                "start_time": time.time(),
                "elapsed_time": 0,
                "is_running": True,
                "pause_time": 0,
                "total_paused_duration": 0,
                "widget": None,
                # Новые поля для таймеров
                "is_countdown": is_countdown,
                "duration": duration,               # для обратного таймера — начальное время в секундах
                "completed": False,                 # для обратного: истёк ли таймер
                "blink_enabled": blink_enabled_var.get(), # для основного: включено ли мигание при паузе
                "blink_color": blink_color_var.get(),    # для основного: цвет мигания
                "blink_state": False                # внутреннее состояние мигания (true/false)
            }
            self.create_timer_widget(timer_id, self.app.active_timers[timer_id])
            self.app.save_config(show_message=False)
            dialog.destroy()

        start_button = tk.Button(dialog, text="Старт", command=start_timer)
        start_button.grid(row=row, column=0, columnspan=3, padx=5, pady=10)

        dialog.bind("<Return>", lambda event: start_timer())
        dialog.bind("<Escape>", lambda event: dialog.destroy())

        dialog.columnconfigure(1, weight=1)
        dialog.wait_window()

    def create_timer_widget(self, timer_id, timer_data):
        timer_widget_frame = tk.Frame(self.app.timers_list_frame, bg="#c0c0c0", bd=1, relief="solid", padx=5, pady=5)
        timer_widget_frame.pack(fill="x", expand=True, pady=2, padx=2)
        timer_data["widget"] = timer_widget_frame

        device_label = tk.Label(timer_widget_frame, text=timer_data["device_name"], font=("Arial", 10, "bold"), anchor=tk.W, bg="#c0c0c0")
        device_label.pack(fill="x")

        time_label = tk.Label(timer_widget_frame, text="00:00:00", font=("Arial", 18, "bold"), anchor=tk.W, bg="#c0c0c0")
        time_label.pack(fill="x")
        
        status_text = "ОБРАТНЫЙ" if timer_data.get("is_countdown") else "РАБОТАЕТ"
        status_color = "blue" if timer_data.get("is_countdown") else "green"
        status_label = tk.Label(timer_widget_frame, text=status_text, font=("Arial", 8), anchor=tk.E, bg="#c0c0c0", fg=status_color)
        status_label.pack(fill="x")
        timer_data["status_label"] = status_label

        # Left click: диалог подтверждения завершения таймера
        def left_click_handler(event, tid=timer_id):
            self.confirm_finish_timer(tid)

        # Right click: если обратный таймер завершён — удаление; если работает — пауза/возобновление
        def right_click_handler(event, tid=timer_id):
            if tid not in self.app.active_timers:
                return
            td = self.app.active_timers[tid]
            if td.get("is_countdown") and td.get("completed"):
                # Если обратный таймер завершён, ПКМ удаляет его
                self._cancel_blink(tid) # Отменяем мигание перед удалением
                if td["widget"]:
                    td["widget"].destroy()
                del self.app.active_timers[tid]
                self.app.save_config(show_message=False) # Сохраняем состояние после удаления
                self.app.timers_list_frame.update_idletasks()
                self.app.timers_canvas.config(scrollregion=self.app.timers_canvas.bbox("all"))
                return
            # Иначе (для работающего таймера любого типа или основного таймера в паузе) — переключаем паузу
            self.toggle_timer_pause(tid)

        timer_widget_frame.bind("<Button-1>", left_click_handler)
        device_label.bind("<Button-1>", left_click_handler)
        time_label.bind("<Button-1>", left_click_handler)
        
        timer_widget_frame.bind("<Button-3>", right_click_handler)
        device_label.bind("<Button-3>", right_click_handler)
        time_label.bind("<Button-3>", right_click_handler)

        self.update_timer_display(timer_id)
        self.app.timers_list_frame.update_idletasks()
        self.app.timers_canvas.config(scrollregion=self.app.timers_canvas.bbox("all"))

    def confirm_finish_timer(self, timer_id):
        # ЛКМ: диалог подтверждения завершения таймера
        if timer_id not in self.app.active_timers:
            return
        td = self.app.active_timers[timer_id]
        name = td.get("device_name", "таймер")
        
        if not self.app._show_messagebox("askyesno", "Завершить таймер", f"Завершить таймер для '{name}'?"):
            return

        if td.get("is_countdown"):
            # Для обратного таймера: по завершении данные никуда не записываются,
            # таймер начинает мигать красной подсветкой.
            td["is_running"] = False
            td["completed"] = True
            td["pause_time"] = 0 # Обнуляем время паузы, так как он завершен
            if td.get("status_label"):
                td["status_label"].config(text="ЗАВЕРШЁН", fg="red")
            self._start_blink(timer_id, "red") # Запускаем мигание красным
            self._play_sound() # Проигрываем звуковой сигнал
        else:
            # Для основного таймера — прежнее поведение: остановить и записать работу
            self.stop_timer(timer_id)
        self.app.save_config(show_message=False) # Сохраняем изменение состояния таймера

    def toggle_timer_pause(self, timer_id):
        # ПКМ: если завершён — обратный таймер удаляется (обработано в create_timer_widget);
        # если ещё работает — то пауза (при паузе мигает желтым).
        if timer_id not in self.app.active_timers:
            return

        td = self.app.active_timers[timer_id]
        status_label = td.get("status_label")

        # Если обратный таймер завершён, ПКМ должна его удалять (уже обработано в right_click_handler)
        if td.get("is_countdown") and td.get("completed"):
            return

        if td["is_running"]:
            # Поставить на паузу
            td["is_running"] = False
            td["pause_time"] = time.time()
            if status_label:
                status_label.config(text="ПАУЗА", fg="orange")
            # Для основного таймера включаем мигание, если оно включено в настройках
            # Для обратного таймера мигание включаем всегда при паузе (жёлтым)
            if td.get("is_countdown") or td.get("blink_enabled"):
                blink_color = td.get("blink_color", "yellow") if not td.get("is_countdown") else "yellow"
                self._start_blink(timer_id, blink_color)
            self.app._show_messagebox("info", "Таймер", f"Таймер для '{td['device_name']}' поставлен на паузу.")
        else:
            # Возобновление
            if td["pause_time"] > 0:
                paused_duration = time.time() - td["pause_time"]
                td["total_paused_duration"] += paused_duration
                td["pause_time"] = 0
            
            td["is_running"] = True
            if status_label:
                status_text = "ОБРАТНЫЙ" if td.get("is_countdown") else "РАБОТАЕТ"
                status_color = "blue" if td.get("is_countdown") else "green"
                status_label.config(text=status_text, fg=status_color)
            # Отменяем мигание при возобновлении
            self._cancel_blink(timer_id)
            self.update_timer_display(timer_id) # Сразу обновляем дисплей после возобновления
            self.app._show_messagebox("info", "Таймер", f"Таймер для '{td['device_name']}' возобновлен.")
        self.app.save_config(show_message=False) # Сохраняем изменение состояния таймера

    def update_timer_display(self, timer_id):
        if timer_id not in self.app.active_timers:
            return

        td = self.app.active_timers[timer_id]
        
        # Если таймер не запущен и не завершен (т.е. на паузе), не обновляем время
        if not td["is_running"] and not td.get("completed"):
            # Если таймер на паузе, но мигание должно быть включено, убедимся, что оно работает
            if td.get("blink_enabled") or td.get("is_countdown"):
                blink_color = td.get("blink_color", "yellow") if not td.get("is_countdown") else "yellow"
                if timer_id not in self._blink_jobs:
                    self._start_blink(timer_id, blink_color)
            return

        # Вычисляем прошедшее время
        current_time = time.time()
        elapsed_time = (current_time - td["start_time"]) - td.get("total_paused_duration", 0)
        td["elapsed_time"] = elapsed_time

        widget_frame = td["widget"]
        if widget_frame and widget_frame.winfo_exists():
            time_label = None
            for child in widget_frame.winfo_children():
                if isinstance(child, tk.Label) and "18" in child.cget("font"): # Ищем метку с большим шрифтом
                    time_label = child
                    break
            
            if time_label:
                if td.get("is_countdown"):
                    # Обратный таймер: оставшееся время
                    remaining_time = max(0, td.get("duration", 0) - int(elapsed_time))
                    hours = int(remaining_time // 3600)
                    minutes = int((remaining_time % 3600) // 60)
                    seconds = int(remaining_time % 60)
                    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                    time_label.config(text=time_str)

                    # Если время истекло и таймер еще не был помечен как завершенный
                    if remaining_time <= 0 and not td.get("completed"):
                        td["is_running"] = False
                        td["completed"] = True
                        if td.get("status_label"):
                            td["status_label"].config(text="ЗАВЕРШЁН", fg="red")
                        self._start_blink(timer_id, "red") # Начинаем мигать красным
                        self._play_sound() # Проигрываем звуковой сигнал
                        # Данные никуда не записываются (по условию для обратных таймеров)
                        self.app.save_config(show_message=False) # Сохраняем состояние завершения
                        return # Прекращаем дальнейшее обновление для этого таймера
                else:
                    # Основной таймер: прошедшее время
                    hours = int(elapsed_time // 3600)
                    minutes = int((elapsed_time % 3600) // 60)
                    seconds = int(elapsed_time % 60)
                    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                    time_label.config(text=time_str)

        # Планируем следующий апдейт, только если таймер всё ещё работает и не завершен
        if td.get("is_running") and not td.get("completed"):
            try:
                self.app.master.after(500, lambda tid=timer_id: self.update_timer_display(tid))
            except Exception:
                # Если мастер-окно уже недоступно (например, при закрытии приложения), просто выходим
                pass

    def stop_timer(self, timer_id):
        # Останавливает основной таймер и записывает работу.
        # Для обратных таймеров этот метод не вызывается при завершении (см. confirm_finish_timer)
        if timer_id not in self.app.active_timers:
            return

        td = self.app.active_timers[timer_id]
        
        # Если это обратный таймер, не записываем его в completed_jobs, просто удаляем виджет.
        if td.get("is_countdown"):
            self._cancel_blink(timer_id)
            if td["widget"]:
                td["widget"].destroy()
            del self.app.active_timers[timer_id]
            self.app.save_config(show_message=False)
            self.app.timers_list_frame.update_idletasks()
            self.app.timers_canvas.config(scrollregion=self.app.timers_canvas.bbox("all"))
            return

        td["is_running"] = False
        
        if td["pause_time"] > 0:
            paused_duration = time.time() - td["pause_time"]
            td["total_paused_duration"] += paused_duration
            
        final_elapsed_time = (time.time() - td["start_time"]) - td["total_paused_duration"]
        job_id = str(uuid.uuid4())
        
        job_entry = {
            "job_id": job_id,
            "device_name": td["device_name"],
            "device_type": td["device_type"],
            "work_type": td["work_type"],
            "time_worked": final_elapsed_time,
            "declared_time": td.get("declared_time", 0),
            "timestamp": time.time(),
            "author": self.app.global_author,
            "note": ""  # Добавляем пустое поле "примечание" при создании записи из таймера
        }
        self.app.completed_jobs.append(job_entry)

        self._cancel_blink(timer_id) # Отменяем мигание, если было
        if td["widget"]:
            td["widget"].destroy()
        
        del self.app.active_timers[timer_id]
        
        self.app.update_work_table_display()
        self.app.save_config(show_message=False)
        self.app.timers_list_frame.update_idletasks()
        self.app.timers_canvas.config(scrollregion=self.app.timers_canvas.bbox("all"))

    def stop_all_timers(self, show_message=True): # Добавил параметр для подавления сообщений при закрытии
        active_timers_copy = list(self.app.active_timers.keys()) # Итерировать по копии, чтобы избежать RuntimeError
        for timer_id in active_timers_copy:
            td = self.app.active_timers.get(timer_id)
            if td and td.get("is_countdown"):
                # Для обратных таймеров просто удаляем виджет и запись
                self._cancel_blink(timer_id)
                if td.get("widget"):
                    td["widget"].destroy()
                del self.app.active_timers[timer_id]
            else:
                self.stop_timer(timer_id) # Обычная остановка для основного
        
        self.app.save_config(show_message=False) # Сохраняем состояние после массовой остановки
        self.app.timers_list_frame.update_idletasks()
        self.app.timers_canvas.config(scrollregion=self.app.timers_canvas.bbox("all"))
        if show_message and active_timers_copy:
            self.app._show_messagebox("info", "Таймеры", "Все активные таймеры остановлены.")

    # --- Мигание: запускаем/отменяем по timer_id ---
    def _start_blink(self, timer_id, color):
        if timer_id not in self.app.active_timers:
            return
        td = self.app.active_timers[timer_id]
        
        # Если таймер уже мигает с тем же цветом, нет нужды перезапускать
        if timer_id in self._blink_jobs and td.get("blink_color_current") == color:
            return

        # Если мигает с другим цветом, сначала отменяем текущее мигание
        self._cancel_blink(timer_id)

        td["blink_color_current"] = color
        td["blink_state"] = False  # Текущее состояние: False => нормальный фон

        def _do_blink():
            if timer_id not in self.app.active_timers:
                self._cancel_blink(timer_id) # Таймер был удален
                return
            tdata = self.app.active_timers.get(timer_id)
            if not tdata or not tdata.get("widget") or not tdata["widget"].winfo_exists():
                self._cancel_blink(timer_id) # Виджет был уничтожен
                return

            widget = tdata["widget"]
            tdata["blink_state"] = not tdata.get("blink_state", False) # Переключаем состояние мигания

            if tdata["blink_state"]: # Если мигаем, ставим цвет
                bg_color = tdata.get("blink_color_current", "#c0c0c0")
            else: # Иначе, возвращаем стандартный
                bg_color = "#c0c0c0" # Стандартный серый цвет фона

            try:
                widget.configure(bg=bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=bg_color)
            except tk.TclError:
                # Окно может быть закрыто во время выполнения after, игнорируем ошибку
                self._cancel_blink(timer_id)
                return

            # Повторяем мигание
            jid = self.app.master.after(self.blink_interval, _do_blink)
            self._blink_jobs[timer_id] = jid

        _do_blink() # Запускаем первый цикл мигания

    def _cancel_blink(self, timer_id):
        if timer_id in self._blink_jobs:
            try:
                self.app.master.after_cancel(self._blink_jobs[timer_id])
            except Exception:
                pass # Пропускаем, если after_cancel вызван для уже завершенного job
            del self._blink_jobs[timer_id]

        td = self.app.active_timers.get(timer_id)
        if td:
            widget = td.get("widget")
            if widget and widget.winfo_exists():
                try:
                    widget.configure(bg="#c0c0c0") # Возвращаем стандартный фон
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label):
                            child.configure(bg="#c0c0c0")
                except tk.TclError:
                    pass # Игнорируем ошибки, если виджет уже удален
            td["blink_state"] = False

    def treeview_sort_column(self, tree, col, reverse):
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        
        def convert_value(val, col_name):
            if "мин" in col_name:
                try:
                    return float(val.replace(',', '.')) if val else 0.0
                except ValueError:
                    return 0.0
            elif "Время завершения" in col_name:
                try:
                    return datetime.fromisoformat(val) # Используем fromisoformat для лучшего парсинга
                except ValueError:
                    # Fallback для старых версий python или других форматов
                    try:
                        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        return datetime.min
            return val.lower()

        l.sort(key=lambda t: convert_value(t[0], tree.heading(col, 'text')), reverse=reverse)

        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)

        tree.heading(col, command=lambda c=col: self.app.treeview_sort_column(tree, c, not reverse))

    def open_work_table_dialog(self):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Таблица работ")
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()
        dialog.geometry("950x600")

        main_frame = tk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill="x", pady=5)
        
        btn_add = tk.Button(control_frame, text="Добавить запись", command=lambda: self.open_job_editor_dialog(dialog))
        btn_add.pack(side=tk.LEFT, padx=5)

        btn_edit = tk.Button(control_frame, text="Редактировать", command=lambda: self.edit_selected_job(dialog), state=tk.DISABLED)
        btn_edit.pack(side=tk.LEFT, padx=5)

        btn_delete = tk.Button(control_frame, text="Удалить", command=self.delete_selected_job, state=tk.DISABLED)
        btn_delete.pack(side=tk.LEFT, padx=5)
        
        export_button = tk.Button(control_frame, text="Экспорт в CSV", command=self.export_work_table_to_csv)
        export_button.pack(side=tk.LEFT, padx=5)

        # НОВАЯ КНОПКА: Управление типами
        btn_manage_types = tk.Button(control_frame, text="Управление типами", command=self.open_manage_types_dialog)
        btn_manage_types.pack(side=tk.RIGHT, padx=5) 

        columns = ("Timestamp", "Device", "DeviceType", "WorkType", "TimeWorked", "DeclaredTime", "Author")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        
        headers = {
            "Timestamp": "Время завершения", 
            "Device": "Устройство", 
            "DeviceType": "Тип устройства", 
            "WorkType": "Тип работ", 
            "TimeWorked": "Время работы (мин)", 
            "DeclaredTime": "Заявленное время (мин)", 
            "Author": "Автор"
        }

        for col, text in headers.items():
            tree.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(tree, c, False))
        
        def enable_buttons(event):
            selected_items = tree.selection()
            if selected_items:
                btn_edit.config(state=tk.NORMAL)
                btn_delete.config(state=tk.NORMAL)
            else:
                btn_edit.config(state=tk.DISABLED)
                btn_delete.config(state=tk.DISABLED)
                
        tree.bind("<<TreeviewSelect>>", enable_buttons)

        tree.column("Timestamp", width=150, anchor=tk.W)
        tree.column("Device", width=150, anchor=tk.W)
        tree.column("DeviceType", width=120, anchor=tk.W)
        tree.column("WorkType", width=120, anchor=tk.W)
        tree.column("TimeWorked", width=100, anchor=tk.E)
        tree.column("DeclaredTime", width=120, anchor=tk.E)
        tree.column("Author", width=80, anchor=tk.W) 

        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=vsb.set)
        
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
        hsb.pack(side="bottom", fill="x")
        tree.configure(xscrollcommand=hsb.set)

        tree.pack(fill="both", expand=True)

        self.app.work_table_tree = tree
        self.update_work_table_display()

        # Новое: двойной клик по строке открывает редактор записи
        def _on_tree_double_click(event):
            row_id = tree.identify_row(event.y)
            if not row_id:
                return
            job = self._find_job_by_id(row_id)
            if job:
                # Открываем диалог редактирования, передаём конкретный объект job
                self.open_job_editor_dialog(dialog, job_data=job)

        tree.bind("<Double-1>", _on_tree_double_click)
        
        dialog.wait_window()

    def update_work_table_display(self):
        if hasattr(self.app, 'work_table_tree') and self.app.work_table_tree and self.app.work_table_tree.winfo_exists():
            for item in self.app.work_table_tree.get_children():
                self.app.work_table_tree.delete(item)
            
            sorted_jobs = sorted(self.app.completed_jobs, key=lambda x: x.get('timestamp', 0), reverse=True)
            
            for job in sorted_jobs:
                timestamp_str = datetime.fromtimestamp(job.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')
                
                time_worked_sec = job.get('time_worked', 0)
                time_worked_min = time_worked_sec / 60.0
                time_worked_str = f"{time_worked_min:.2f}"
                
                declared_time_sec = job.get('declared_time', 0)
                declared_time_min = declared_time_sec / 60.0 if declared_time_sec > 0 else 0
                declared_time_str = f"{declared_time_min:.2f}" if declared_time_min > 0 else ''

                job_id = job.get('job_id', str(uuid.uuid4()))

                self.app.work_table_tree.insert("", "end", iid=job_id, values=(
                    timestamp_str,
                    job.get("device_name", ""),
                    job.get("device_type", ""),
                    job.get("work_type", ""),
                    time_worked_str,
                    declared_time_str,
                    job.get("author", "")
                ))

    def _find_job_by_id(self, job_id):
        for job in self.app.completed_jobs:
            if job.get('job_id') == job_id:
                return job
        return None

    def open_job_editor_dialog(self, parent_dialog, job_data=None):
        is_editing = job_data is not None
        
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Редактировать работу" if is_editing else "Добавить работу")
        self.app.center_window(dialog)
        dialog.transient(parent_dialog)
        dialog.grab_set()

        initial_device_name = job_data.get("device_name", "") if is_editing else ""
        initial_device_type = job_data.get("device_type", "") if is_editing else (self.app.device_types[0] if self.app.device_types else "")
        initial_work_type = job_data.get("work_type", "") if is_editing else (self.app.work_types[0] if self.app.work_types else "")
        initial_time_worked_min = job_data.get("time_worked", 0) / 60 if is_editing else 0
        initial_declared_time_min = job_data.get("declared_time", 0) / 60 if is_editing else 0
        initial_note = job_data.get("note", "") if is_editing else ""  # начальное значение для поля "примечание"
        
        row = 0
        
        tk.Label(dialog, text="Название устройства:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        device_name_entry = tk.Entry(dialog)
        device_name_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        device_name_entry.insert(0, initial_device_name)
        row += 1

        tk.Label(dialog, text="Тип устройства:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        device_type_var = tk.StringVar(value=initial_device_type)
        device_type_combo = ttk.Combobox(dialog, textvariable=device_type_var, values=self.app.device_types, state="readonly")
        device_type_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        tk.Label(dialog, text="Тип работ:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        work_type_var = tk.StringVar(value=initial_work_type)
        work_type_combo = ttk.Combobox(dialog, textvariable=work_type_var, values=self.app.work_types, state="readonly")
        work_type_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1
        
        tk.Label(dialog, text="Время работы (мин):").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        time_worked_var = tk.StringVar(value=f"{initial_time_worked_min:.2f}".replace('.', ','))
        time_worked_entry = tk.Entry(dialog, textvariable=time_worked_var)
        time_worked_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        tk.Label(dialog, text="Заявленное время (мин):").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        declared_time_var = tk.StringVar(value=f"{initial_declared_time_min:.2f}".replace('.', ','))
        declared_time_entry = tk.Entry(dialog, textvariable=declared_time_var)
        declared_time_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1
        
        tk.Label(dialog, text="Автор:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        author_var = tk.StringVar(value=job_data.get("author", self.app.global_author) if is_editing else self.app.global_author)
        author_entry = tk.Entry(dialog, textvariable=author_var)
        author_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        tk.Label(dialog, text="Примечание:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.NW)
        note_frame = tk.Frame(dialog)
        note_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        note_text = tk.Text(note_frame, height=6, wrap='word')
        note_text.insert("1.0", initial_note)
        note_text.pack(side=tk.LEFT, fill="both", expand=True)
        note_vsb = ttk.Scrollbar(note_frame, orient="vertical", command=note_text.yview)
        note_vsb.pack(side=tk.RIGHT, fill="y")
        note_text.configure(yscrollcommand=note_vsb.set)
        row += 1
        
        def save_job():
            device_name = device_name_entry.get().strip()
            if not device_name:
                self.app._show_messagebox("warning", "Предупреждение", "Название устройства обязательно.")
                return
            
            try:
                time_worked_min = float(time_worked_var.get().replace(',', '.'))
                declared_time_min = float(declared_time_var.get().replace(',', '.'))
            except ValueError:
                self.app._show_messagebox("error", "Ошибка ввода", "Время должно быть числом.")
                return

            time_worked_sec = time_worked_min * 60
            declared_time_sec = declared_time_min * 60

            note_value = note_text.get("1.0", "end").rstrip("\n")

            new_job_data = {
                "device_name": device_name,
                "device_type": device_type_var.get(),
                "work_type": work_type_var.get(),
                "time_worked": time_worked_sec,
                "declared_time": declared_time_sec,
                "author": author_var.get(),
                "note": note_value
            }
            
            if is_editing:
                job_data.update(new_job_data)
            else:
                new_job_data["job_id"] = str(uuid.uuid4())
                new_job_data["timestamp"] = time.time()
                self.app.completed_jobs.append(new_job_data)

            self.app.save_config(show_message=False)
            self.app.update_work_table_display()
            dialog.destroy()

        save_button = tk.Button(dialog, text="Сохранить" if is_editing else "Добавить", command=save_job)
        save_button.grid(row=row, column=0, columnspan=2, padx=5, pady=10)

        dialog.columnconfigure(1, weight=1)
        dialog.rowconfigure(row-1, weight=1)
        dialog.wait_window()

    def delete_selected_job(self):
        if not self.app.work_table_tree:
            return

        selected_item_id = self.app.work_table_tree.selection()
        if not selected_item_id:
            self.app._show_messagebox("warning", "Удаление", "Выберите строку для удаления.")
            return
            
        job_id_to_delete = selected_item_id[0]
        job_to_delete = self._find_job_by_id(job_id_to_delete)

        if job_to_delete and self.app._show_messagebox("askyesno", "Подтверждение удаления", 
                                                   f"Вы уверены, что хотите удалить запись о работе '{job_to_delete['device_name']}'?"):
            
            self.app.completed_jobs.remove(job_to_delete)
            self.app.save_config(show_message=False)
            self.app.update_work_table_display()

    def edit_selected_job(self, parent_dialog):
        if not self.app.work_table_tree:
            return

        selected_item_id = self.app.work_table_tree.selection()
        if not selected_item_id:
            return

        job_id_to_edit = selected_item_id[0]
        job_data = self._find_job_by_id(job_id_to_edit)

        if job_data:
            self.open_job_editor_dialog(parent_dialog, job_data=job_data)

    def export_work_table_to_csv(self):
        if not self.app.completed_jobs:
            self.app._show_messagebox("warning", "Экспорт", "Нет данных для экспорта.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Сохранить таблицу работ как CSV"
        )
        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';') 
                
                header = ["Время завершения", "Устройство", "Тип устройства", "Тип работ", "Время работы (мин)", "Заявленное время (мин)", "Автор", "Примечание"]
                writer.writerow(header)

                for job in self.app.completed_jobs:
                    timestamp_str = datetime.fromtimestamp(job.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')
                    time_worked_min = job.get('time_worked', 0) / 60.0
                    declared_time_min = job.get('declared_time', 0) / 60.0 if job.get('declared_time', 0) > 0 else 0

                    row = [
                        timestamp_str,
                        job.get("device_name", ""),
                        job.get("device_type", ""),
                        job.get("work_type", ""),
                        f"{time_worked_min:.2f}".replace('.', ','),
                        f"{declared_time_min:.2f}".replace('.', ',') if declared_time_min > 0 else "",
                        job.get("author", ""),
                        job.get("note", "")
                    ]
                    writer.writerow(row)
            
            self.app._show_messagebox("info", "Экспорт", f"Данные успешно экспортированы в {filename}")

        except Exception as e:
            self.app._show_messagebox("error", "Ошибка экспорта", f"Произошла ошибка при экспорте: {e}")

    def open_manage_types_dialog(self):
        dialog = tk.Toplevel(self.app.master)
        dialog.title("Управление типами")
        self.app.center_window(dialog)
        dialog.transient(self.app.master)
        dialog.grab_set()
        dialog.geometry("800x500")
        dialog.minsize(600, 400)
        dialog.resizable(True, True)

        temp_work_types = list(self.app.work_types)
        temp_device_types = list(self.app.device_types)

        main_frame = tk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        work_types_frame = tk.Frame(main_frame, bd=2, relief=tk.GROOVE, padx=5, pady=5)
        work_types_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        tk.Label(work_types_frame, text="Типы работ", font=("Arial", 10, "bold")).pack(pady=5)

        work_control_frame = tk.Frame(work_types_frame)
        work_control_frame.pack(fill="x", pady=(0, 5))

        device_types_frame = tk.Frame(main_frame, bd=2, relief=tk.GROOVE, padx=5, pady=5)
        device_types_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(1, weight=1)

        tk.Label(device_types_frame, text="Типы устройств", font=("Arial", 10, "bold")).pack(pady=5)

        device_control_frame = tk.Frame(device_types_frame)
        device_control_frame.pack(fill="x", pady=(0, 5))

        def _update_tree(tree, data_list):
            for item in tree.get_children():
                tree.delete(item)
            data_list.sort()
            for item_text in data_list:
                tree.insert("", "end", values=(item_text,))
        
        def _open_type_editor_dialog(parent, current_value, title, type_list, tree_widget, is_new_entry=False):
            editor_dialog = tk.Toplevel(parent)
            editor_dialog.title(f"{'Добавить' if is_new_entry else 'Редактировать'} {title}")
            self.app.center_window(editor_dialog)
            editor_dialog.transient(parent)
            editor_dialog.grab_set()

            tk.Label(editor_dialog, text=f"{'Новый' if is_new_entry else 'Редактировать'} {title}:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            entry = tk.Entry(editor_dialog, width=30)
            entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
            entry.insert(0, current_value)
            entry.focus_set()

            def save_change():
                new_type_name = entry.get().strip()
                if not new_type_name:
                    self.app._show_messagebox("warning", "Предупреждение", "Название типа не может быть пустым.")
                    return
                
                if is_new_entry:
                    if new_type_name in type_list:
                        self.app._show_messagebox("warning", "Предупреждение", f"Тип '{new_type_name}' уже существует.")
                        return
                    type_list.append(new_type_name)
                else:
                    if new_type_name == current_value:
                        editor_dialog.destroy()
                        return

                    if new_type_name in type_list and new_type_name != current_value:
                        self.app._show_messagebox("warning", "Предупреждение", f"Тип '{new_type_name}' уже существует.")
                        return
                    
                    try:
                        index = type_list.index(current_value)
                        type_list[index] = new_type_name
                    except ValueError:
                        pass
                
                _update_tree(tree_widget, type_list)
                editor_dialog.destroy()

            btn_save = tk.Button(editor_dialog, text="Сохранить", command=save_change)
            btn_save.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

            editor_dialog.bind("<Return>", lambda event: save_change())
            editor_dialog.bind("<Escape>", lambda event: editor_dialog.destroy())
            editor_dialog.columnconfigure(1, weight=1)
            editor_dialog.wait_window()

        def _add_type_action(tree, type_list, title):
            _open_type_editor_dialog(dialog, "", title, type_list, tree, is_new_entry=True)

        def _delete_type_action(tree, type_list, title):
            selected_item_id = tree.selection()
            if not selected_item_id:
                self.app._show_messagebox("warning", "Удаление", f"Выберите {title.lower()} для удаления.")
                return

            item_text = tree.item(selected_item_id[0], 'values')[0]

            if not self.app._show_messagebox("askyesno", "Подтверждение удаления", 
                                          f"Вы уверены, что хотите удалить '{item_text}' из {title.lower()}?\n"
                                          "Это не изменит уже созданные записи, но удалит тип из списка выбора."):
                return
            
            if item_text in type_list:
                type_list.remove(item_text)
                _update_tree(tree, type_list)

        def _edit_type_action(event, tree, type_list, title):
            selected_item_id = tree.selection()
            if not selected_item_id:
                return
            
            if not tree.identify_row(event.y): 
                return

            item_text = tree.item(selected_item_id[0], 'values')[0]
            _open_type_editor_dialog(dialog, item_text, title, type_list, tree, is_new_entry=False)

        work_tree = ttk.Treeview(work_types_frame, columns=("Type",), show="headings", selectmode="browse")
        work_tree.heading("Type", text="Тип работ")
        work_tree.column("Type", width=200, anchor=tk.W)
        work_tree.pack(fill="both", expand=True)

        work_vsb = ttk.Scrollbar(work_types_frame, orient="vertical", command=work_tree.yview)
        work_vsb.pack(side="right", fill="y")
        work_tree.configure(yscrollcommand=work_vsb.set)
        
        btn_add_work_type = tk.Button(work_control_frame, text="Добавить", command=lambda: _add_type_action(work_tree, temp_work_types, "Тип работ"))
        btn_add_work_type.pack(side=tk.LEFT, padx=(0,5))
        btn_del_work_type = tk.Button(work_control_frame, text="Удалить", command=lambda: _delete_type_action(work_tree, temp_work_types, "Тип работ"))
        btn_del_work_type.pack(side=tk.LEFT)

        work_tree.bind("<Double-1>", lambda e: _edit_type_action(e, work_tree, temp_work_types, "Тип работ"))
        work_tree.bind("<Delete>", lambda e: _delete_type_action(work_tree, temp_work_types, "Тип работ"))
        _update_tree(work_tree, temp_work_types)

        device_tree = ttk.Treeview(device_types_frame, columns=("Type",), show="headings", selectmode="browse")
        device_tree.heading("Type", text="Тип устройства")
        device_tree.column("Type", width=200, anchor=tk.W)
        device_tree.pack(fill="both", expand=True)

        device_vsb = ttk.Scrollbar(device_types_frame, orient="vertical", command=device_tree.yview)
        device_vsb.pack(side="right", fill="y")
        device_tree.configure(yscrollcommand=device_vsb.set)

        btn_add_device_type = tk.Button(device_control_frame, text="Добавить", command=lambda: _add_type_action(device_tree, temp_device_types, "Тип устройства"))
        btn_add_device_type.pack(side=tk.LEFT, padx=(0,5))
        btn_del_device_type = tk.Button(device_control_frame, text="Удалить", command=lambda: _delete_type_action(device_tree, temp_device_types, "Тип устройства"))
        btn_del_device_type.pack(side=tk.LEFT)

        device_tree.bind("<Double-1>", lambda e: _edit_type_action(e, device_tree, temp_device_types, "Тип устройства"))
        device_tree.bind("<Delete>", lambda e: _delete_type_action(device_tree, temp_device_types, "Тип устройства"))
        _update_tree(device_tree, temp_device_types)

        bottom_frame = tk.Frame(dialog)
        bottom_frame.pack(fill="x", pady=10)

        def finalize_changes():
            self.app.work_types[:] = temp_work_types
            self.app.device_types[:] = temp_device_types
            self.app.save_config(show_message=True)

            dialog.destroy()

        btn_save_all = tk.Button(bottom_frame, text="Сохранить", command=finalize_changes)
        btn_save_all.pack(side=tk.RIGHT, padx=5)

        btn_cancel = tk.Button(bottom_frame, text="Отмена", command=dialog.destroy)
        btn_cancel.pack(side=tk.RIGHT)

        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.wait_window()
