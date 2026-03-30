import customtkinter as ctk

from crypto.generator import generate_password
from utils.clipboard import copy_with_auto_clear


class GeneratorDialog(ctk.CTkToplevel):
    def __init__(self, parent, target_entry=None):
        super().__init__(parent)
        self.parent = parent
        self.target_entry = target_entry

        self.title("Password Generator")
        self.geometry("400x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._generate()

    def _build_ui(self):
        pad = {"padx": 24, "fill": "x"}

        ctk.CTkLabel(
            self, text="Password Generator",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 16), **pad)

        # Generated password display
        self.result_entry = ctk.CTkEntry(
            self, height=44, corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            justify="center",
        )
        self.result_entry.pack(pady=(0, 16), **pad)

        # Length slider
        len_frame = ctk.CTkFrame(self, fg_color="transparent")
        len_frame.pack(**pad, pady=(0, 8))

        ctk.CTkLabel(len_frame, text="Length:", font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(side="left")

        self.length_label = ctk.CTkLabel(len_frame, text="16",
                                         font=ctk.CTkFont(size=13, weight="bold"), width=30)
        self.length_label.pack(side="right")

        self.length_slider = ctk.CTkSlider(
            self, from_=8, to=64, number_of_steps=56,
            command=self._on_length_change,
        )
        self.length_slider.set(16)
        self.length_slider.pack(**pad, pady=(0, 12))

        # Character set checkboxes
        self.upper_var = ctk.BooleanVar(value=True)
        self.lower_var = ctk.BooleanVar(value=True)
        self.digit_var = ctk.BooleanVar(value=True)
        self.symbol_var = ctk.BooleanVar(value=True)
        self.ambig_var = ctk.BooleanVar(value=False)

        # Row 1: A-Z & a-z
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(**pad, pady=(0, 6))

        ctk.CTkCheckBox(row1, text="A-Z", variable=self.upper_var,
                        font=ctk.CTkFont(size=12, weight="bold"), command=self._generate).pack(side="left", padx=(0, 24))
        ctk.CTkCheckBox(row1, text="a-z", variable=self.lower_var,
                        font=ctk.CTkFont(size=12, weight="bold"), command=self._generate).pack(side="left")

        # Row 2: 0-9 & special characters
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(**pad, pady=(0, 6))

        ctk.CTkCheckBox(row2, text="0-9", variable=self.digit_var,
                        font=ctk.CTkFont(size=12, weight="bold"), command=self._generate).pack(side="left", padx=(0, 24))
        ctk.CTkCheckBox(row2, text="!@#$", variable=self.symbol_var,
                        font=ctk.CTkFont(size=12, weight="bold"), command=self._generate).pack(side="left")

        # Row 3: Exclude ambiguous
        ctk.CTkCheckBox(
            self, text="Exclude ambiguous characters (0, O, 1, l, I, |)",
            variable=self.ambig_var, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._generate,
        ).pack(**pad, pady=(0, 16))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(**pad, pady=(0, 20))

        ctk.CTkButton(
            btn_frame, text="Regenerate", width=100, height=38, corner_radius=8,
            fg_color="transparent", border_width=1, border_color="gray",
            hover_color="#2a2e3d",
            command=self._generate,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_frame, text="Copy", width=80, height=38, corner_radius=8,
            fg_color="transparent", border_width=1, border_color="gray",
            hover_color="#2a2e3d",
            command=self._copy,
        ).pack(side="left", padx=(0, 6))

        if self.target_entry is not None:
            ctk.CTkButton(
                btn_frame, text="Use Password", width=120, height=38, corner_radius=8,
                fg_color="#00d67f", hover_color="#00b86b", text_color="#0f1117",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=self._use,
            ).pack(side="right")

    def _on_length_change(self, value):
        length = int(value)
        self.length_label.configure(text=str(length))
        self._generate()

    def _generate(self, *_):
        pw = generate_password(
            length=int(self.length_slider.get()),
            uppercase=self.upper_var.get(),
            lowercase=self.lower_var.get(),
            digits=self.digit_var.get(),
            symbols=self.symbol_var.get(),
            exclude_ambiguous=self.ambig_var.get(),
        )
        self.result_entry.delete(0, "end")
        self.result_entry.insert(0, pw)

    def _copy(self):
        pw = self.result_entry.get()
        # Walk up to find the root CTk window
        root = self
        while root.master is not None:
            root = root.master
        copy_with_auto_clear(root, pw)

    def _use(self):
        pw = self.result_entry.get()
        if self.target_entry:
            self.target_entry.delete(0, "end")
            self.target_entry.insert(0, pw)
        self.destroy()
