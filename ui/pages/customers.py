"""Customers page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class CustomersPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Customers", "Customer profiles and purchase history")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.search_var = ctk.StringVar()
        search = ctk.CTkEntry(toolbar, height=34, textvariable=self.search_var, placeholder_text="Search name, phone, email")
        search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(toolbar, text="Search", height=34, command=self.refresh).grid(row=0, column=1, padx=4)
        ctk.CTkButton(toolbar, text="Add Customer", height=34, command=self.add_customer).grid(row=0, column=2, padx=4)
        ctk.CTkButton(toolbar, text="Refresh", height=34, fg_color="#64748B", hover_color="#475569", command=self.refresh).grid(row=0, column=3)
        self.table = DataTable(self.body, [("name", "Name", 190), ("phone", "Phone", 130), ("email", "Email", 200), ("total_spent", "Total Spent", 110), ("last_purchase_at", "Last Purchase", 170)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        rows = self.app.context["customers"].list_customers(query=self.search_var.get())
        self.table.set_rows(rows, id_column="customer_id")

    def add_customer(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add Customer")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry("460x470")
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        fields = {}
        for i, (key, label) in enumerate([("name", "Name"), ("phone", "Phone"), ("email", "Email"), ("address", "Address"), ("notes", "Notes"), ("discount_percent", "Discount %")]):
            ctk.CTkLabel(frame, text=label, font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=i * 2, column=0, sticky="w", pady=(8, 2))
            e = ctk.CTkEntry(frame, height=34)
            e.grid(row=i * 2 + 1, column=0, sticky="ew")
            fields[key] = e
        def save():
            data = {k: v.get() for k, v in fields.items()}
            try:
                self.app.context["customers"].create_customer(self.app.current_user, data)
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Save", height=34, command=save).grid(row=12, column=0, sticky="ew", pady=(12, 0))