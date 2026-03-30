import customtkinter as ctk

from database.models import add_entry, update_entry
from gui.generator_dialog import GeneratorDialog


class EntryDialog(ctk.CTkToplevel):
    def __init__(self, app, conn, key, entry=None, on_save=None):
        super().__init__(app)
        self.conn = conn
        self.key = key
        self.entry = entry
        self.on_save = on_save

        self.title("Edit Entry" if entry else "Add Entry")
        self.geometry("420x380")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()

        self._build_form()
        self.after(100, self.service_entry.focus_set)

    def _build_form(self):
        pad = {"padx": 30, "fill": "x"}

        # Title
        ctk.CTkLabel(
            self,
            text="Edit Entry" if self.entry else "New Entry",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 16), **pad)

        # Service
        ctk.CTkLabel(self, text="Service", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(**pad)
        self.service_entry = ctk.CTkEntry(self, height=38, corner_radius=8,
                                          placeholder_text="e.g. GitHub, Gmail, Netflix")
        self.service_entry.pack(pady=(2, 10), **pad)

        # Username
        ctk.CTkLabel(self, text="Username / Email", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(**pad)
        self.username_entry = ctk.CTkEntry(self, height=38, corner_radius=8,
                                           placeholder_text="e.g. user@example.com")
        self.username_entry.pack(pady=(2, 10), **pad)

        # Password row
        ctk.CTkLabel(self, text="Password", font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(**pad)

        pw_frame = ctk.CTkFrame(self, fg_color="transparent")
        pw_frame.pack(pady=(2, 16), **pad)

        self.password_entry = ctk.CTkEntry(
            pw_frame, height=38, corner_radius=8, show="●",
            placeholder_text="Enter or generate a password",
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.show_pw = False
        self.toggle_btn = ctk.CTkButton(
            pw_frame, text="👁", width=38, height=38, corner_radius=8,
            fg_color="transparent", border_width=1, border_color="gray",
            command=self._toggle_password,
        )
        self.toggle_btn.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            pw_frame, text="Gen", width=50, height=38, corner_radius=8,
            fg_color="#00d67f", hover_color="#00b86b", text_color="#0f1117",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_generator,
        ).pack(side="left")

        # Pre-fill for edit
        if self.entry:
            self.service_entry.insert(0, self.entry["service"])
            self.username_entry.insert(0, self.entry["username"])
            self.password_entry.insert(0, self.entry["password"])

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 20), **pad)

        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=38, corner_radius=8,
            fg_color="transparent", border_width=1, border_color="gray",
            hover_color="#2a2e3d",
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Save", width=100, height=38, corner_radius=8,
            fg_color="#00d67f", hover_color="#00b86b", text_color="#0f1117",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_save,
        ).pack(side="right")

        # Error
        self.error_label = ctk.CTkLabel(self, text="", text_color="#ff4d6a",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self.error_label.pack()

        self.bind("<Return>", lambda e: self._on_save())

    def _toggle_password(self):
        self.show_pw = not self.show_pw
        self.password_entry.configure(show="" if self.show_pw else "●")

    def _open_generator(self):
        GeneratorDialog(self, target_entry=self.password_entry)

    def _on_save(self):
        service = self.service_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not service:
            self.error_label.configure(text="Service name is required")
            return
        if not username:
            self.error_label.configure(text="Username is required")
            return
        if not password:
            self.error_label.configure(text="Password is required")
            return

        if self.entry:
            update_entry(self.conn, self.key, self.entry["id"], service, username, password)
        else:
            add_entry(self.conn, self.key, service, username, password)

        if self.on_save:
            self.on_save()
        self.destroy()
