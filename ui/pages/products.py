"""Products page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import confirm, info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class ProductsPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Products", "Manage products, prices, and stock thresholds")
        self.app = app
        self._build()

    def _build(self):
        bar = ctk.CTkFrame(self.body, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))
        self.search_var = ctk.StringVar()
        entry = ctk.CTkEntry(bar, textvariable=self.search_var, placeholder_text="Search name/SKU/barcode")
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.refresh())
        ctk.CTkButton(bar, text="Search", command=self.refresh).pack(side="left", padx=8)
        ctk.CTkButton(bar, text="Add Product", command=self.add_product).pack(side="left", padx=8)
        ctk.CTkButton(bar, text="Edit", command=self.edit_product).pack(side="left", padx=8)
        ctk.CTkButton(bar, text="Deactivate", command=self.deactivate_product).pack(side="left", padx=8)
        ctk.CTkButton(bar, text="Refresh", command=self.refresh).pack(side="left", padx=8)
        self.table = DataTable(self.body, [
            ("name", "Name", 180), ("sku", "SKU", 100), ("barcode", "Barcode", 120), ("category", "Category", 110),
            ("purchase_cost", "Cost", 80), ("selling_price", "Price", 80), ("min_stock", "Min", 60), ("is_active", "Active", 60)
        ])
        self.table.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        products = self.app.context["products"].search_products(query=self.search_var.get(), active_only=False)
        stock_map = self.app.context["inventory"].stock_map()
        rows = []
        for p in products:
            rows.append({**p, "stock": str(stock_map.get(p["product_id"], 0))})
        self.table.set_rows(rows, id_column="product_id")

    def _form(self, initial=None):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Product")
        dialog.geometry("520x640")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry("560x720")
        dialog.minsize(420, 400)
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=0, pady=8)
        fields = {}
        labels = [
            ("sku", "SKU"), ("barcode", "Barcode"), ("name", "Name"), ("category", "Category"),
            ("brand", "Brand"), ("unit", "Unit"), ("purchase_cost", "Purchase cost"),
            ("selling_price", "Selling price"), ("wholesale_price", "Wholesale price"),
            ("min_stock", "Min stock"), ("max_stock", "Max stock"), ("supplier_id", "Supplier ID"),
            ("description", "Description"),
        ]
        for key, label in labels:
            ctk.CTkLabel(scroll, text=label, font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).pack(anchor="w", padx=16, pady=(8, 2))
            entry = ctk.CTkEntry(scroll, height=34)
            if initial:
                entry.insert(0, initial.get(key, "") or "")
            entry.pack(fill="x", padx=16, pady=(0, 2))
            fields[key] = entry
        is_active_var = ctk.StringVar(value=initial.get("is_active", "true") if initial else "true")
        ctk.CTkLabel(scroll, text="Active", font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).pack(anchor="w", padx=16, pady=(8, 2))
        ctk.CTkComboBox(scroll, values=["true", "false"], variable=is_active_var, height=34).pack(fill="x", padx=16, pady=(0, 2))
        fields["is_active"] = is_active_var

        def save():
            data = {k: (v.get() if hasattr(v, "get") else v) for k, v in fields.items()}
            if isinstance(fields["is_active"], ctk.StringVar):
                data["is_active"] = is_active_var.get()
            try:
                if initial:
                    self.app.context["products"].update_product(self.app.current_user, initial["product_id"], data)
                else:
                    self.app.context["products"].create_product(self.app.current_user, data)
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=12)
        return dialog

    def add_product(self):
        self._form()

    def edit_product(self):
        pid = self.table.selected_iid()
        if not pid:
            info(self.app, "Select product", "Choose a product first.")
            return
        product = self.app.context["products"].get_product(product_id=pid)
        self._form(initial=product)

    def deactivate_product(self):
        pid = self.table.selected_iid()
        if not pid:
            return
        if not confirm(self.app, "Deactivate", "Deactivate selected product?"):
            return
        try:
            self.app.context["products"].deactivate_product(self.app.current_user, pid)
            self.refresh()
        except Exception as exc:
            info(self.app, "Error", str(exc))