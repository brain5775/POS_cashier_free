"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import customtkinter as ctk

from config.app_config import DEFAULT_SETTINGS, load_config
from core.logging_config import setup_logging
from services.audit_service import AuditService
from services.auth_service import AuthService
from services.cash_register_service import CashRegisterService
from services.checkout_service import CheckoutService
from services.customer_service import CustomerService
from services.inventory_service import InventoryService
from services.product_service import ProductService
from services.purchase_service import PurchaseService
from services.return_service import ReturnService
from services.sales_service import SalesService
from services.settings_service import SettingsService
from services.supplier_service import SupplierService
from storage.backup_manager import BackupManager
from storage.csv_manager import CsvStore
from storage.transaction_manager import TransactionManager
from ui.app import POSApplication


def main():
    config = load_config()
    logger = setup_logging(config.log_dir)
    logger.info("Starting Integrated POS")
    store = CsvStore(config.data_dir)
    txn = TransactionManager(store)
    audit = AuditService(store)
    auth = AuthService(store, audit)
    auth.seed_roles()
    auth.ensure_first_admin()
    settings = SettingsService(store, DEFAULT_SETTINGS)
    inventory = InventoryService(store, settings, audit)
    products = ProductService(store, audit)
    customers = CustomerService(store, audit)
    suppliers = SupplierService(store, audit)
    cash = CashRegisterService(store, audit)
    purchases = PurchaseService(store, products, inventory, audit)
    sales = SalesService(store, inventory, audit)
    returns = ReturnService(store, inventory, cash, customers, audit, sales)
    checkout = CheckoutService(store, txn, products, inventory, customers, settings, cash, audit)
    backup = BackupManager(config.data_dir, config.backup_dir)
    context = {
        "config": config,
        "store": store,
        "logger": logger,
        "transaction_manager": txn,
        "audit": audit,
        "auth": auth,
        "settings": settings,
        "products": products,
        "inventory": inventory,
        "customers": customers,
        "suppliers": suppliers,
        "cash": cash,
        "purchases": purchases,
        "sales": sales,
        "returns": returns,
        "checkout": checkout,
        "backup": backup,
    }
    # recovery pending transactions (best effort)
    try:
        for row in txn.pending():
            logger.warning("Pending transaction found: %s", row["transaction_id"])
    except Exception as exc:
        logger.exception("Recovery scan failed: %s", exc)

    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme(str(PROJECT_ROOT / "assets" / "themes" / "premium.json"))
    app = POSApplication(context)
    app.mainloop()


if __name__ == "__main__":
    main()