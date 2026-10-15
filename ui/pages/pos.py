"""Cashier POS page."""

from __future__ import annotations

from decimal import Decimal

import customtkinter as ctk

from core.exceptions import AppError
from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import BUTTON_HEIGHT, CARD, DANGER, FONT_FAMILY, FONT_SECTION, FONT_SIZE, MUTED, PRIMARY, SUCCESS, TEXT


class POSPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Cashier / POS", "Scan or search products, build the cart, and complete the sale")
        self.app = app
        self.cart = []
        self._build()

    def _build(self):
        container = ctk.CTkFrame(self.body, fg_color="transparent")
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=5)
        container.grid_columnconfigure(1, weight=4)
        container.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(container, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        search = ctk.CTkFrame(left, fg_color=CARD, corner_radius=8)
        search.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        search.grid_columnconfigure(0, weight=2)
        search.grid_columnconfigure(1, weight=2)
        search.grid_columnconfigure(2, weight=0)
        self.barcode_entry = ctk.CTkEntry(search, height=34, placeholder_text="Barcode / SKU + Enter")
        self.barcode_entry.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=12)
        self.barcode_entry.bind("<Return>", lambda e: self.scan_barcode())
        self.search_entry = ctk.CTkEntry(search, height=34, placeholder_text="Search name, SKU, brand")
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=12)
        self.search_entry.bind("<Return>", lambda e: self.search_products())
        ctk.CTkButton(search, text="Search", height=34, width=92, command=self.search_products).grid(row=0, column=2, padx=(6, 12), pady=12)

        filters = ctk.CTkFrame(left, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(filters, text="Double-click a result to add it to the cart.", text_color=MUTED, font=(FONT_FAMILY, FONT_SIZE - 1)).pack(anchor="w")

        self.results_table = DataTable(left, [("name", "Name", 240), ("sku", "SKU", 110), ("selling_price", "Price", 90), ("stock", "Stock", 70)])
        self.results_table.grid(row=2, column=0, sticky="nsew")

        right = ctk.CTkFrame(container, fg_color=CARD, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Cart", font=(FONT_FAMILY, FONT_SECTION, "bold"), text_color=TEXT).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))
        self.cart_table = DataTable(right, [("name", "Item", 170), ("quantity", "Qty", 48), ("unit_price", "Price", 82), ("total", "Total", 90)])
        self.cart_table.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        totals = ctk.CTkFrame(right, fg_color="transparent")
        totals.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 8))
        totals.grid_columnconfigure(0, weight=1)
        self.subtotal_label = ctk.CTkLabel(totals, text="Subtotal: 0", anchor="e")
        self.subtotal_label.grid(row=0, column=0, sticky="e")
        self.discount_label = ctk.CTkLabel(totals, text="Discount: 0", anchor="e")
        self.discount_label.grid(row=1, column=0, sticky="e")
        self.tax_label = ctk.CTkLabel(totals, text="Tax: 0", anchor="e")
        self.tax_label.grid(row=2, column=0, sticky="e")
        self.total_label = ctk.CTkLabel(totals, text="Total: 0", anchor="e", font=(FONT_FAMILY, 17, "bold"), text_color=PRIMARY)
        self.total_label.grid(row=3, column=0, sticky="e", pady=(4, 0))

        controls = ctk.CTkFrame(right, fg_color="transparent")
        controls.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 8))
        controls.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.qty_entry = ctk.CTkEntry(controls, height=34, placeholder_text="Qty")
        self.qty_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(controls, text="Update", height=34, command=self.update_qty).grid(row=0, column=1, sticky="ew", padx=3)
        ctk.CTkButton(controls, text="Remove", height=34, command=self.remove_item, fg_color=DANGER, hover_color="#B91C1C").grid(row=0, column=2, sticky="ew", padx=3)
        ctk.CTkButton(controls, text="Clear", height=34, command=self.clear_cart, fg_color="#64748B", hover_color="#475569").grid(row=0, column=3, sticky="ew", padx=(3, 0))

        bottom = ctk.CTkScrollableFrame(right, fg_color="transparent", height=260)
        bottom.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 12))
        bottom.grid_columnconfigure(0, weight=1)

        labels = ["Customer ID (optional)", "Order discount", "Payment method", "Cash received (cash payments)"]
        for i, label in enumerate(labels):
            ctk.CTkLabel(bottom, text=label, font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).pack(anchor="w", pady=(8 if i else 0, 2))
        self.customer_entry = ctk.CTkEntry(bottom, height=34, placeholder_text="Customer ID")
        self.customer_entry.pack(fill="x", pady=(0, 2))
        self.order_discount_entry = ctk.CTkEntry(bottom, height=34, placeholder_text="0")
        self.order_discount_entry.pack(fill="x", pady=(0, 2))
        self.payment_method = ctk.CTkComboBox(bottom, height=34, values=["cash", "card", "bank_transfer", "qr", "split"])
        self.payment_method.pack(fill="x", pady=(0, 2))
        self.cash_received_entry = ctk.CTkEntry(bottom, height=34, placeholder_text="0")
        self.cash_received_entry.pack(fill="x", pady=(0, 2))
        self.checkout_btn = ctk.CTkButton(bottom, text="Complete Sale", height=40, fg_color=SUCCESS, hover_color="#15803D", command=self.checkout)
        self.checkout_btn.pack(fill="x", pady=(10, 0))

    def _recalc_totals(self, *args):
        try:
            items = [{"product_id": l["product_id"], "quantity": l["quantity"], "unit_price": l["unit_price"], "discount": l["discount"]} for l in self.cart]
            order_discount = self.order_discount_entry.get() or "0"
            calc = self.app.context["checkout"].calculate_totals(items, self.customer_entry.get() or None, order_discount)
            currency = self.app.context["settings"].get("currency", "IDR")
            self.subtotal_label.configure(text=f"Subtotal: {currency} {calc['subtotal']}")
            self.discount_label.configure(text=f"Discount: {currency} {calc['order_discount']}")
            self.tax_label.configure(text=f"Tax: {currency} {calc['tax_total']}")
            self.total_label.configure(text=f"Total: {currency} {calc['total']}")
        except Exception as exc:
            self.total_label.configure(text=f"Total error: {exc}")

    # preserve original methods
    def scan_barcode(self):
        code = self.barcode_entry.get().strip()
        if not code:
            return
        product = self.app.context["products"].get_product(barcode=code, sku=code)
        if not product:
            info(self.app, "Not found", f"No product for {code}")
            return
        self.add_product_to_cart(product)
        self.barcode_entry.delete(0, "end")

    def search_products(self):
        q = self.search_entry.get().strip()
        products = self.app.context["products"].search_products(query=q)
        stock_map = self.app.context["inventory"].stock_map()
        rows = []
        for p in products:
            rows.append({
                "product_id": p["product_id"],
                "name": p["name"],
                "sku": p["sku"],
                "selling_price": p["selling_price"],
                "stock": str(stock_map.get(p["product_id"], 0)),
            })
        self.results_table.set_rows(rows, id_column="product_id")
        self.results_table.tree.bind("<Double-1>", lambda e: self.add_selected_result())

    def add_selected_result(self):
        pid = self.results_table.selected_iid()
        if pid:
            product = self.app.context["products"].get_product(product_id=pid)
            if product:
                self.add_product_to_cart(product)

    def add_product_to_cart(self, product):
        for line in self.cart:
            if line["product_id"] == product["product_id"]:
                line["quantity"] += Decimal("1")
                self.refresh_cart()
                return
        self.cart.append({
            "product_id": product["product_id"],
            "name": product["name"],
            "quantity": Decimal("1"),
            "unit_price": Decimal(product["selling_price"] or "0"),
            "discount": Decimal("0"),
        })
        self.refresh_cart()

    def refresh_cart(self):
        rows = []
        for line in self.cart:
            rows.append({
                "name": line["name"],
                "quantity": str(line["quantity"]),
                "unit_price": str(line["unit_price"]),
                "total": str((line["unit_price"] * line["quantity"]) - line["discount"]),
            })
        self.cart_table.set_rows(rows)
        self._recalc_totals()

    def update_qty(self):
        selection = self.cart_table.tree.selection()
        if not selection:
            return
        idx = self.cart_table.tree.index(selection[0])
        if idx < len(self.cart):
            try:
                new_qty = Decimal(self.qty_entry.get())
                if new_qty <= 0:
                    raise ValueError
                self.cart[idx]["quantity"] = new_qty
                self.refresh_cart()
            except Exception:
                info(self.app, "Invalid quantity", "Enter a positive number.")

    def remove_item(self):
        selection = self.cart_table.tree.selection()
        if selection:
            idx = self.cart_table.tree.index(selection[0])
            if 0 <= idx < len(self.cart):
                del self.cart[idx]
                self.refresh_cart()

    def clear_cart(self):
        self.cart = []
        self.refresh_cart()

    def checkout(self):
        if not self.cart:
            info(self.app, "Empty cart", "Add products before checkout.")
            return
        self.checkout_btn.configure(state="disabled")
        try:
            items = [{"product_id": l["product_id"], "quantity": l["quantity"], "unit_price": l["unit_price"], "discount": l["discount"]} for l in self.cart]
            method = self.payment_method.get()
            order_discount = self.order_discount_entry.get() or "0"
            calc = self.app.context["checkout"].calculate_totals(items, self.customer_entry.get() or None, order_discount)
            total = calc["total"]
            if method == "cash":
                cash_received = Decimal(self.cash_received_entry.get() or "0")
                if cash_received < total:
                    raise ValueError("Cash received is less than total.")
                payments = [{"method": "cash", "amount": total, "reference": ""}]
            else:
                payments = [{"method": method, "amount": total, "reference": ""}]
            shift_id = self.app.current_shift["shift_id"] if self.app.current_shift else None
            result = self.app.context["checkout"].checkout(self.app.current_user, {
                "items": items,
                "customer_id": self.customer_entry.get() or None,
                "order_discount": order_discount,
                "payments": payments,
                "shift_id": shift_id,
            })
            if result.get("success"):
                info(self.app, "Sale completed", f"Receipt {result['receipt_number']}.\nTotal: {total}")
                self.clear_cart()
        except Exception as exc:
            info(self.app, "Checkout failed", str(exc))
        finally:
            self.checkout_btn.configure(state="normal")