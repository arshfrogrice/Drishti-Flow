"""CustomTkinter dashboard for Drishti-Flow.

All Tk GUI updates and webcam reads happen on the main thread through .after().
No cv2.imshow() windows: the live preview is embedded in this dashboard.
"""

import time
import tkinter as tk
from tkinter import messagebox

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps

import config as cfg
from detector import HabitDetector
from intervention import EpisodeTracker, apply_blur


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DrishtiFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=cfg.BG)
        self.title("Drishti-Flow | Habit Awareness")
        self.geometry("1180x770")
        self.minsize(1040, 690)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.capture = None
        self.detector = None
        self.mode = "stopped"  # stopped | running | paused
        self.tracker = EpisodeTracker()
        self._frame_job = None
        self._clock_job = None
        self._image_ref = None
        self._active_since = None
        self._accumulated_seconds = 0.0
        self._last_event = "None yet"

        self.enabled_vars = {habit: tk.BooleanVar(value=True) for habit in cfg.HABITS}
        self.sensitivity_var = tk.DoubleVar(value=1.0)
        self._build_layout()
        self._refresh_ui()
        self._refresh_clock()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=258, corner_radius=0, fg_color=cfg.SURFACE)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        logo = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, padx=20, pady=(27, 5), sticky="ew")
        ctk.CTkLabel(logo, text="◉  DRISHTI-FLOW", font=("Arial", 21, "bold"),
                     text_color=cfg.TEXT).pack(anchor="w")
        ctk.CTkLabel(logo, text="REAL-TIME HABIT AWARENESS",
                     font=("Arial", 10, "bold"), text_color=cfg.MUTED).pack(anchor="w", pady=(3, 0))

        ctk.CTkLabel(sidebar, text="SESSION", font=("Arial", 11, "bold"),
                     text_color=cfg.MUTED).grid(row=1, column=0, padx=22, pady=(34, 10), sticky="w")

        self.start_button = ctk.CTkButton(
            sidebar, text="▶   Start session", height=42, fg_color=cfg.ACCENT,
            command=self._start_new_session, font=("Arial", 13, "bold"))
        self.start_button.grid(row=2, column=0, padx=18, pady=5, sticky="ew")

        self.pause_button = ctk.CTkButton(
            sidebar, text="Ⅱ   Pause", height=39, fg_color=cfg.PANEL,
            hover_color=cfg.BORDER, command=self._toggle_pause)
        self.pause_button.grid(row=3, column=0, padx=18, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(
            sidebar, text="■   Stop session", height=39, fg_color=cfg.PANEL,
            hover_color=cfg.BORDER, command=self._stop_session)
        self.stop_button.grid(row=4, column=0, padx=18, pady=5, sticky="ew")

        ctk.CTkLabel(sidebar, text="TRACK HABITS", font=("Arial", 11, "bold"),
                     text_color=cfg.MUTED).grid(row=5, column=0, padx=22, pady=(34, 12), sticky="w")

        for i, label in enumerate(cfg.HABITS):
            ctk.CTkCheckBox(
                sidebar, text=label, variable=self.enabled_vars[label],
                command=self._on_settings_changed, checkbox_width=20,
                checkbox_height=20, font=("Arial", 12),
                fg_color=cfg.ACCENT, hover_color=cfg.ACCENT,
            ).grid(row=6 + i, column=0, padx=22, pady=7, sticky="w")

        ctk.CTkLabel(sidebar, text="SENSITIVITY", font=("Arial", 11, "bold"),
                     text_color=cfg.MUTED).grid(row=9, column=0, padx=22, pady=(34, 8), sticky="w")
        self.sensitivity_label = ctk.CTkLabel(
            sidebar, text="100% (default)", font=("Arial", 12),
            text_color=cfg.TEXT)
        self.sensitivity_label.grid(row=10, column=0, padx=22, sticky="w")
        self.sensitivity_slider = ctk.CTkSlider(
            sidebar, from_=0.75, to=1.25, number_of_steps=20,
            variable=self.sensitivity_var, command=self._on_sensitivity_changed,
            progress_color=cfg.ACCENT, button_color=cfg.ACCENT,
        )
        self.sensitivity_slider.grid(row=11, column=0, padx=18, pady=(10, 3), sticky="ew")
        ctk.CTkLabel(sidebar, text="Adjusts gesture proximity thresholds.",
                     text_color=cfg.MUTED, font=("Arial", 10)).grid(
                         row=12, column=0, padx=22, sticky="w")

        sidebar.grid_rowconfigure(13, weight=1)
        ctk.CTkLabel(sidebar,
                     text="Privacy first\nVideo stays on this device.\nNo frames are uploaded or saved.",
                     justify="left", text_color=cfg.MUTED,
                     font=("Arial", 11)).grid(
                         row=14, column=0, padx=22, pady=(0, 23), sticky="w")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, padx=24, pady=24, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        heading = ctk.CTkFrame(main, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        heading.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(heading, text="Live monitoring", font=("Arial", 28, "bold"),
                     text_color=cfg.TEXT).grid(row=0, column=0, sticky="w")
        self.badge = ctk.CTkLabel(heading, text="●  Not started", width=144,
                                  corner_radius=12, height=30,
                                  fg_color=cfg.PANEL, text_color=cfg.MUTED,
                                  font=("Arial", 12, "bold"))
        self.badge.grid(row=0, column=1, sticky="e")

        self.subtitle = ctk.CTkLabel(
            main, text="Your webcam preview will appear when you start a session.",
            text_color=cfg.MUTED, anchor="w", font=("Arial", 12))
        self.subtitle.grid(row=1, column=0, pady=(0, 12), sticky="ew")

        preview_outer = ctk.CTkFrame(main, fg_color=cfg.SURFACE,
                                      corner_radius=16, border_width=1,
                                      border_color=cfg.BORDER)
        preview_outer.grid(row=2, column=0, sticky="nsew")
        preview_outer.grid_rowconfigure(0, weight=1)
        preview_outer.grid_columnconfigure(0, weight=1)
        self.preview = tk.Label(
            preview_outer, bg="#080F1C", fg="#A7B8CD",
            text="Camera off\n\nPress Start session to begin",
            font=("Arial", 17), justify="center", relief="flat")
        self.preview.grid(row=0, column=0, padx=11, pady=11, sticky="nsew")
        self.preview.bind("<Configure>", self._preview_resize)
        self._preview_size = (cfg.PREVIEW_WIDTH, cfg.PREVIEW_HEIGHT)

        row = ctk.CTkFrame(main, fg_color="transparent")
        row.grid(row=3, column=0, pady=(16, 0), sticky="ew")
        for i in range(3):
            row.grid_columnconfigure(i, weight=1, uniform="stats")
        self.count_widgets = {}
        titles = {cfg.NOSE: "NOSE FINGERING", cfg.FACE: "FACE TOUCHING",
                  cfg.NAIL: "POSSIBLE NAIL BITING"}
        for i, habit in enumerate(cfg.HABITS):
            card = ctk.CTkFrame(row, fg_color=cfg.SURFACE, corner_radius=12,
                                border_width=1, border_color=cfg.BORDER)
            card.grid(row=0, column=i, padx=(0 if i == 0 else 5, 0 if i == 2 else 5),
                      sticky="ew")
            ctk.CTkLabel(card, text=titles[habit], font=("Arial", 10, "bold"),
                         text_color=cfg.MUTED).pack(anchor="w", padx=18, pady=(13, 2))
            counter = ctk.CTkLabel(card, text="0", font=("Arial", 30, "bold"),
                                   text_color=cfg.TEXT)
            counter.pack(anchor="w", padx=18, pady=(0, 12))
            self.count_widgets[habit] = counter

        footer = ctk.CTkFrame(main, fg_color=cfg.SURFACE, corner_radius=12)
        footer.grid(row=4, column=0, pady=(14, 0), sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(footer, text="SESSION TIME", font=("Arial", 10, "bold"),
                     text_color=cfg.MUTED).grid(row=0, column=0, padx=(17, 9), pady=14)
        self.timer_label = ctk.CTkLabel(footer, text="00:00", font=("Arial", 17, "bold"),
                                       text_color=cfg.TEXT)
        self.timer_label.grid(row=0, column=1, sticky="w")
        self.last_event_label = ctk.CTkLabel(footer, text="Last detection: None yet",
                                               font=("Arial", 11), text_color=cfg.MUTED)
        self.last_event_label.grid(row=0, column=2, padx=16, sticky="e")

    def _preview_resize(self, event):
        # Image dimensions reflect available frame area, without enlargement beyond source.
        self._preview_size = (max(event.width - 4, 120), max(event.height - 4, 90))

    def _on_sensitivity_changed(self, _value=None):
        value = self.sensitivity_var.get()
        text = f"{round(value * 100)}%" + (" (default)" if abs(value - 1) < 0.001 else "")
        self.sensitivity_label.configure(text=text)
        self.tracker.reset_candidate()

    def _on_settings_changed(self):
        self.tracker.reset_candidate()

    def _start_new_session(self):
        if self.mode != "stopped":
            return
        self.tracker.reset_session()
        self._last_event = "None yet"
        self._accumulated_seconds = 0
        self._active_since = None
        if self._open_camera_and_models():
            self.mode = "running"
            self._active_since = time.monotonic()
            self._refresh_ui()
            self._schedule_next_frame()

    def _open_camera_and_models(self):
        cap = cv2.VideoCapture(cfg.CAMERA_INDEX)
        if not cap.isOpened():
            cap.release()
            messagebox.showerror(
                "Camera unavailable",
                "Cannot access webcam. Close other camera apps, check camera permissions, "
                "and verify CAMERA_INDEX in config.py.",
                parent=self,
            )
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.CAMERA_HEIGHT)
        try:
            detector = HabitDetector()
        except Exception as exc:
            cap.release()
            messagebox.showerror("Detector error", f"Unable to start MediaPipe:\n{exc}",
                                 parent=self)
            return False
        self.capture = cap
        self.detector = detector
        return True

    def _release_camera_and_models(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        if self.detector is not None:
            self.detector.close()
            self.detector = None

    def _cancel_frame_job(self):
        if self._frame_job is not None:
            try:
                self.after_cancel(self._frame_job)
            except ValueError:
                pass
            self._frame_job = None

    def _toggle_pause(self):
        if self.mode == "running":
            self._cancel_frame_job()
            if self._active_since is not None:
                self._accumulated_seconds += time.monotonic() - self._active_since
                self._active_since = None
            self._release_camera_and_models()
            self.tracker.reset_candidate()
            self.mode = "paused"
            self._set_placeholder("Session paused\n\nCamera is off")
            self._refresh_ui()
        elif self.mode == "paused":
            if self._open_camera_and_models():
                self.mode = "running"
                self._active_since = time.monotonic()
                self._refresh_ui()
                self._schedule_next_frame()

    def _stop_session(self):
        if self.mode == "stopped":
            return
        self._cancel_frame_job()
        if self._active_since is not None:
            self._accumulated_seconds += time.monotonic() - self._active_since
            self._active_since = None
        self._release_camera_and_models()
        self.tracker.reset_candidate()
        self.mode = "stopped"
        self._set_placeholder("Session stopped\n\nPress Start session to begin again")
        self._refresh_ui()

    def _set_placeholder(self, text):
        self.preview.configure(image="", text=text, fg="#A7B8CD")
        self._image_ref = None

    def _schedule_next_frame(self):
        self._frame_job = self.after(cfg.FRAME_INTERVAL_MS, self._process_frame)

    def _process_frame(self):
        self._frame_job = None
        if self.mode != "running":
            return
        try:
            ok, frame = self.capture.read()
            if not ok:
                raise RuntimeError("Could not read a frame from webcam.")
            frame = cv2.flip(frame, 1)
            enabled = {h for h, var in self.enabled_vars.items() if var.get()}
            candidate = self.detector.process(
                frame, sensitivity=float(self.sensitivity_var.get()), enabled=enabled
            ) if enabled else None
            now = time.monotonic()
            detection = self.tracker.update(candidate, now)
            if detection.new_event:
                self._last_event = detection.candidate
                self._refresh_counts()
            if detection.confirmed:
                frame = apply_blur(frame)
                self.subtitle.configure(text=f"Pause. Notice the moment.  •  {candidate}",
                                        text_color=cfg.DANGER)
                self.badge.configure(text="●  Habit detected",
                                     fg_color="#3F2633", text_color=cfg.DANGER)
                status = f"PAUSE  •  {candidate}"
                color = (135, 131, 243)
            elif detection.candidate:
                self.subtitle.configure(text=f"Checking gesture: {candidate}",
                                        text_color=cfg.WARNING)
                self.badge.configure(text="●  Checking", fg_color="#3B3226",
                                     text_color=cfg.WARNING)
                status = "Checking..."
                color = (106, 192, 245)
            else:
                self.subtitle.configure(text="Tracking hand and facial landmarks locally.",
                                        text_color=cfg.MUTED)
                self.badge.configure(text="●  Monitoring", fg_color="#17382F",
                                     text_color=cfg.SUCCESS)
                status = "Monitoring"
                color = (164, 214, 82)

            cv2.putText(frame, status, (18, 32), cv2.FONT_HERSHEY_SIMPLEX,
                        0.82, color, 2, cv2.LINE_AA)
            self._update_preview(frame)
        except Exception as exc:
            self._stop_session()
            messagebox.showerror("Monitoring stopped", f"An error occurred:\n{exc}",
                                 parent=self)
            return

        self._schedule_next_frame()

    def _update_preview(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        size = self._preview_size
        # Fit within the available preview area without cropping video.
        image = ImageOps.contain(image, size, method=Image.Resampling.BILINEAR)
        tk_image = ImageTk.PhotoImage(image, master=self.preview)
        self.preview.configure(image=tk_image, text="")
        self._image_ref = tk_image  # Keep reference so Tk doesn't blank the image.

    def _refresh_counts(self):
        for habit in cfg.HABITS:
            self.count_widgets[habit].configure(text=str(self.tracker.counts[habit]))
        self.last_event_label.configure(text=f"Last detection: {self._last_event}")

    def _refresh_ui(self):
        running = self.mode == "running"
        paused = self.mode == "paused"
        self.start_button.configure(state="normal" if self.mode == "stopped" else "disabled")
        self.pause_button.configure(
            state="normal" if self.mode != "stopped" else "disabled",
            text="▶   Resume" if paused else "Ⅱ   Pause",
        )
        self.stop_button.configure(state="normal" if self.mode != "stopped" else "disabled")
        if not running:
            name = "Paused" if paused else "Not monitoring"
            self.badge.configure(text=f"●  {name}", fg_color=cfg.PANEL,
                                 text_color=cfg.MUTED)
            self.subtitle.configure(text="Camera off. Your video stays on this device.",
                                    text_color=cfg.MUTED)
        self._refresh_counts()

    def _refresh_clock(self):
        elapsed = self._accumulated_seconds
        if self._active_since is not None:
            elapsed += time.monotonic() - self._active_since
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        self.timer_label.configure(
            text=f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else
                 f"{minutes:02d}:{seconds:02d}"
        )
        self._clock_job = self.after(250, self._refresh_clock)

    def _on_close(self):
        self._cancel_frame_job()
        if self._clock_job is not None:
            self.after_cancel(self._clock_job)
            self._clock_job = None
        self._release_camera_and_models()
        self.destroy()
