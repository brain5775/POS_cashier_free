"""Settings page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class SettingsPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Settings", "Business and application settings")
        self.app = app
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self.body)
        scroll.grid(row=0, column=0, sticky="nsew")
        self.body.grid_rowconfigure(0, weight=1)
        scroll.grid_columnconfigure(0, weight=1)
        settings = self.app.context["settings"].all()
        self.entries = {}
        for i, key in enumerate(["business_name", "business_address", "business_phone", "business_email", "currency", "tax_rate", "tax_mode", "receipt_header", "receipt_footer", "default_low_stock", "allow_negative_stock"]):
            ctk.CTkLabel(scroll, text=key.replace("_", " ").title(), font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=i * 2, column=0, sticky="w", pady=(10, 2))
            entry = ctk.CTkEntry(scroll, height=34)
            entry.insert(0, settings.get(key, ""))
            entry.grid(row=i * 2 + 1, column=0, sticky="ew", pady=(0, 2))
            self.entries[key] = entry
        ctk.CTkButton(scroll, text="Save Settings", height=36, command=self.save).grid(row=24, column=0, sticky="ew", pady=(16, 0))

    def save(self):
        try:
            data = {k: v.get() for k, v in self.entries.items()}
            self.app.context["settings"].update_many(data, self.app.current_user)
            info(self.app, "Saved", "Settings saved.")
        except Exception as exc:
            info(self.app, "Error", str(exc))