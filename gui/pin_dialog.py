import customtkinter as ctk

from config import PIN_MIN_LENGTH, PIN_MAX_LENGTH


class PinDialog(ctk.CTkToplevel):
    """Modal dialog that prompts for a PIN and returns it via a callback."""

    def __init__(self, app, title: str, prompt: str, on_submit):
        super().__init__(app)
        self.on_submit = on_submit
        self.result = None

        self.title(title)
        self.geometry("360x220")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()

        ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 8), padx=30)

        ctk.CTkLabel(
            self, text=prompt,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
            wraplength=300,
        ).pack(padx=30, pady=(0, 12))

        self.pin_entry = ctk.CTkEntry(
            self, show="●", width=240, height=42,
            font=ctk.CTkFont(size=18, weight="bold"),
            justify="center",
            placeholder_text=f"{PIN_MIN_LENGTH}-{PIN_MAX_LENGTH} digits",
            corner_radius=10,
        )
        self.pin_entry.pack(pady=(0, 12), padx=30)
        self.pin_entry.bind("<Return>", lambda e: self._on_ok())

        self.error_label = ctk.CTkLabel(
            self, text="", text_color="#ff4d6a",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.error_label.pack()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(4, 16), padx=30)

        ctk.CTkButton(
            btn_frame, text="Cancel", width=90, height=36, corner_radius=8,
            fg_color="transparent", border_width=1, border_color="gray",
            hover_color="#2a2e3d",
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="OK", width=90, height=36, corner_radius=8,
            fg_color="#00d67f", hover_color="#00b86b", text_color="#0f1117",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_ok,
        ).pack(side="right")

        self.after(100, self.pin_entry.focus_set)

    def _on_ok(self):
        pin = self.pin_entry.get().strip()
        if not pin.isdigit() or not (PIN_MIN_LENGTH <= len(pin) <= PIN_MAX_LENGTH):
            self.error_label.configure(text=f"PIN must be {PIN_MIN_LENGTH}-{PIN_MAX_LENGTH} digits")
            return
        self.result = pin
        self.destroy()
        self.on_submit(pin)
