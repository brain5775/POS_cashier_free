"""Suppliers page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class SuppliersPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Suppliers", "Supplier profiles")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.search_var = ctk.StringVar()
        search = ctk.CTkEntry(toolbar, height=34, textvariable=self.search_var, placeholder_text="Search name, contact, phone")
        search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(toolbar, text="Search", height=34, command=self.refresh).grid(row=0, column=1, padx=4)
        ctk.CTkButton(toolbar, text="Add Supplier", height=34, command=self.add_supplier).grid(row=0, column=2, padx=4)
        ctk.CTkButton(toolbar, text="Refresh", height=34, fg_color="#64748B", hover_color="#475569", command=self.refresh).grid(row=0, column=3)
        self.table = DataTable(self.body, [("name", "Name", 190), ("contact_person", "Contact", 150), ("phone", "Phone", 130), ("email", "Email", 200), ("is_active", "Active", 80)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        rows = self.app.context["suppliers"].list_suppliers(query=self.search_var.get())
        self.table.set_rows(rows, id_column="supplier_id")

    def add_supplier(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add Supplier")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry("460x430")
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        fields = {}
        labels = ["name", "contact_person", "phone", "email", "address", "notes"]
        for i, key in enumerate(labels):
            ctk.CTkLabel(frame, text=key.replace("_", " ").title(), font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=i * 2, column=0, sticky="w", pady=(8, 2))
            e = ctk.CTkEntry(frame, height=34)
            e.grid(row=i * 2 + 1, column=0, sticky="ew")
            fields[key] = e
        def save():
            data = {k: v.get() for k, v in fields.items()}
            try:
                self.app.context["suppliers"].create_supplier(self.app.current_user, data)
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Save", height=34, command=save).grid(row=12, column=0, sticky="ew", pady=(12, 0))