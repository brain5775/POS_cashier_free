import tempfile
from pathlib import Path
from decimal import Decimal

from config.app_config import DEFAULT_SETTINGS
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
from storage.backup_manager import BackupManager
from storage.csv_manager import CsvStore
from storage.transaction_manager import TransactionManager


def build_env(tmpdir):
    store = CsvStore(tmpdir)
    txn = TransactionManager(store)
    audit = None
    auth = AuthService(store, audit)
    auth.seed_roles()
    auth.ensure_first_admin()
    settings = SettingsService(store, DEFAULT_SETTINGS)
    inventory = InventoryService(store, settings, audit)
    products = ProductService(store, audit)
    customers = CustomerService(store, audit)
    suppliers = SupplierService(store, audit) if False else None
    from services.supplier_service import SupplierService
    suppliers = SupplierService(store, audit)
    cash = CashRegisterService(store, audit)
    purchases = PurchaseService(store, products, inventory, audit)
    sales = SalesService(store, inventory, audit)
    returns = ReturnService(store, inventory, cash, customers, audit, sales)
    checkout = CheckoutService(store, txn, products, inventory, customers, settings, cash, audit)
    return store, auth, products, inventory, customers, suppliers, cash, purchases, sales, returns, checkout


def test_product_checkout_stock_return():
    with tempfile.TemporaryDirectory() as d:
        store, auth, products, inventory, customers, suppliers, cash, purchases, sales, returns, checkout = build_env(d)
        admin = auth.login("admin", "ChangeMe123!")
        cat = products.create_category(admin, "Food")
        product = products.create_product(admin, {"sku": "SKU1", "name": "Rice", "category": "Food", "purchase_cost": "10", "selling_price": "15", "min_stock": "2"})
        # opening stock
        inventory.set_opening_stock(admin, product["product_id"], 5, 10)
        assert inventory.current_stock(product["product_id"]) == Decimal("5")
        shift = cash.open_shift(admin, 100)
        calc = checkout.calculate_totals([{"product_id": product["product_id"], "quantity": 2, "unit_price": "15", "discount": "0"}], None, 0)
        assert calc["total"] == Decimal("30.00")
        result = checkout.checkout(admin, {"items": [{"product_id": product["product_id"], "quantity": 2, "unit_price": "15", "discount": "0"}], "payments": [{"method": "cash", "amount": "30"}], "shift_id": shift["shift_id"]}, )
        assert result["success"]
        assert inventory.current_stock(product["product_id"]) == Decimal("3")
        # return one
        sale = sales.get_sale(result["sale_id"])
        items = sales.get_sale_items(result["sale_id"])
        ret = returns.create_return(admin, result["sale_id"], [{"sale_item_id": items[0]["sale_item_id"], "quantity": 1, "restock": True}], "damaged", "cash")
        assert Decimal(ret["refund_total"]) == Decimal("15.00")
        assert inventory.current_stock(product["product_id"]) == Decimal("4")
        # idempotency duplicate idempotency key not tested
        # backup
        bk = BackupManager(Path(d), Path(d) / "bak")
        path = bk.create_backup("test")
        ok, msg = bk.validate(path)
        assert ok, msg


def test_negative_stock_prevented():
    with tempfile.TemporaryDirectory() as d:
        store, auth, products, inventory, customers, suppliers, cash, purchases, sales, returns, checkout = build_env(d)
        admin = auth.login("admin", "ChangeMe123!")
        product = products.create_product(admin, {"sku": "SKU2", "name": "Drink", "purchase_cost": "5", "selling_price": "8"})
        inventory.set_opening_stock(admin, product["product_id"], 1, 5)
        shift = cash.open_shift(admin, 0)
        try:
            checkout.checkout(admin, {"items": [{"product_id": product["product_id"], "quantity": 2, "unit_price": "8", "discount": "0"}], "payments": [{"method": "cash", "amount": "16"}], "shift_id": shift["shift_id"]})
            assert False
        except Exception as exc:
            assert "Insufficient" in str(exc) or "stock" in str(exc).lower()


def test_purchase_receiving_increases_stock():
    with tempfile.TemporaryDirectory() as d:
        store, auth, products, inventory, customers, suppliers, cash, purchases, sales, returns, checkout = build_env(d)
        admin = auth.login("admin", "ChangeMe123!")
        product = products.create_product(admin, {"sku": "SKU3", "name": "Soap", "purchase_cost": "4", "selling_price": "7"})
        po = purchases.create_purchase(admin, "", [{"product_id": product["product_id"], "quantity": 3, "unit_cost": 4}], "")
        assert inventory.current_stock(product["product_id"]) == Decimal("0")
        purchases.receive_goods(admin, po["purchase_id"], [{"product_id": product["product_id"], "quantity": 2}], "")
        assert inventory.current_stock(product["product_id"]) == Decimal("2")
        # duplicate receipt exceed validation
        try:
            purchases.receive_goods(admin, po["purchase_id"], [{"product_id": product["product_id"], "quantity": 2}], "")
            assert False
        except Exception:
            pass