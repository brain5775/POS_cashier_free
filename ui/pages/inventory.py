"""Inventory page."""

from __future__ import annotations

from decimal import Decimal

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class InventoryPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Inventory", "Current stock levels and adjustments")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(toolbar, text="Adjust Stock", height=34, command=self.adjust).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(toolbar, text="Refresh", height=34, command=self.refresh, fg_color="#64748B", hover_color="#475569").grid(row=0, column=1, padx=4)
        ctk.CTkButton(toolbar, text="Low Stock Only", height=34, command=self.low_stock, fg_color="#D97706", hover_color="#B45309").grid(row=0, column=2, padx=4)
        self.table = DataTable(self.body, [("name", "Product", 220), ("sku", "SKU", 110), ("current_stock", "Stock", 90), ("min_stock", "Min", 80), ("purchase_cost", "Cost", 90)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def _rows(self, low_only=False):
        products = self.app.context["products"].search_products(active_only=False)
        stock_map = self.app.context["inventory"].stock_map()
        rows = []
        for p in products:
            stock = stock_map.get(p["product_id"], Decimal("0"))
            if low_only and stock >= Decimal(p.get("min_stock") or "0"):
                continue
            rows.append({**p, "current_stock": str(stock)})
        return rows

    def refresh(self):
        self.table.set_rows(self._rows(), id_column="product_id")

    def low_stock(self):
        self.table.set_rows(self._rows(low_only=True), id_column="product_id")

    def adjust(self):
        pid = self.table.selected_iid()
        if not pid:
            info(self.app, "Select product", "Choose a product first.")
            return
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Stock Adjustment")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry("420x330")
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="Adjustment details", font=(FONT_FAMILY, 16, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        qty = ctk.CTkEntry(frame, height=34, placeholder_text="Quantity change (+/-)")
        qty.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        reason = ctk.CTkEntry(frame, height=34, placeholder_text="Reason")
        reason.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        mtype = ctk.CTkComboBox(frame, height=34, values=["ADJUSTMENT", "DAMAGED", "EXPIRED", "COUNT"])
        mtype.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        cost = ctk.CTkEntry(frame, height=34, placeholder_text="Unit cost (optional)")
        cost.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        def save():
            try:
                delta = Decimal(qty.get())
                uc = cost.get() or None
                self.app.context["inventory"].adjust_stock(self.app.current_user, pid, delta, mtype.get(), reason.get(), uc)
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Apply", height=34, command=save).grid(row=5, column=0, sticky="ew", pady=(8, 0))


class StockMovementsPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Stock Movements", "Inventory movement history")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(toolbar, text="Refresh", height=34, command=self.refresh, fg_color="#64748B", hover_color="#475569").pack(anchor="w")
        self.table = DataTable(self.body, [("timestamp", "Time", 180), ("product_id", "Product", 120), ("quantity_change", "Change", 80), ("movement_type", "Type", 150), ("reference_type", "Ref Type", 110), ("reason", "Reason", 260)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        rows = sorted(self.app.context["inventory"].movements.all(), key=lambda r: r.get("timestamp", ""), reverse=True)
        self.table.set_rows(rows, id_column="movement_id")