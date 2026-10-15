"""Product and category management."""

from __future__ import annotations

from decimal import Decimal

from core.exceptions import PermissionError, DuplicateError, NotFoundError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, non_negative_decimal, optional_text, required_text
from storage.csv_manager import CsvStore, Repository


class ProductService:
    def __init__(self, store: CsvStore, audit=None):
        self.store = store
        self.products = Repository(store, "products.csv", "product_id")
        self.categories = Repository(store, "categories.csv", "category_id")
        self.price_history = Repository(store, "price_history.csv", "price_history_id")
        self.audit = audit

    def _ensure_permission(self, actor, permission):
        if actor is not None and not has_permission(actor, permission):
            raise PermissionError(f"Missing permission: {permission}")

    # Categories
    def list_categories(self, active_only: bool = False) -> list[dict]:
        rows = self.categories.all()
        if active_only:
            rows = [r for r in rows if r.get("is_active", "").lower() == "true"]
        return sorted(rows, key=lambda r: r.get("name", "").lower())

    def create_category(self, actor, name: str, description: str = "") -> dict:
        self._ensure_permission(actor, "products.manage")
        name = required_text(name, "Category name")
        if self.categories.one(lambda r: r["name"].lower() == name.lower()):
            raise DuplicateError("Category already exists.")
        now = iso_now()
        row = {"category_id": new_id("cat"), "name": name, "description": optional_text(description), "is_active": "true", "created_at": now, "updated_at": now}
        self.categories.insert(row)
        if self.audit:
            self.audit.log((actor or {}).get("user_id", ""), "create_category", "category", row["category_id"], name)
        return row

    def update_category(self, actor, category_id: str, patch: dict) -> dict:
        self._ensure_permission(actor, "products.manage")
        row = self.categories.get(category_id)
        if not row:
            raise NotFoundError("Category not found.")
        if "name" in patch:
            patch["name"] = required_text(patch["name"], "Category name")
        patch["updated_at"] = iso_now()
        self.categories.update(category_id, patch)
        return self.categories.get(category_id)

    def deactivate_category(self, actor, category_id: str) -> None:
        self.update_category(actor, category_id, {"is_active": "false"})

    # Products
    def _validate_product(self, data: dict, existing_id: str | None = None):
        sku = required_text(data.get("sku"), "SKU")
        name = required_text(data.get("name"), "Name")
        if self.products.one(lambda r: r["sku"].lower() == sku.lower() and r["product_id"] != (existing_id or "")):
            raise DuplicateError("SKU already exists.")
        barcode = optional_text(data.get("barcode"))
        if barcode and self.products.one(lambda r: r["barcode"] == barcode and r["product_id"] != (existing_id or "")):
            raise DuplicateError("Barcode already exists.")
        for field in ("purchase_cost", "selling_price"):
            non_negative_decimal(data.get(field, "0"), field)
        min_stock = non_negative_decimal(data.get("min_stock", "0"), "Minimum stock")
        max_stock = non_negative_decimal(data.get("max_stock", ""), "Maximum stock") if optional_text(data.get("max_stock")) else Decimal("0")
        if max_stock > 0 and min_stock > max_stock:
            raise ValidationError("Minimum stock cannot exceed maximum stock.")
        return sku, name, barcode

    def create_product(self, actor, data: dict) -> dict:
        self._ensure_permission(actor, "products.manage")
        sku, name, barcode = self._validate_product(data)
        now = iso_now()
        row = {
            "product_id": new_id("prd"),
            "sku": sku,
            "barcode": barcode,
            "name": name,
            "description": optional_text(data.get("description")),
            "category": optional_text(data.get("category")),
            "brand": optional_text(data.get("brand")),
            "unit": optional_text(data.get("unit")) or "pcs",
            "purchase_cost": str(non_negative_decimal(data.get("purchase_cost", "0"), "Purchase cost")),
            "selling_price": str(non_negative_decimal(data.get("selling_price", "0"), "Selling price")),
            "wholesale_price": str(non_negative_decimal(data.get("wholesale_price", ""), "Wholesale price")) if optional_text(data.get("wholesale_price")) else "",
            "tax_category": optional_text(data.get("tax_category")),
            "min_stock": str(non_negative_decimal(data.get("min_stock", "0"), "Minimum stock")),
            "max_stock": str(non_negative_decimal(data.get("max_stock", ""), "Maximum stock")) if optional_text(data.get("max_stock")) else "",
            "supplier_id": optional_text(data.get("supplier_id")),
            "image_path": optional_text(data.get("image_path")),
            "is_active": "true",
            "created_at": now,
            "updated_at": now,
        }
        self.products.insert(row)
        if self.audit:
            self.audit.log((actor or {}).get("user_id", ""), "create_product", "product", row["product_id"], sku)
        return row

    def update_product(self, actor, product_id: str, data: dict) -> dict:
        self._ensure_permission(actor, "products.manage")
        existing = self.products.get(product_id)
        if not existing:
            raise NotFoundError("Product not found.")
        sku, name, barcode = self._validate_product(data, existing_id=product_id)
        old_cost = Decimal(existing.get("purchase_cost") or "0")
        old_price = Decimal(existing.get("selling_price") or "0")
        new_cost = non_negative_decimal(data.get("purchase_cost", existing.get("purchase_cost", "0")), "Purchase cost")
        new_price = non_negative_decimal(data.get("selling_price", existing.get("selling_price", "0")), "Selling price")
        patch = {
            "sku": sku,
            "barcode": barcode,
            "name": name,
            "description": optional_text(data.get("description", existing.get("description"))),
            "category": optional_text(data.get("category", existing.get("category"))),
            "brand": optional_text(data.get("brand", existing.get("brand"))),
            "unit": optional_text(data.get("unit", existing.get("unit"))) or "pcs",
            "purchase_cost": str(new_cost),
            "selling_price": str(new_price),
            "wholesale_price": str(non_negative_decimal(data.get("wholesale_price", existing.get("wholesale_price") or ""), "Wholesale price")) if optional_text(data.get("wholesale_price", existing.get("wholesale_price"))) else "",
            "tax_category": optional_text(data.get("tax_category", existing.get("tax_category"))),
            "min_stock": str(non_negative_decimal(data.get("min_stock", existing.get("min_stock", "0")), "Minimum stock")),
            "max_stock": str(non_negative_decimal(data.get("max_stock", existing.get("max_stock") or ""), "Maximum stock")) if optional_text(data.get("max_stock", existing.get("max_stock"))) else "",
            "supplier_id": optional_text(data.get("supplier_id", existing.get("supplier_id"))),
            "image_path": optional_text(data.get("image_path", existing.get("image_path"))),
            "is_active": data.get("is_active", existing.get("is_active", "true")),
            "updated_at": iso_now(),
        }
        self.products.update(product_id, patch)
        if old_cost != new_cost or old_price != new_price:
            self.price_history.insert({
                "price_history_id": new_id("ph"),
                "product_id": product_id,
                "old_cost": str(old_cost),
                "new_cost": str(new_cost),
                "old_price": str(old_price),
                "new_price": str(new_price),
                "changed_by": (actor or {}).get("user_id", ""),
                "created_at": iso_now(),
            })
        if self.audit:
            self.audit.log((actor or {}).get("user_id", ""), "update_product", "product", product_id, sku)
        return self.products.get(product_id)

    def deactivate_product(self, actor, product_id: str) -> None:
        self.update_product(actor, product_id, {"is_active": "false"})

    def get_product(self, product_id: str | None = None, barcode: str | None = None, sku: str | None = None) -> dict | None:
        if product_id:
            return self.products.get(product_id)
        if barcode:
            return self.products.one(lambda r: r.get("barcode") == barcode and r.get("is_active", "").lower() == "true")
        if sku:
            return self.products.one(lambda r: r.get("sku", "").lower() == sku.lower())
        return None

    def search_products(self, query: str = "", category: str = "", active_only: bool = True, low_stock_only: bool = False, inventory=None) -> list[dict]:
        q = query.strip().lower()
        result = []
        for p in self.products.all():
            if active_only and p.get("is_active", "").lower() != "true":
                continue
            if category and p.get("category", "").lower() != category.lower():
                continue
            if q and q not in " ".join([p.get("name", ""), p.get("sku", ""), p.get("barcode", ""), p.get("brand", "")]).lower():
                continue
            if low_stock_only and inventory is not None:
                stock = inventory.current_stock(p["product_id"])
                if stock >= Decimal(p.get("min_stock") or "0"):
                    continue
            result.append(p)
        return sorted(result, key=lambda r: r.get("name", "").lower())

    def paginate(self, rows: list, page: int, page_size: int) -> tuple[list, int]:
        page = max(1, page)
        page_size = max(1, min(page_size, 200))
        start = (page - 1) * page_size
        return rows[start:start + page_size], (len(rows) + page_size - 1) // page_size

    def export_products(self) -> list[dict]:
        return self.products.all()

    def preview_import(self, rows: list[dict]) -> dict:
        return self.import_products(None, rows, dry_run=True, validate_permissions=False)

    def import_products(self, actor, rows: list[dict], dry_run: bool = False, validate_permissions: bool = True) -> dict:
        if validate_permissions and actor is not None and not has_permission(actor, "products.manage"):
            raise PermissionError("Missing permission: products.manage")
        report = {"created": 0, "invalid": [], "duplicates": []}
        for index, row in enumerate(rows, start=1):
            try:
                sku = required_text(row.get("sku"), "SKU")
                name = required_text(row.get("name"), "Name")
                if self.products.one(lambda r: r["sku"].lower() == sku.lower()):
                    report["duplicates"].append({"row": index, "sku": sku})
                    continue
                data = {
                    "sku": sku,
                    "barcode": row.get("barcode", ""),
                    "name": name,
                    "description": row.get("description", ""),
                    "category": row.get("category", ""),
                    "brand": row.get("brand", ""),
                    "unit": row.get("unit", "") or "pcs",
                    "purchase_cost": row.get("purchase_cost", "0") or "0",
                    "selling_price": row.get("selling_price", "0") or "0",
                    "wholesale_price": row.get("wholesale_price", "") or "",
                    "tax_category": row.get("tax_category", ""),
                    "min_stock": row.get("min_stock", "0") or "0",
                    "max_stock": row.get("max_stock", "") or "",
                    "supplier_id": row.get("supplier_id", ""),
                }
                self._validate_product(data)
                if not dry_run:
                    self.create_product(actor if actor is not None else {"user_id": ""}, data) if False else self.products.insert({
                        "product_id": new_id("prd"),
                        "sku": data["sku"],
                        "barcode": data["barcode"],
                        "name": data["name"],
                        "description": data["description"],
                        "category": data["category"],
                        "brand": data["brand"],
                        "unit": data["unit"],
                        "purchase_cost": str(non_negative_decimal(data["purchase_cost"], "Purchase cost")),
                        "selling_price": str(non_negative_decimal(data["selling_price"], "Selling price")),
                        "wholesale_price": str(non_negative_decimal(data["wholesale_price"], "Wholesale price")) if str(data["wholesale_price"]).strip() else "",
                        "tax_category": data["tax_category"],
                        "min_stock": str(non_negative_decimal(data["min_stock"], "Minimum stock")),
                        "max_stock": str(non_negative_decimal(data["max_stock"], "Maximum stock")) if str(data["max_stock"]).strip() else "",
                        "supplier_id": data["supplier_id"],
                        "image_path": "",
                        "is_active": "true",
                        "created_at": iso_now(),
                        "updated_at": iso_now(),
                    })
                report["created"] += 1
            except Exception as exc:
                report["invalid"].append({"row": index, "error": str(exc)})
        return report

    def get_product_by_barcode(self, barcode: str):
        return self.get_product(barcode=barcode)

    def get_product_by_sku(self, sku: str):
        return self.get_product(sku=sku)

    def get_by_barcode(self, barcode: str):
        return self.get_product(barcode=barcode)

    def get_by_sku(self, sku: str):
        return self.get_product(sku=sku)

    def list_products(self, query: str = "", category: str = "", active_only: bool = True, low_stock_only: bool = False):
        if low_stock_only:
            return self.search_products(query=query, category=category, active_only=active_only, low_stock_only=True, inventory=None)
        return self.search_products(query=query, category=category, active_only=active_only)

    def search(self, *args, **kwargs):
        return self.search_products(*args, **kwargs)