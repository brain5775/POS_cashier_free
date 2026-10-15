"""Purchasing page."""

from __future__ import annotations

from decimal import Decimal

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class PurchasingPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Purchasing", "Purchase orders and goods receiving")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(toolbar, text="New PO", height=34, command=self.new_po).pack(side="left", padx=(0, 6))
        ctk.CTkButton(toolbar, text="Receive Selected", height=34, command=self.receive).pack(side="left", padx=6)
        ctk.CTkButton(toolbar, text="Refresh", height=34, fg_color="#64748B", hover_color="#475569", command=self.refresh).pack(side="left", padx=6)
        self.table = DataTable(self.body, [("purchase_number", "Number", 120), ("status", "Status", 140), ("supplier_id", "Supplier", 120), ("total", "Total", 100), ("created_at", "Created", 170)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        rows = self.app.context["purchases"].list_purchases()
        self.table.set_rows(rows, id_column="purchase_id")

    def new_po(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("New Purchase Order")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry("430x360")
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        fields = {}
        for i, (key, label, placeholder) in enumerate([
            ("supplier", "Supplier ID (optional)", "Supplier ID"),
            ("product", "Product ID", "Product ID"),
            ("qty", "Quantity", "Quantity"),
            ("cost", "Unit cost", "Unit cost"),
        ]):
            ctk.CTkLabel(frame, text=label, font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=i * 2, column=0, sticky="w", pady=(8, 2))
            e = ctk.CTkEntry(frame, height=34, placeholder_text=placeholder)
            e.grid(row=i * 2 + 1, column=0, sticky="ew", pady=(0, 2))
            fields[key] = e
        def save():
            try:
                item = {"product_id": fields["product"].get(), "quantity": fields["qty"].get(), "unit_cost": fields["cost"].get() or None}
                po = self.app.context["purchases"].create_purchase(self.app.current_user, fields["supplier"].get(), [item], "")
                dialog.destroy()
                self.refresh()
                info(self.app, "PO created", po["purchase_number"])
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Save", height=34, command=save).grid(row=8, column=0, sticky="ew", pady=(12, 0))

    def receive(self):
        pid = self.table.selected_iid()
        if not pid:
            return
        items = self.app.context["purchases"].purchase_items_for(pid)
        dialog_items = []
        for it in items:
            remaining = Decimal(it["quantity_ordered"]) - Decimal(it["quantity_received"] or "0")
            if remaining > 0:
                dialog_items.append((it, remaining))
        if not dialog_items:
            info(self.app, "Nothing to receive", "All items already received.")
            return
        received = [{"purchase_item_id": it["purchase_item_id"], "product_id": it["product_id"], "quantity": str(remaining)} for it, remaining in dialog_items]
        try:
            self.app.context["purchases"].receive_goods(self.app.current_user, pid, received, "Received via UI")
            self.refresh()
            info(self.app, "Received", "Goods receipt created.")
        except Exception as exc:
            info(self.app, "Error", str(exc))