"""Customer management."""

from __future__ import annotations

from core.exceptions import PermissionError, DuplicateError, NotFoundError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, optional_text, required_text, valid_email, valid_phone
from storage.csv_manager import CsvStore, Repository


class CustomerService:
    def __init__(self, store: CsvStore, audit=None):
        self.store = store
        self.customers = Repository(store, "customers.csv", "customer_id")
        self.audit = audit

    def list_customers(self, query: str = "", active_only: bool = False) -> list[dict]:
        q = query.strip().lower()
        rows = self.customers.all()
        if active_only:
            rows = [r for r in rows if r.get("is_active", "").lower() == "true"]
        if q:
            rows = [r for r in rows if q in " ".join([r.get("name", ""), r.get("phone", ""), r.get("email", "")]).lower()]
        return sorted(rows, key=lambda r: r.get("name", "").lower())

    def create_customer(self, actor, data: dict) -> dict:
        if actor is not None and not has_permission(actor, "customers.manage"):
            raise PermissionError("Missing permission: customers.manage")
        name = required_text(data.get("name"), "Customer name")
        phone = optional_text(data.get("phone"))
        email = optional_text(data.get("email"))
        if not valid_phone(phone):
            raise ValidationError("Invalid phone number.")
        if not valid_email(email):
            raise ValidationError("Invalid email address.")
        now = iso_now()
        row = {
            "customer_id": new_id("cus"),
            "name": name,
            "phone": phone,
            "email": email,
            "address": optional_text(data.get("address")),
            "notes": optional_text(data.get("notes")),
            "is_active": "true",
            "loyalty_points": "0",
            "discount_percent": optional_text(data.get("discount_percent")) or "0",
            "total_spent": "0",
            "last_purchase_at": "",
            "created_at": now,
            "updated_at": now,
        }
        self.customers.insert(row)
        if self.audit and actor:
            self.audit.log(actor.get("user_id", ""), "create_customer", "customer", row["customer_id"], name)
        return row

    def update_customer(self, actor, customer_id: str, data: dict) -> dict:
        if actor is not None and not has_permission(actor, "customers.manage"):
            raise PermissionError("Missing permission: customers.manage")
        existing = self.customers.get(customer_id)
        if not existing:
            raise NotFoundError("Customer not found.")
        phone = optional_text(data.get("phone", existing.get("phone")))
        email = optional_text(data.get("email", existing.get("email")))
        if not valid_phone(phone):
            raise ValidationError("Invalid phone number.")
        if not valid_email(email):
            raise ValidationError("Invalid email address.")
        patch = {
            "name": required_text(data.get("name", existing.get("name")), "Customer name"),
            "phone": phone,
            "email": email,
            "address": optional_text(data.get("address", existing.get("address"))),
            "notes": optional_text(data.get("notes", existing.get("notes"))),
            "discount_percent": optional_text(data.get("discount_percent", existing.get("discount_percent"))) or "0",
            "is_active": data.get("is_active", existing.get("is_active", "true")),
            "updated_at": iso_now(),
        }
        self.customers.update(customer_id, patch)
        return self.customers.get(customer_id)

    def add_purchase_stats(self, customer_id: str | None, amount: Decimal, when: str) -> None:
        if not customer_id:
            return
        customer = self.customers.get(customer_id)
        if not customer:
            return
        total = Decimal(customer.get("total_spent") or "0") + amount
        self.customers.update(customer_id, {"total_spent": str(total), "last_purchase_at": when})

    def get_customer(self, customer_id: str):
        return self.customers.get(customer_id)

    def list_all(self, query: str = "", active_only: bool = False):
        return self.list_customers(query=query, active_only=active_only)