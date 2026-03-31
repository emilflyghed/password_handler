import customtkinter as ctk
from tkinter import messagebox, filedialog

from database.models import get_all_entries, search_entries, delete_entry
from utils.clipboard import copy_with_auto_clear
from utils.backup import export_backup, import_backup
from gui.entry_dialog import EntryDialog
from gui.generator_dialog import GeneratorDialog
from gui.pin_dialog import PinDialog
from config import BACKUP_EXTENSION, PASSWORD_SHOW_SECONDS


class MainFrame(ctk.CTkFrame):
    def __init__(self, app, conn, key):
        super().__init__(app, fg_color="transparent")
        self.app = app
        self.conn = conn
        self.key = key
        self._show_jobs = {}

        self._build_toolbar()
        self._build_entry_list()
        self._refresh()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=50)
        toolbar.pack(fill="x", padx=16, pady=(12, 4))

        # Search
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search())

        self.search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text="Search vault...",
            width=300,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.search_entry.pack(side="left", padx=(0, 8))

        # Add button
        self.add_btn = ctk.CTkButton(
            toolbar,
            text="+ Add Entry",
            width=120,
            height=38,
            corner_radius=8,
            fg_color="#00d67f",
            hover_color="#00b86b",
            text_color="#0f1117",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_add,
        )
        self.add_btn.pack(side="left", padx=(0, 8))

        # Right side buttons
        self.lock_btn = ctk.CTkButton(
            toolbar,
            text="Lock",
            width=70,
            height=38,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color="#2a2e3d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.app.lock,
        )
        self.lock_btn.pack(side="right", padx=(4, 0))

        self.import_btn = ctk.CTkButton(
            toolbar,
            text="Import",
            width=80,
            height=38,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color="#2a2e3d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_import,
        )
        self.import_btn.pack(side="right", padx=(4, 0))

        self.export_btn = ctk.CTkButton(
            toolbar,
            text="Export",
            width=80,
            height=38,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color="#2a2e3d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_export,
        )
        self.export_btn.pack(side="right", padx=(4, 0))

        self.gen_btn = ctk.CTkButton(
            toolbar,
            text="Generate",
            width=90,
            height=38,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color="#2a2e3d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_generate,
        )
        self.gen_btn.pack(side="right", padx=(4, 0))

    def _build_entry_list(self):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        header.pack(fill="x", padx=16, pady=(8, 0))

        ctk.CTkLabel(header, text="SERVICE", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray", anchor="w", width=200).pack(side="left", padx=(12, 0))
        ctk.CTkLabel(header, text="USERNAME", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray", anchor="w", width=200).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(header, text="PASSWORD", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray", anchor="w", width=160).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(header, text="ACTIONS", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray", anchor="center").pack(side="right", padx=(0, 12))

        # Separator
        sep = ctk.CTkFrame(self, height=1, fg_color="gray")
        sep.pack(fill="x", padx=16, pady=(4, 0))

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Bottom bar: entry count + lock timer
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=16, pady=(0, 8))

        self.count_label = ctk.CTkLabel(
            bottom_bar,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
        )
        self.count_label.pack(side="left")

        self.timer_label = ctk.CTkLabel(
            bottom_bar,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
        )
        self.timer_label.pack(side="right")

    def _refresh(self):
        query = self.search_var.get().strip()
        if query:
            entries = search_entries(self.conn, self.key, query)
        else:
            entries = get_all_entries(self.conn, self.key)

        # Clear existing rows
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self._show_jobs.clear()

        if not entries:
            empty_label = ctk.CTkLabel(
                self.list_frame,
                text="No entries found" if query else "Your vault is empty — add your first entry!",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="gray",
            )
            empty_label.pack(pady=40)
            self.count_label.configure(text="0 entries")
            return

        for entry in entries:
            self._create_entry_row(entry)

        self.count_label.configure(text=f"{len(entries)} {'entry' if len(entries) == 1 else 'entries'}")

    def _create_entry_row(self, entry: dict):
        row = ctk.CTkFrame(self.list_frame, height=48, corner_radius=8)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Service
        ctk.CTkLabel(
            row, text=entry["service"],
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", width=200,
        ).pack(side="left", padx=(12, 0))

        # Username
        ctk.CTkLabel(
            row, text=entry["username"],
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", width=200,
        ).pack(side="left", padx=(8, 0))

        # Password (masked)
        pw_label = ctk.CTkLabel(
            row, text="●" * 10,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", width=160,
        )
        pw_label.pack(side="left", padx=(8, 0))

        # Actions
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=(0, 8))

        eid = entry["id"]
        pw = entry["password"]

        ctk.CTkButton(
            actions, text="Show", width=50, height=28, corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent", border_width=1, border_color="gray",
            hover_color="#2a2e3d",
            command=lambda l=pw_label, p=pw, i=eid: self._toggle_show(l, p, i),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions, text="Copy", width=50, height=28, corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent", border_width=1, border_color="gray",
            hover_color="#2a2e3d",
            command=lambda p=pw: copy_with_auto_clear(self.app, p),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions, text="Edit", width=50, height=28, corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent", border_width=1, border_color="gray",
            hover_color="#2a2e3d",
            command=lambda e=entry: self._on_edit(e),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions, text="Del", width=44, height=28, corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent", border_width=1, border_color="#ff4d6a",
            hover_color="#3d1520",
            text_color="#ff4d6a",
            command=lambda i=eid, s=entry["service"]: self._on_delete(i, s),
        ).pack(side="left", padx=2)

    def _toggle_show(self, label, password, entry_id):
        if label.cget("text") == "●" * 10:
            label.configure(text=password)
            # Auto-hide after configured seconds
            if entry_id in self._show_jobs:
                self.after_cancel(self._show_jobs[entry_id])
            self._show_jobs[entry_id] = self.after(
                PASSWORD_SHOW_SECONDS * 1000,
                lambda l=label: l.configure(text="●" * 10),
            )
        else:
            label.configure(text="●" * 10)
            if entry_id in self._show_jobs:
                self.after_cancel(self._show_jobs[entry_id])

    def _on_search(self):
        self._refresh()

    def _on_add(self):
        EntryDialog(self.app, self.conn, self.key, on_save=self._refresh)

    def _on_edit(self, entry: dict):
        EntryDialog(self.app, self.conn, self.key, entry=entry, on_save=self._refresh)

    def _on_delete(self, entry_id: int, service: str):
        if messagebox.askyesno("Delete Entry", f"Delete '{service}'? This cannot be undone."):
            delete_entry(self.conn, entry_id)
            self._refresh()

    def _on_export(self):
        filepath = filedialog.asksaveasfilename(
            title="Export Backup",
            defaultextension=BACKUP_EXTENSION,
            filetypes=[("Vault Backup", f"*{BACKUP_EXTENSION}")],
        )
        if not filepath:
            return

        def do_export(pin):
            try:
                export_backup(self.conn, self.key, pin, filepath)
                messagebox.showinfo("Export", "Backup exported successfully!")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

        PinDialog(
            self.app,
            title="Export PIN",
            prompt="Choose a PIN to protect this backup. You'll need it to import on another device.",
            on_submit=do_export,
        )

    def _on_import(self):
        filepath = filedialog.askopenfilename(
            title="Import Backup",
            filetypes=[("Vault Backup", f"*{BACKUP_EXTENSION}")],
        )
        if not filepath:
            return

        def do_import(pin):
            try:
                count = import_backup(self.conn, self.key, pin, filepath)
                messagebox.showinfo("Import", f"Imported {count} entries!")
                self._refresh()
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import. Wrong PIN or corrupted file.\n\n{e}")

        PinDialog(
            self.app,
            title="Import PIN",
            prompt="Enter the PIN that was used when this backup was exported.",
            on_submit=do_import,
        )

    def update_timer(self, seconds: int):
        mins, secs = divmod(seconds, 60)
        if mins > 0:
            self.timer_label.configure(text=f"Auto-lock in {mins}:{secs:02d}")
        else:
            self.timer_label.configure(text=f"Auto-lock in {secs}s")

    def _on_generate(self):
        GeneratorDialog(self.app)
