from ui.pages.backup import BackupPage
from ui.pages.cash_register import CashRegisterPage
from ui.pages.categories import CategoriesPage
from ui.pages.customers import CustomersPage
from ui.pages.dashboard import DashboardPage
from ui.pages.inventory import InventoryPage, StockMovementsPage
from ui.pages.pos import POSPage
from ui.pages.products import ProductsPage
from ui.pages.purchasing import PurchasingPage
from ui.pages.reports import ReportsPage
from ui.pages.returns import ReturnsPage
from ui.pages.sales import SalesHistoryPage
from ui.pages.settings import SettingsPage
from ui.pages.suppliers import SuppliersPage
from ui.pages.users import UsersPage

PAGE_FACTORIES = {
    "dashboard": lambda parent, app: DashboardPage(parent, app),
    "pos": lambda parent, app: POSPage(parent, app),
    "products": lambda parent, app: ProductsPage(parent, app),
    "categories": lambda parent, app: CategoriesPage(parent, app),
    "inventory": lambda parent, app: InventoryPage(parent, app),
    "stock_movements": lambda parent, app: StockMovementsPage(parent, app),
    "sales": lambda parent, app: SalesHistoryPage(parent, app),
    "returns": lambda parent, app: ReturnsPage(parent, app),
    "purchasing": lambda parent, app: PurchasingPage(parent, app),
    "suppliers": lambda parent, app: SuppliersPage(parent, app),
    "customers": lambda parent, app: CustomersPage(parent, app),
    "cash_register": lambda parent, app: CashRegisterPage(parent, app),
    "reports": lambda parent, app: ReportsPage(parent, app),
    "users": lambda parent, app: UsersPage(parent, app),
    "settings": lambda parent, app: SettingsPage(parent, app),
    "backup": lambda parent, app: BackupPage(parent, app),
}