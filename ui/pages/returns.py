"""Returns and refunds page."""

from __future__ import annotations

from decimal import Decimal

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class ReturnsPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Returns / Refunds", "Process returns against completed sales")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(toolbar, text="Sale ID", font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=0, column=0, padx=(0, 6))
        self.sale_id_entry = ctk.CTkEntry(toolbar, height=34, width=260)
        self.sale_id_entry.grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(toolbar, text="Load Eligible Items", height=34, command=self.load_items).grid(row=0, column=2, padx=4)
        ctk.CTkButton(toolbar, text="Process Full Return", height=34, command=self.full_return).grid(row=0, column=3, padx=4)
        self.table = DataTable(self.body, [("product_name", "Product", 220), ("quantity", "Sold", 80), ("returnable_quantity", "Returnable", 100), ("unit_price", "Price", 90)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)

    def load_items(self):
        sale_id = self.sale_id_entry.get().strip()
        if not sale_id:
            return
        items = self.app.context["returns"].eligible_items(sale_id)
        self.loaded_sale_id = sale_id
        self.loaded_items = items
        self.table.set_rows(items, id_column="sale_item_id")

    def full_return(self):
        sale_id = getattr(self, "loaded_sale_id", None) or self.sale_id_entry.get().strip()
        if not sale_id:
            return
        try:
            eligible = self.app.context["returns"].eligible_items(sale_id)
            items = [{"sale_item_id": i["sale_item_id"], "quantity": i["returnable_quantity"], "restock": True} for i in eligible]
            self.app.context["returns"].create_return(self.app.current_user, sale_id, items, "Full return", "cash")
            info(self.app, "Return complete", "Full return processed.")
            self.load_items()
        except Exception as exc:
            info(self.app, "Error", str(exc))