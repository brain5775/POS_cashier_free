"""Categories page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import CARD, FONT_FAMILY, FONT_SIZE, MUTED


class CategoriesPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Categories", "Manage product categories")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(0, weight=0)
        toolbar.grid_columnconfigure(1, weight=0)
        ctk.CTkButton(toolbar, text="Add Category", height=34, command=self.add_category).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(toolbar, text="Refresh", height=34, command=self.refresh, fg_color="#64748B", hover_color="#475569").grid(row=0, column=1)
        self.table = DataTable(self.body, [("name", "Name", 240), ("description", "Description", 420), ("is_active", "Active", 90)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        rows = self.app.context["products"].list_categories()
        self.table.set_rows(rows, id_column="category_id")

    def add_category(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add Category")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry("420x250")
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="Category details", font=(FONT_FAMILY, 16, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        name = ctk.CTkEntry(frame, height=34, placeholder_text="Name")
        name.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        desc = ctk.CTkEntry(frame, height=34, placeholder_text="Description")
        desc.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        def save():
            try:
                self.app.context["products"].create_category(self.app.current_user, name.get(), desc.get())
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Save", height=34, command=save).grid(row=3, column=0, sticky="ew", pady=(8, 0))