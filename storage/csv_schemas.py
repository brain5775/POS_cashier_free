"""CSV schema definitions."""

from __future__ import annotations

SCHEMAS: dict[str, list[str]] = {
    "products.csv": ["product_id", "sku", "barcode", "name", "description", "category", "brand", "unit", "purchase_cost", "selling_price", "wholesale_price", "tax_category", "min_stock", "max_stock", "supplier_id", "image_path", "is_active", "created_at", "updated_at"],
    "categories.csv": ["category_id", "name", "description", "is_active", "created_at", "updated_at"],
    "sales.csv": ["sale_id", "receipt_number", "transaction_id", "customer_id", "user_id", "subtotal", "discount_total", "tax_total", "total", "payment_status", "status", "notes", "created_at"],
    "sale_items.csv": ["sale_item_id", "sale_id", "product_id", "product_name", "sku", "barcode", "quantity", "unit_price", "discount", "total", "line_cost", "created_at"],
    "payments.csv": ["payment_id", "sale_id", "payment_method", "amount", "reference", "status", "created_at"],
    "stock_movements.csv": ["movement_id", "transaction_id", "product_id", "quantity_change", "movement_type", "reference_type", "reference_id", "user_id", "timestamp", "reason", "unit_cost"],
    "customers.csv": ["customer_id", "name", "phone", "email", "address", "notes", "is_active", "loyalty_points", "discount_percent", "total_spent", "last_purchase_at", "created_at", "updated_at"],
    "suppliers.csv": ["supplier_id", "name", "contact_person", "phone", "email", "address", "notes", "is_active", "created_at", "updated_at"],
    "purchases.csv": ["purchase_id", "purchase_number", "supplier_id", "status", "subtotal", "tax_total", "total", "notes", "created_by", "created_at", "updated_at"],
    "purchase_items.csv": ["purchase_item_id", "purchase_id", "product_id", "product_name", "quantity_ordered", "quantity_received", "unit_cost", "total", "created_at"],
    "goods_receipts.csv": ["receipt_id", "purchase_id", "received_by", "received_at", "notes"],
    "goods_receipt_items.csv": ["receipt_item_id", "receipt_id", "purchase_id", "product_id", "quantity_received", "unit_cost", "created_at"],
    "returns.csv": ["return_id", "return_number", "sale_id", "customer_id", "user_id", "refund_total", "refund_method", "reason", "status", "created_at"],
    "return_items.csv": ["return_item_id", "return_id", "sale_item_id", "product_id", "quantity", "unit_price", "refund_amount", "restock", "created_at"],
    "users.csv": ["user_id", "username", "full_name", "role", "password_hash", "is_active", "created_at", "updated_at", "last_login_at"],
    "roles.csv": ["role_id", "name", "description"],
    "role_permissions.csv": ["role_name", "permission"],
    "cash_register_shifts.csv": ["shift_id", "user_id", "opened_at", "closed_at", "opening_cash", "closing_cash", "expected_cash", "cash_sales", "cash_refunds", "cash_in", "cash_out", "status", "notes"],
    "cash_movements.csv": ["cash_movement_id", "shift_id", "user_id", "movement_type", "amount", "reason", "reference_type", "reference_id", "created_at"],
    "audit_logs.csv": ["audit_id", "user_id", "action", "entity_type", "entity_id", "details", "created_at"],
    "settings.csv": ["setting_key", "setting_value", "updated_at"],
    "transaction_journal.csv": ["transaction_id", "operation", "status", "payload", "created_at", "updated_at", "completed_at", "error"],
    "price_history.csv": ["price_history_id", "product_id", "old_cost", "new_cost", "old_price", "new_price", "changed_by", "created_at"],
}
FILES = list(SCHEMAS.keys())