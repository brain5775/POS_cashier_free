"""Purchasing and receiving."""

from __future__ import annotations

from decimal import Decimal

from core.exceptions import PermissionError, NotFoundError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, optional_text, required_text
from storage.csv_manager import CsvStore, Repository


class PurchaseService:
    def __init__(self, store: CsvStore, product_service, inventory_service, audit=None):
        self.store = store
        self.purchases = Repository(store, "purchases.csv", "purchase_id")
        self.purchase_items = Repository(store, "purchase_items.csv", "purchase_item_id")
        self.receipts = Repository(store, "goods_receipts.csv", "receipt_id")
        self.receipt_items = Repository(store, "goods_receipt_items.csv", "receipt_item_id")
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.audit = audit

    def list_purchases(self, status: str = "", supplier_id: str = "") -> list[dict]:
        rows = self.purchases.all()
        if status:
            rows = [r for r in rows if r.get("status", "").lower() == status.lower()]
        if supplier_id:
            rows = [r for r in rows if r.get("supplier_id") == supplier_id]
        return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)

    def get_purchase(self, purchase_id: str) -> dict | None:
        return self.purchases.get(purchase_id)

    def purchase_items_for(self, purchase_id: str) -> list[dict]:
        return self.purchase_items.find(lambda r: r.get("purchase_id") == purchase_id)

    def create_purchase(self, actor, supplier_id: str, items: list[dict], notes: str = "") -> dict:
        if actor is not None and not has_permission(actor, "purchases.manage"):
            raise PermissionError("Missing permission: purchases.manage")
        if not items:
            raise ValidationError("Purchase requires at least one item.")
        now = iso_now()
        subtotal = Decimal("0")
        purchase_id = new_id("pur")
        number = f"PO-{purchase_id[-6:].upper()}"
        purchase = {
            "purchase_id": purchase_id,
            "purchase_number": number,
            "supplier_id": supplier_id or "",
            "status": "ordered",
            "subtotal": "0",
            "tax_total": "0",
            "total": "0",
            "notes": optional_text(notes),
            "created_by": (actor or {}).get("user_id", ""),
            "created_at": now,
            "updated_at": now,
        }
        self.purchases.insert(purchase)
        for item in items:
            product = self.product_service.get_product(product_id=item["product_id"])
            if not product:
                raise NotFoundError("Product not found.")
            qty = Decimal(str(item["quantity"]))
            if qty <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            unit_cost = Decimal(str(item.get("unit_cost", product.get("purchase_cost") or "0")))
            total = qty * unit_cost
            subtotal += total
            self.purchase_items.insert({
                "purchase_item_id": new_id("pi"),
                "purchase_id": purchase_id,
                "product_id": product["product_id"],
                "product_name": product["name"],
                "quantity_ordered": str(qty),
                "quantity_received": "0",
                "unit_cost": str(unit_cost),
                "total": str(total),
                "created_at": now,
            })
        purchase["subtotal"] = str(subtotal)
        purchase["total"] = str(subtotal)
        purchase["updated_at"] = iso_now()
        self.purchases.update(purchase_id, {"subtotal": purchase["subtotal"], "total": purchase["total"], "updated_at": purchase["updated_at"]})
        if self.audit and actor:
            self.audit.log(actor.get("user_id", ""), "create_purchase", "purchase", purchase_id, number)
        return self.purchases.get(purchase_id)

    def receive_goods(self, actor, purchase_id: str, received_items: list[dict], notes: str = "") -> dict:
        if actor is not None and not has_permission(actor, "purchases.manage"):
            raise PermissionError("Missing permission: purchases.manage")
        purchase = self.purchases.get(purchase_id)
        if not purchase:
            raise NotFoundError("Purchase not found.")
        if purchase.get("status") == "completed":
            raise ValidationError("Purchase already completed.")
        items = self.purchase_items_for(purchase_id)
        item_map = {i["purchase_item_id"]: i for i in items}
        # also map product id
        product_item_map = {i["product_id"]: i for i in items}
        now = iso_now()
        receipt_id = new_id("gr")
        self.receipts.insert({
            "receipt_id": receipt_id,
            "purchase_id": purchase_id,
            "received_by": (actor or {}).get("user_id", ""),
            "received_at": now,
            "notes": optional_text(notes),
        })
        for received in received_items:
            item_id = received.get("purchase_item_id")
            pitem = item_map.get(item_id) if item_id else product_item_map.get(received.get("product_id"))
            if not pitem:
                raise NotFoundError("Purchase item not found.")
            qty = Decimal(str(received["quantity"]))
            if qty <= 0:
                continue
            ordered = Decimal(pitem["quantity_ordered"])
            already = Decimal(pitem["quantity_received"] or "0")
            if already + qty > ordered:
                raise ValidationError("Received quantity exceeds ordered quantity.")
            unit_cost = Decimal(str(received.get("unit_cost", pitem["unit_cost"])))
            # transaction id? generate
            txn = new_id("txn")
            self.inventory_service.add_movement(txn, pitem["product_id"], qty, "PURCHASE_RECEIPT", "goods_receipt", receipt_id, (actor or {}).get("user_id", ""), f"Purchase {purchase.get('purchase_number')}", unit_cost)
            pitem["quantity_received"] = str(already + qty)
            self.purchase_items.update(pitem["purchase_item_id"], {"quantity_received": pitem["quantity_received"]})
            self.receipt_items.insert({
                "receipt_item_id": new_id("gri"),
                "receipt_id": receipt_id,
                "purchase_id": purchase_id,
                "product_id": pitem["product_id"],
                "quantity_received": str(qty),
                "unit_cost": str(unit_cost),
                "created_at": now,
            })
        # status
        refreshed = self.purchase_items_for(purchase_id)
        complete = all(Decimal(i["quantity_received"] or "0") >= Decimal(i["quantity_ordered"] or "0") for i in refreshed)
        any_received = any(Decimal(i["quantity_received"] or "0") > 0 for i in refreshed)
        status = "completed" if complete else "partially_received" if any_received else "ordered"
        self.purchases.update(purchase_id, {"status": status, "updated_at": iso_now()})
        if self.audit and actor:
            self.audit.log(actor.get("user_id", ""), "receive_goods", "purchase", purchase_id, receipt_id)
        return self.receipts.get(receipt_id)

    def create_po(self, *args, **kwargs):
        return self.create_purchase(*args, **kwargs)

    def receive_po(self, *args, **kwargs):
        return self.receive_goods(*args, **kwargs)

    def list_all(self, status: str = "", supplier_id: str = ""):
        return self.list_purchases(status=status, supplier_id=supplier_id)