"""Sales history and voiding."""

from __future__ import annotations

from decimal import Decimal

from core.exceptions import NotFoundError, PermissionError as AppPermissionError, ValidationError
from core.permissions import has_permission
from core.validation import iso_now, optional_text
from storage.csv_manager import CsvStore, Repository


class SalesService:
    def __init__(self, store: CsvStore, inventory_service=None, audit=None):
        self.store = store
        self.inventory = inventory_service
        self.sales = Repository(store, "sales.csv", "sale_id")
        self.sale_items = Repository(store, "sale_items.csv", "sale_item_id")
        self.payments = Repository(store, "payments.csv", "payment_id")
        self.audit = audit

    def list_sales(self, user_id: str = "", date_from: str = "", date_to: str = "", status: str = "") -> list[dict]:
        rows = self.sales.all()
        if user_id:
            rows = [r for r in rows if r.get("user_id") == user_id]
        if status:
            rows = [r for r in rows if r.get("status", "").lower() == status.lower()]
        if date_from:
            rows = [r for r in rows if r.get("created_at", "") >= date_from]
        if date_to:
            rows = [r for r in rows if r.get("created_at", "") <= date_to]
        return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)

    def get_sale(self, sale_id: str) -> dict | None:
        return self.sales.get(sale_id)

    def get_sale_items(self, sale_id: str) -> list[dict]:
        return self.sale_items.find(lambda r: r.get("sale_id") == sale_id)

    def get_payments(self, sale_id: str) -> list[dict]:
        return self.payments.find(lambda r: r.get("sale_id") == sale_id)

    def void_sale(self, actor, sale_id: str, reason: str) -> None:
        if not has_permission(actor, "returns.approve"):
            raise AppPermissionError("You do not have permission to void sales.")
        sale = self.sales.get(sale_id)
        if not sale:
            raise NotFoundError("Sale not found.")
        if sale.get("status") == "voided":
            return
        if sale.get("status") != "completed":
            raise ValidationError("Only completed sales can be voided.")
        reason = optional_text(reason) or "Voided"
        if self.inventory is not None:
            for item in self.get_sale_items(sale_id):
                self.inventory.add_movement(
                    sale.get("transaction_id", ""), item["product_id"], Decimal(item["quantity"]),
                    "VOID", "sale", sale_id, (actor or {}).get("user_id", ""), f"Void sale {sale.get('receipt_number')} - {reason}",
                    Decimal(item.get("line_cost", "0")) / Decimal(item["quantity"]) if Decimal(item.get("quantity") or "0") else Decimal("0")
                )
        self.sales.update(sale_id, {"status": "voided", "notes": f"{sale.get('notes','')} | VOID: {reason}".strip()})
        if self.audit:
            self.audit.log((actor or {}).get("user_id", ""), "void_sale", "sale", sale_id, reason)

    def list_all(self, user_id: str = "", date_from: str = "", date_to: str = "", status: str = ""):
        return self.list_sales(user_id=user_id, date_from=date_from, date_to=date_to, status=status)

    def void(self, *args, **kwargs):
        return self.void_sale(*args, **kwargs)