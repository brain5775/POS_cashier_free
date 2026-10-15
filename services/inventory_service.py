"""Inventory and stock movement management."""

from __future__ import annotations

from decimal import Decimal

from core.exceptions import PermissionError, InsufficientStockError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, non_negative_decimal, optional_text, required_text
from storage.csv_manager import CsvStore, Repository


class InventoryService:
    def __init__(self, store: CsvStore, settings=None, audit=None):
        self.store = store
        self.movements = Repository(store, "stock_movements.csv", "movement_id")
        self.products = Repository(store, "products.csv", "product_id")
        self.settings = settings
        self.audit = audit

    def allow_negative(self) -> bool:
        if self.settings is None:
            return False
        return self.settings.get("allow_negative_stock", "false").lower() in ("true", "1", "yes")

    def current_stock(self, product_id: str) -> Decimal:
        total = Decimal("0")
        for row in self.movements.all():
            if row.get("product_id") == product_id:
                total += Decimal(row.get("quantity_change") or "0")
        return total

    def stock_map(self) -> dict[str, Decimal]:
        result: dict[str, Decimal] = {}
        for row in self.movements.all():
            pid = row["product_id"]
            result[pid] = result.get(pid, Decimal("0")) + Decimal(row.get("quantity_change") or "0")
        return result

    def _product(self, product_id: str):
        product = self.products.get(product_id)
        if not product:
            raise ValidationError("Product not found.")
        return product

    def add_movement(self, transaction_id: str, product_id: str, quantity_change: Decimal | str, movement_type: str, reference_type: str, reference_id: str, user_id: str, reason: str = "", unit_cost: Decimal | str | None = None) -> dict:
        self._product(product_id)
        delta = Decimal(str(quantity_change))
        new_stock = self.current_stock(product_id) + delta
        if not self.allow_negative() and new_stock < 0:
            raise InsufficientStockError(f"Insufficient stock for product {product_id}.")
        row = {
            "movement_id": new_id("mov"),
            "transaction_id": transaction_id or "",
            "product_id": product_id,
            "quantity_change": str(delta),
            "movement_type": movement_type,
            "reference_type": reference_type,
            "reference_id": reference_id or "",
            "user_id": user_id or "",
            "timestamp": iso_now(),
            "reason": reason or movement_type,
            "unit_cost": "" if unit_cost is None else str(unit_cost),
        }
        self.movements.insert(row)
        return row

    def adjust_stock(self, actor, product_id: str, delta: Decimal | str, movement_type: str, reason: str, unit_cost=None) -> dict:
        if actor is not None and not has_permission(actor, "inventory.manage"):
            raise PermissionError("Missing permission: inventory.manage")
        reason = required_text(reason, "Reason")
        movement_type = required_text(movement_type, "Movement type")
        return self.add_movement("", product_id, delta, movement_type, "manual", "", (actor or {}).get("user_id", ""), reason, unit_cost)

    def set_opening_stock(self, actor, product_id: str, quantity: Decimal | str, unit_cost=None) -> dict:
        # Remove? We allow additional opening movement; not idempotent except caller.
        return self.adjust_stock(actor, product_id, quantity, "OPENING", "Opening stock", unit_cost)

    def low_stock_products(self, product_service) -> list[dict]:
        result = []
        stock_map = self.stock_map()
        for product in product_service.search_products(active_only=True):
            min_stock = Decimal(product.get("min_stock") or "0")
            stock = stock_map.get(product["product_id"], Decimal("0"))
            if stock < min_stock:
                result.append({**product, "current_stock": str(stock)})
        return result

    def valuation(self, product_service) -> Decimal:
        total = Decimal("0")
        stock_map = self.stock_map()
        cost_map = {p["product_id"]: Decimal(p.get("purchase_cost") or "0") for p in product_service.search_products(active_only=False)}
        for pid, stock in stock_map.items():
            total += stock * cost_map.get(pid, Decimal("0"))
        return total

    def movements_for_product(self, product_id: str) -> list[dict]:
        return [r for r in self.movements.all() if r.get("product_id") == product_id]

    def get_stock(self, product_id: str):
        return self.current_stock(product_id)

    def available_stock(self, product_id: str):
        return self.current_stock(product_id)

    def stock_for_product(self, product_id: str):
        return self.current_stock(product_id)