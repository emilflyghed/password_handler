import customtkinter as ctk
from database.db import is_first_run
from database.models import setup_pin, verify_pin
from config import PIN_MIN_LENGTH, PIN_MAX_LENGTH


class LoginFrame(ctk.CTkFrame):
    def __init__(self, app, conn, first_run: bool):
        super().__init__(app, fg_color="transparent")
        self.app = app
        self.conn = conn
        self.first_run = first_run
        self._failed_attempts = 0
        self._locked_out = False

        # Center container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.place(relx=0.5, rely=0.45, anchor="center")

        # Shield icon / title
        self.icon_label = ctk.CTkLabel(
            self.container,
            text="\U0001f512",
            font=ctk.CTkFont(size=48),
        )
        self.icon_label.pack(pady=(0, 8))

        self.title_label = ctk.CTkLabel(
            self.container,
            text="Password Vault",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.title_label.pack(pady=(0, 4))

        self.subtitle_label = ctk.CTkLabel(
            self.container,
            text="Create your PIN to get started" if first_run else "Enter your PIN to unlock",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="gray",
        )
        self.subtitle_label.pack(pady=(0, 24))

        # PIN entry
        self.pin_label = ctk.CTkLabel(
            self.container,
            text="PIN" if not first_run else "Create PIN",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self.pin_label.pack(fill="x", padx=40)

        self.pin_entry = ctk.CTkEntry(
            self.container,
            show="●",
            width=280,
            height=44,
            font=ctk.CTkFont(size=18, weight="bold"),
            justify="center",
            placeholder_text=f"{PIN_MIN_LENGTH}-{PIN_MAX_LENGTH} digits",
            corner_radius=10,
        )
        self.pin_entry.pack(pady=(4, 12), padx=40)
        self.pin_entry.bind("<Return>", self._on_submit)

        # Confirm PIN (first run only)
        self.confirm_entry = None
        if first_run:
            self.confirm_label = ctk.CTkLabel(
                self.container,
                text="Confirm PIN",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
            )
            self.confirm_label.pack(fill="x", padx=40)

            self.confirm_entry = ctk.CTkEntry(
                self.container,
                show="●",
                width=280,
                height=44,
                font=ctk.CTkFont(size=18, weight="bold"),
                justify="center",
                placeholder_text=f"Re-enter your PIN",
                corner_radius=10,
            )
            self.confirm_entry.pack(pady=(4, 12), padx=40)
            self.confirm_entry.bind("<Return>", self._on_submit)

        # Submit button
        self.submit_btn = ctk.CTkButton(
            self.container,
            text="Create Vault" if first_run else "Unlock",
            width=280,
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=10,
            fg_color="#00d67f",
            hover_color="#00b86b",
            text_color="#0f1117",
            command=self._on_submit,
        )
        self.submit_btn.pack(pady=(8, 8), padx=40)

        # Error label
        self.error_label = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ff4d6a",
        )
        self.error_label.pack(pady=(4, 0))

        # Status label for key derivation
        self.status_label = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
        )
        self.status_label.pack(pady=(2, 0))

        self.pin_entry.focus_set()

    def _show_error(self, msg: str):
        self.error_label.configure(text=msg)

    def _clear_error(self):
        self.error_label.configure(text="")

    def _validate_pin(self, pin: str) -> str | None:
        if not pin.isdigit():
            return "PIN must contain only digits"
        if len(pin) < PIN_MIN_LENGTH:
            return f"PIN must be at least {PIN_MIN_LENGTH} digits"
        if len(pin) > PIN_MAX_LENGTH:
            return f"PIN must be at most {PIN_MAX_LENGTH} digits"
        return None

    def _on_submit(self, event=None):
        if self._locked_out:
            return

        pin = self.pin_entry.get().strip()
        error = self._validate_pin(pin)
        if error:
            self._show_error(error)
            return

        if self.first_run:
            confirm = self.confirm_entry.get().strip() if self.confirm_entry else ""
            if pin != confirm:
                self._show_error("PINs do not match")
                return
            self._clear_error()
            self.submit_btn.configure(state="disabled")
            self.status_label.configure(text="Deriving encryption key...")
            self.update_idletasks()
            key = setup_pin(self.conn, pin)
            self.app.on_login_success(key)
        else:
            self._clear_error()
            self.submit_btn.configure(state="disabled")
            self.status_label.configure(text="Verifying...")
            self.update_idletasks()
            key = verify_pin(self.conn, pin)
            if key is not None:
                self._failed_attempts = 0
                self.app.on_login_success(key)
            else:
                self._failed_attempts += 1
                self.pin_entry.delete(0, "end")

                if self._failed_attempts >= 3:
                    lockout_secs = 30 * (self._failed_attempts - 2)
                    self._locked_out = True
                    self.submit_btn.configure(state="disabled")
                    self._show_error(f"Too many attempts. Locked for {lockout_secs}s")
                    self._countdown(lockout_secs)
                else:
                    self.submit_btn.configure(state="normal")
                    self.status_label.configure(text="")
                    self._show_error(f"Incorrect PIN ({3 - self._failed_attempts} attempts left)")
                    self.pin_entry.focus_set()

    def _countdown(self, remaining: int):
        if remaining <= 0:
            self._locked_out = False
            self.submit_btn.configure(state="normal")
            self._show_error("Try again")
            self.status_label.configure(text="")
            self.pin_entry.focus_set()
            return
        self.status_label.configure(text=f"Wait {remaining}s...")
        self.after(1000, lambda: self._countdown(remaining - 1))
