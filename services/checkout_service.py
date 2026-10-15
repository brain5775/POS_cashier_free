"""Checkout and payment processing."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from core.exceptions import PermissionError, InsufficientStockError, TransactionError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, optional_text
from storage.csv_manager import CsvStore, Repository


CENT = Decimal("0.01")


class CheckoutService:
    def __init__(self, store: CsvStore, transaction_manager, product_service, inventory_service, customer_service, settings_service, cash_register_service=None, audit=None):
        self.store = store
        self.txn = transaction_manager
        self.products = product_service
        self.inventory = inventory_service
        self.customers = customer_service
        self.settings = settings_service
        self.cash_register = cash_register_service
        self.audit = audit
        self.sales = Repository(store, "sales.csv", "sale_id")
        self.sale_items = Repository(store, "sale_items.csv", "sale_item_id")
        self.payments = Repository(store, "payments.csv", "payment_id")

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(CENT, rounding=ROUND_HALF_UP)

    def calculate_totals(self, items: list[dict], customer_id: str | None = None, order_discount: Decimal | str = "0") -> dict:
        products_by_id = {p["product_id"]: p for p in self.products.search_products(active_only=False)}
        subtotal = Decimal("0")
        line_items = []
        for item in items:
            product = products_by_id.get(item["product_id"]) or self.products.get_product(product_id=item["product_id"])
            if not product:
                raise ValidationError("Product not found.")
            if product.get("is_active", "").lower() != "true":
                raise ValidationError(f"Product is inactive: {product.get('name')}")
            qty = Decimal(str(item["quantity"]))
            if qty <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            unit_price = Decimal(str(item.get("unit_price", product["selling_price"])))
            discount = Decimal(str(item.get("discount", "0")))
            line_total = (unit_price * qty) - discount
            if line_total < 0:
                raise ValidationError("Line total cannot be negative.")
            subtotal += line_total
            line_items.append({
                "product": product,
                "quantity": qty,
                "unit_price": unit_price,
                "discount": discount,
                "line_total": line_total,
            })
        order_discount = Decimal(str(order_discount or "0"))
        if order_discount < 0 or order_discount > subtotal:
            raise ValidationError("Invalid order discount.")
        taxable_base = subtotal - order_discount
        tax_rate = Decimal(str(self.settings.get("tax_rate", "0") or "0"))
        tax_mode = self.settings.get("tax_mode", "exclusive")
        if tax_mode == "inclusive":
            if tax_rate > 0:
                tax = taxable_base - (taxable_base / (Decimal("1") + tax_rate))
            else:
                tax = Decimal("0")
            total = taxable_base
        else:
            tax = taxable_base * tax_rate
            total = taxable_base + tax
        total = self._money(total)
        tax = self._money(tax)
        subtotal = self._money(subtotal)
        order_discount = self._money(order_discount)
        # customer discount
        if customer_id:
            customer = self.customers.customers.get(customer_id)
            if customer:
                try:
                    pct = Decimal(customer.get("discount_percent") or "0")
                except Exception:
                    pct = Decimal("0")
                if pct > 0:
                    customer_discount = self._money(total * (pct / Decimal("100")))
                    if order_discount == 0:
                        order_discount = customer_discount
                        taxable_base = subtotal - order_discount
                        if tax_mode == "inclusive":
                            tax = taxable_base - (taxable_base / (Decimal("1") + tax_rate)) if tax_rate > 0 else Decimal("0")
                            total = taxable_base
                        else:
                            tax = taxable_base * tax_rate
                            total = taxable_base + tax
                        total = self._money(total)
                        tax = self._money(tax)
                        order_discount = self._money(order_discount)
        return {
            "line_items": line_items,
            "subtotal": subtotal,
            "order_discount": order_discount,
            "tax_total": tax,
            "total": total,
            "tax_rate": tax_rate,
            "tax_mode": tax_mode,
        }

    def checkout(self, actor, request: dict) -> dict:
        if actor is None or not has_permission(actor, "pos.use"):
            raise PermissionError("Missing permission: pos.use")
        items = request.get("items") or []
        if not items:
            raise ValidationError("Cart is empty.")
        customer_id = request.get("customer_id") or None
        order_discount = request.get("order_discount", "0")
        payments = request.get("payments") or []
        if not payments:
            raise ValidationError("Payment is required.")
        shift_id = request.get("shift_id")
        idempotency_key = request.get("idempotency_key") or new_id("idem")

        # Idempotency: recover completed checkout with same key.
        for journal in self.txn.pending() + []:  # also scan completed
            pass
        for row in self.store.read("transaction_journal.csv"):
            if row.get("operation") == "checkout" and row.get("status") == "completed":
                try:
                    payload = self.txn.payload(row["transaction_id"])
                except Exception:
                    payload = {}
                if payload.get("idempotency_key") == idempotency_key:
                    sale = self.sales.one(lambda r: r.get("transaction_id") == row["transaction_id"])
                    if sale:
                        return {"success": True, "sale_id": sale["sale_id"], "receipt_number": sale["receipt_number"], "transaction_id": row["transaction_id"], "duplicate": True}

        # Validate stock
        calculated = self.calculate_totals(items, customer_id, order_discount)
        for line in calculated["line_items"]:
            product = line["product"]
            stock = self.inventory.current_stock(product["product_id"])
            if stock < line["quantity"] and not self.inventory.allow_negative():
                raise InsufficientStockError(f"Insufficient stock for {product['name']}. Available: {stock}")

        # Payments sum
        payment_total = sum((Decimal(str(p.get("amount", "0"))) for p in payments), Decimal("0"))
        if self._money(payment_total) != calculated["total"]:
            raise ValidationError(f"Payment total {payment_total} does not match sale total {calculated['total']}.")

        transaction_id = self.txn.begin("checkout", {
            "idempotency_key": idempotency_key,
            "user_id": actor.get("user_id"),
            "customer_id": customer_id,
        })

        try:
            # Existing sale for this transaction?
            sale = self.sales.one(lambda r: r.get("transaction_id") == transaction_id)
            if not sale:
                sale_id = new_id("sale")
                receipt_number = f"RCP-{sale_id[-8:].upper()}"
                now = iso_now()
                sale = {
                    "sale_id": sale_id,
                    "receipt_number": receipt_number,
                    "transaction_id": transaction_id,
                    "customer_id": customer_id or "",
                    "user_id": actor.get("user_id", ""),
                    "subtotal": str(calculated["subtotal"]),
                    "discount_total": str(calculated["order_discount"]),
                    "tax_total": str(calculated["tax_total"]),
                    "total": str(calculated["total"]),
                    "payment_status": "paid",
                    "status": "completed",
                    "notes": optional_text(request.get("notes")),
                    "created_at": now,
                }
                self.sales.insert(sale)
            else:
                sale_id = sale["sale_id"]
                receipt_number = sale["receipt_number"]

            # Sale items
            existing_items = self.sale_items.find(lambda r: r.get("sale_id") == sale_id)
            if not existing_items:
                for line in calculated["line_items"]:
                    product = line["product"]
                    self.sale_items.insert({
                        "sale_item_id": new_id("si"),
                        "sale_id": sale_id,
                        "product_id": product["product_id"],
                        "product_name": product["name"],
                        "sku": product["sku"],
                        "barcode": product.get("barcode", ""),
                        "quantity": str(line["quantity"]),
                        "unit_price": str(line["unit_price"]),
                        "discount": str(line["discount"]),
                        "total": str(self._money(line["line_total"])),
                        "line_cost": str(Decimal(product.get("purchase_cost") or "0") * line["quantity"]),
                        "created_at": iso_now(),
                    })

            # Payments
            existing_payments = self.payments.find(lambda r: r.get("sale_id") == sale_id)
            if not existing_payments:
                for payment in payments:
                    self.payments.insert({
                        "payment_id": new_id("pay"),
                        "sale_id": sale_id,
                        "payment_method": payment.get("method", "cash"),
                        "amount": str(Decimal(str(payment.get("amount", "0")))),
                        "reference": optional_text(payment.get("reference")),
                        "status": "completed",
                        "created_at": iso_now(),
                    })

            # Stock movements
            existing_moves = self.store.read("stock_movements.csv")
            txn_moves = [m for m in existing_moves if m.get("transaction_id") == transaction_id]
            if not txn_moves:
                for line in calculated["line_items"]:
                    product = line["product"]
                    self.inventory.add_movement(
                        transaction_id, product["product_id"], -line["quantity"], "SALE", "sale", sale_id,
                        actor.get("user_id", ""), f"Sale {receipt_number}",
                        Decimal(product.get("purchase_cost") or "0")
                    )

            # Customer stats
            self.customers.add_purchase_stats(customer_id, calculated["total"], iso_now())

            # Cash register movements
            if self.cash_register is not None and shift_id:
                cash_amount = sum((Decimal(str(p.get("amount", "0"))) for p in payments if p.get("method", "").lower() == "cash"), Decimal("0"))
                if cash_amount > 0:
                    self.cash_register.add_movement(shift_id, actor, "sale", cash_amount, f"Sale {receipt_number}", "sale", sale_id)

            # Audit
            if self.audit:
                self.audit.log(actor.get("user_id", ""), "checkout", "sale", sale_id, receipt_number)

            self.txn.complete(transaction_id)
            return {
                "success": True,
                "sale_id": sale_id,
                "receipt_number": receipt_number,
                "transaction_id": transaction_id,
                "total": calculated["total"],
                "change": self._money(payment_total - calculated["total"]),
            }
        except Exception as exc:
            self.txn.fail(transaction_id, str(exc))
            raise TransactionError(f"Checkout failed: {exc}") from exc

    def process_checkout(self, *args, **kwargs):
        return self.checkout(*args, **kwargs)

    def process(self, *args, **kwargs):
        return self.checkout(*args, **kwargs)