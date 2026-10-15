"""Sales history page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import confirm, info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class SalesHistoryPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Sales History", "Search and review sales")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(toolbar, text="Status", font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=0, column=0, padx=(0, 6))
        self.status_var = ctk.StringVar(value="")
        ctk.CTkEntry(toolbar, height=34, textvariable=self.status_var, placeholder_text="completed/voided").grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(toolbar, text="Refresh", height=34, command=self.refresh, fg_color="#64748B", hover_color="#475569").grid(row=0, column=2, padx=4)
        ctk.CTkButton(toolbar, text="View Items", height=34, command=self.view_items).grid(row=0, column=3, padx=4)
        ctk.CTkButton(toolbar, text="Void", height=34, fg_color="#DC2626", hover_color="#B91C1C", command=self.void_sale).grid(row=0, column=4, padx=4)
        self.table = DataTable(self.body, [("receipt_number", "Receipt", 130), ("created_at", "Date", 170), ("total", "Total", 100), ("payment_status", "Payment", 90), ("status", "Status", 90), ("user_id", "Cashier", 100)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        status = self.status_var.get().strip()
        rows = self.app.context["sales"].list_sales(status=status)
        self.table.set_rows(rows, id_column="sale_id")

    def selected_sale_id(self):
        return self.table.selected_iid()

    def view_items(self):
        sid = self.selected_sale_id()
        if not sid:
            return
        items = self.app.context["sales"].get_sale_items(sid)
        info(self.app, "Sale Items", "\n".join(f"{i['product_name']} x{i['quantity']} = {i['total']}" for i in items) or "No items")

    def void_sale(self):
        sid = self.selected_sale_id()
        if not sid:
            return
        if not confirm(self.app, "Void Sale", "Void this sale and restock items?"):
            return
        try:
            self.app.context["sales"].void_sale(self.app.current_user, sid, "Voided from UI")
            self.refresh()
        except Exception as exc:
            info(self.app, "Error", str(exc))