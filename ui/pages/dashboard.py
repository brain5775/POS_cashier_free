"""Dashboard page."""

from __future__ import annotations

from decimal import Decimal

import customtkinter as ctk

from ui.components.base import BasePage
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED, TEXT


class DashboardPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Dashboard", "Today's business overview")
        self.app = app
        self._build()

    def _build(self):
        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1)
        metrics = [
            ("Today Sales", self._today_sales()),
            ("Transactions", self._today_transactions()),
            ("Inventory Value", self._inventory_value()),
            ("Low Stock", self._low_stock_count()),
        ]
        for idx, (label, value) in enumerate(metrics):
            card = ctk.CTkFrame(grid, corner_radius=10)
            card.grid(row=0, column=idx, padx=8, pady=8, sticky="nsew")
            ctk.CTkLabel(card, text=label, text_color=MUTED, font=(FONT_FAMILY, FONT_SIZE)).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(card, text=str(value), font=(FONT_FAMILY, 22, "bold"), text_color=TEXT).pack(anchor="w", padx=16, pady=(0, 12))
        # recent sales table placeholder
        ctk.CTkLabel(self.body, text="Recent transactions", font=(FONT_FAMILY, 16, "bold")).pack(anchor="w", pady=(16, 6))
        from ui.components.base import DataTable
        table = DataTable(self.body, [("receipt_number", "Receipt", 160), ("created_at", "Date", 180), ("total", "Total", 120), ("status", "Status", 100)])
        table.pack(fill="both", expand=True)
        app = self.app
        sales = sorted(app.context["sales"].list_sales(), key=lambda r: r.get("created_at", ""), reverse=True)[:10]
        table.set_rows(sales, id_column="sale_id")

    def _today_sales(self):
        from datetime import date
        today = date.today().isoformat()
        total = Decimal("0")
        for sale in self.app.context["sales"].list_sales():
            if sale.get("created_at", "").startswith(today) and sale.get("status") == "completed":
                total += Decimal(sale.get("total") or "0")
        cur = self.app.context["settings"].get("currency", "IDR")
        return f"{cur} {total:,.2f}"

    def _today_transactions(self):
        from datetime import date
        today = date.today().isoformat()
        return sum(1 for s in self.app.context["sales"].list_sales() if s.get("created_at", "").startswith(today) and s.get("status") == "completed")

    def _inventory_value(self):
        val = self.app.context["inventory"].valuation(self.app.context["products"])
        cur = self.app.context["settings"].get("currency", "IDR")
        return f"{cur} {val:,.2f}"

    def _low_stock_count(self):
        return len(self.app.context["inventory"].low_stock_products(self.app.context["products"]))