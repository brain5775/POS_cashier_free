"""Reports page."""

from __future__ import annotations

import csv
from pathlib import Path

import customtkinter as ctk

from ui.components.base import BasePage
from ui.components.dialogs import info
from ui.theme import BUTTON_HEIGHT, FONT_SIZE, MUTED


class ReportsPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Reports", "Sales and inventory reports")
        self.app = app
        self._build()

    def _build(self):
        self.body.grid_rowconfigure(0, weight=1)
        panel = ctk.CTkFrame(self.body, fg_color="transparent")
        panel.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(panel, text="Export business data to CSV or review key totals.", text_color=MUTED).pack(anchor="w", pady=(0, 12))
        for text, command in [
            ("Export Sales CSV", self.export_sales),
            ("Export Products CSV", self.export_products),
            ("Export Stock Movements CSV", self.export_moves),
            ("Inventory Valuation", self.inventory_value),
        ]:
            ctk.CTkButton(panel, text=text, height=BUTTON_HEIGHT, command=command).pack(fill="x", pady=4)

    def _write_csv(self, filename, rows, headers):
        out = Path("reports") / filename
        out.parent.mkdir(exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        info(self.app, "Exported", str(out))

    def export_sales(self):
        rows = self.app.context["sales"].list_sales()
        headers = list(self.app.context["store"].headers("sales.csv"))
        self._write_csv("sales_export.csv", rows, headers)

    def export_products(self):
        rows = self.app.context["products"].products.all()
        headers = list(self.app.context["store"].headers("products.csv"))
        self._write_csv("products_export.csv", rows, headers)

    def export_moves(self):
        rows = self.app.context["inventory"].movements.all()
        headers = list(self.app.context["store"].headers("stock_movements.csv"))
        self._write_csv("stock_movements_export.csv", rows, headers)

    def inventory_value(self):
        val = self.app.context["inventory"].valuation(self.app.context["products"])
        info(self.app, "Inventory Valuation", f"{val}")