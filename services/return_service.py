"""Returns and refunds."""

from __future__ import annotations

from decimal import Decimal

from core.exceptions import PermissionError, NotFoundError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, optional_text
from storage.csv_manager import CsvStore, Repository


class ReturnService:
    def __init__(self, store: CsvStore, inventory_service, cash_register_service=None, customer_service=None, audit=None, sales_service=None):
        self.store = store
        self.inventory = inventory_service
        self.cash_register = cash_register_service
        self.customers = customer_service
        self.audit = audit
        self.sales_service = sales_service or SalesService(store, inventory_service)
        self.returns = Repository(store, "returns.csv", "return_id")
        self.return_items = Repository(store, "return_items.csv", "return_item_id")
        self.sales = Repository(store, "sales.csv", "sale_id")
        self.sale_items = Repository(store, "sale_items.csv", "sale_item_id")

    def returned_quantity(self, sale_item_id: str) -> Decimal:
        total = Decimal("0")
        for r in self.return_items.all():
            if r.get("sale_item_id") == sale_item_id:
                total += Decimal(r.get("quantity") or "0")
        return total

    def eligible_items(self, sale_id: str) -> list[dict]:
        result = []
        for item in self.sales_service.get_sale_items(sale_id):
            returned = self.returned_quantity(item["sale_item_id"])
            original = Decimal(item["quantity"])
            remaining = original - returned
            if remaining > 0:
                result.append({**item, "returned_quantity": str(returned), "returnable_quantity": str(remaining)})
        return result

    def create_return(self, actor, sale_id: str, items: list[dict], reason: str, refund_method: str = "cash", restock_default: bool = True) -> dict:
        if actor is not None and not has_permission(actor, "returns.create"):
            raise PermissionError("Missing permission: returns.create")
        sale = self.sales.get(sale_id)
        if not sale or sale.get("status") != "completed":
            raise ValidationError("Only completed sales can be returned.")
        if not items:
            raise ValidationError("Return requires at least one item.")
        reason = optional_text(reason) or "Return"
        now = iso_now()
        return_id = new_id("ret")
        number = f"RET-{return_id[-6:].upper()}"
        refund_total = Decimal("0")
        return_row = {
            "return_id": return_id,
            "return_number": number,
            "sale_id": sale_id,
            "customer_id": sale.get("customer_id", ""),
            "user_id": (actor or {}).get("user_id", ""),
            "refund_total": "0",
            "refund_method": refund_method,
            "reason": reason,
            "status": "completed",
            "created_at": now,
        }
        self.returns.insert(return_row)
        for item in items:
            sale_item_id = item["sale_item_id"]
            sale_item = self.sale_items.get(sale_item_id)
            if not sale_item or sale_item.get("sale_id") != sale_id:
                raise NotFoundError("Sale item not found.")
            qty = Decimal(str(item["quantity"]))
            if qty <= 0:
                continue
            returnable = Decimal(sale_item["quantity"]) - self.returned_quantity(sale_item_id)
            if qty > returnable:
                raise ValidationError(f"Cannot return more than {returnable} units.")
            unit_price = Decimal(sale_item["unit_price"])
            refund_amount = unit_price * qty
            # subtract item discount proportion? simple.
            restock = "true" if item.get("restock", restock_default) else "false"
            if restock == "true":
                self.inventory.add_movement(
                    "", sale_item["product_id"], qty, "RETURN_RESTOCK", "return", return_id,
                    (actor or {}).get("user_id", ""), f"Return {number}", Decimal(sale_item.get("line_cost", "0")) / Decimal(sale_item["quantity"]) if Decimal(sale_item["quantity"]) else Decimal("0")
                )
            self.return_items.insert({
                "return_item_id": new_id("ri"),
                "return_id": return_id,
                "sale_item_id": sale_item_id,
                "product_id": sale_item["product_id"],
                "quantity": str(qty),
                "unit_price": str(unit_price),
                "refund_amount": str(refund_amount),
                "restock": restock,
                "created_at": now,
            })
            refund_total += refund_amount

        self.returns.update(return_id, {"refund_total": str(refund_total)})
        if self.cash_register is not None and refund_method.lower() == "cash":
            user_id = (actor or {}).get("user_id", "")
            shift = self.cash_register.current_shift(user_id)
            if shift:
                self.cash_register.add_movement(shift["shift_id"], actor, "refund", refund_total, f"Return {number}", "return", return_id)
        if self.audit:
            self.audit.log((actor or {}).get("user_id", ""), "create_return", "return", return_id, number)
        return self.returns.get(return_id)

    def process_return(self, *args, **kwargs):
        return self.create_return(*args, **kwargs)

    def create(self, *args, **kwargs):
        return self.create_return(*args, **kwargs)