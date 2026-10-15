"""Role and permission helpers."""

from __future__ import annotations

PERMISSIONS = [
    "dashboard.view",
    "pos.use",
    "sales.view",
    "returns.create",
    "returns.approve",
    "products.view",
    "products.manage",
    "inventory.view",
    "inventory.manage",
    "purchases.view",
    "purchases.manage",
    "suppliers.manage",
    "customers.view",
    "customers.manage",
    "cash_register.use",
    "cash_register.manage",
    "reports.view",
    "reports.export",
    "users.manage",
    "settings.manage",
    "backup.manage",
]

ROLE_PERMISSIONS = {
    "Administrator": PERMISSIONS,
    "Manager": [
        "dashboard.view", "pos.use", "sales.view", "returns.create", "returns.approve",
        "products.view", "products.manage", "inventory.view", "inventory.manage",
        "purchases.view", "purchases.manage", "suppliers.manage", "customers.view",
        "customers.manage", "cash_register.use", "cash_register.manage", "reports.view",
        "reports.export", "backup.manage",
    ],
    "Cashier": [
        "dashboard.view", "pos.use", "sales.view", "returns.create",
        "products.view", "customers.view", "customers.manage",
        "cash_register.use",
    ],
    "Inventory Staff": [
        "dashboard.view", "products.view", "products.manage", "inventory.view",
        "inventory.manage", "purchases.view", "purchases.manage", "suppliers.manage",
        "reports.view", "reports.export",
    ],
}


def role_permissions(role: str) -> list[str]:
    return list(ROLE_PERMISSIONS.get(role, []))


def has_permission(user: dict | None, permission: str) -> bool:
    if not user:
        return False
    role = user.get("role", "")
    return permission in ROLE_PERMISSIONS.get(role, [])