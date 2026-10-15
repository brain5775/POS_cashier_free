"""Supplier management."""

from __future__ import annotations

from core.exceptions import PermissionError, NotFoundError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, optional_text, required_text, valid_email, valid_phone
from storage.csv_manager import CsvStore, Repository


class SupplierService:
    def __init__(self, store: CsvStore, audit=None):
        self.store = store
        self.suppliers = Repository(store, "suppliers.csv", "supplier_id")
        self.audit = audit

    def list_suppliers(self, query: str = "", active_only: bool = False) -> list[dict]:
        q = query.strip().lower()
        rows = self.suppliers.all()
        if active_only:
            rows = [r for r in rows if r.get("is_active", "").lower() == "true"]
        if q:
            rows = [r for r in rows if q in " ".join([r.get("name", ""), r.get("contact_person", ""), r.get("phone", "")]).lower()]
        return sorted(rows, key=lambda r: r.get("name", "").lower())

    def create_supplier(self, actor, data: dict) -> dict:
        if actor is not None and not has_permission(actor, "suppliers.manage"):
            raise PermissionError("Missing permission: suppliers.manage")
        name = required_text(data.get("name"), "Supplier name")
        phone = optional_text(data.get("phone"))
        email = optional_text(data.get("email"))
        if not valid_phone(phone):
            raise ValidationError("Invalid phone number.")
        if not valid_email(email):
            raise ValidationError("Invalid email address.")
        now = iso_now()
        row = {
            "supplier_id": new_id("sup"),
            "name": name,
            "contact_person": optional_text(data.get("contact_person")),
            "phone": phone,
            "email": email,
            "address": optional_text(data.get("address")),
            "notes": optional_text(data.get("notes")),
            "is_active": "true",
            "created_at": now,
            "updated_at": now,
        }
        self.suppliers.insert(row)
        if self.audit and actor:
            self.audit.log(actor.get("user_id", ""), "create_supplier", "supplier", row["supplier_id"], name)
        return row

    def update_supplier(self, actor, supplier_id: str, data: dict) -> dict:
        if actor is not None and not has_permission(actor, "suppliers.manage"):
            raise PermissionError("Missing permission: suppliers.manage")
        existing = self.suppliers.get(supplier_id)
        if not existing:
            raise NotFoundError("Supplier not found.")
        patch = {
            "name": required_text(data.get("name", existing.get("name")), "Supplier name"),
            "contact_person": optional_text(data.get("contact_person", existing.get("contact_person"))),
            "phone": optional_text(data.get("phone", existing.get("phone"))),
            "email": optional_text(data.get("email", existing.get("email"))),
            "address": optional_text(data.get("address", existing.get("address"))),
            "notes": optional_text(data.get("notes", existing.get("notes"))),
            "is_active": data.get("is_active", existing.get("is_active", "true")),
            "updated_at": iso_now(),
        }
        self.suppliers.update(supplier_id, patch)
        return self.suppliers.get(supplier_id)

    def get_supplier(self, supplier_id: str):
        return self.suppliers.get(supplier_id)

    def list_all(self, query: str = "", active_only: bool = False):
        return self.list_suppliers(query=query, active_only=active_only)