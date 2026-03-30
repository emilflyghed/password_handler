import time
import customtkinter as ctk

from config import APP_TITLE, APP_SIZE, APP_MIN_SIZE, AUTO_LOCK_SECONDS
from database.db import get_connection, is_first_run
from database.models import get_config, set_config
from crypto.encryption import zero_key
from gui.login_frame import LoginFrame
from gui.main_frame import MainFrame


class PasswordVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        self.minsize(*APP_MIN_SIZE)

        self.conn = get_connection()
        self._key = None
        self._idle_deadline = None
        self._tick_job = None
        self._first_run = is_first_run(self.conn)

        ctk.set_appearance_mode("dark")

        self.login_frame = None
        self.main_frame = None

        self._show_login()

        # bind_all catches events from ALL windows including Toplevel dialogs
        self.bind_all("<Motion>", self._on_activity)
        self.bind_all("<Key>", self._on_activity)
        self.bind_all("<Button>", self._on_activity)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _show_login(self):
        self._stop_timer()
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None
        self.login_frame = LoginFrame(self, self.conn, self._first_run)
        self.login_frame.pack(fill="both", expand=True)

    def on_login_success(self, key: bytearray):
        self._key = key
        self._first_run = False
        if self.login_frame:
            self.login_frame.destroy()
            self.login_frame = None
        self.main_frame = MainFrame(self, self.conn, self._key)
        self.main_frame.pack(fill="both", expand=True)
        self._start_timer()

    def lock(self):
        self._stop_timer()
        # Close any open Toplevel dialogs (generator, entry dialog, etc.)
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkToplevel):
                widget.destroy()
        if self._key:
            zero_key(self._key)
            self._key = None
        self._show_login()

    def get_remaining_seconds(self) -> int:
        if self._idle_deadline is None:
            return 0
        remaining = self._idle_deadline - time.monotonic()
        return max(0, int(remaining))

    def _on_activity(self, event=None):
        if self._key is None:
            return
        self._idle_deadline = time.monotonic() + AUTO_LOCK_SECONDS

    def _start_timer(self):
        self._idle_deadline = time.monotonic() + AUTO_LOCK_SECONDS
        self._tick()

    def _stop_timer(self):
        self._idle_deadline = None
        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None

    def _tick(self):
        if self._key is None or self._idle_deadline is None:
            return

        remaining = self._idle_deadline - time.monotonic()

        if remaining <= 0:
            self.lock()
            return

        # Update the timer label in main_frame
        if self.main_frame:
            self.main_frame.update_timer(int(remaining))

        self._tick_job = self.after(500, self._tick)

    def _on_close(self):
        self._stop_timer()
        if self._key:
            zero_key(self._key)
        self.conn.close()
        self.destroy()
