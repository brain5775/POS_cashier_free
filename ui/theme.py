"""UI theme constants for the premium POS desktop interface."""

from __future__ import annotations

APP_NAME = "Integrated POS"
FONT_FAMILY = "Segoe UI"

# Colors
PRIMARY = "#1D4ED8"
PRIMARY_HOVER = "#1E40AF"
SECONDARY = "#475569"
SIDEBAR = "#0F172A"
SIDEBAR_HOVER = "#1E293B"
SIDEBAR_TEXT = "#CBD5E1"
BACKGROUND = "#F5F7FB"
CARD = "#FFFFFF"
TEXT = "#111827"
MUTED = "#64748B"
BORDER = "#E2E8F0"
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
INFO = "#0EA5E9"

# Typography
FONT_SIZE = 13
FONT_SMALL = 11
FONT_TITLE = 22
FONT_SECTION = 16
FONT_METRIC = 24

# Spacing and shape
RADIUS = 8
SPACING = 8
PAGE_MARGIN = 24
BUTTON_HEIGHT = 34
INPUT_HEIGHT = 34
CARD_PADDING = 16

SIDEBAR_WIDTH = 212
SIDEBAR_COLLAPSED = 72

SIDEBAR_ITEMS = [
    ("dashboard", "Dashboard"),
    ("pos", "Cashier / POS"),
    ("products", "Products"),
    ("categories", "Categories"),
    ("inventory", "Inventory"),
    ("stock_movements", "Stock Movements"),
    ("sales", "Sales History"),
    ("returns", "Returns / Refunds"),
    ("purchasing", "Purchasing"),
    ("suppliers", "Suppliers"),
    ("customers", "Customers"),
    ("cash_register", "Cash Register"),
    ("reports", "Reports"),
    ("users", "User Management"),
    ("settings", "Settings"),
    ("backup", "Backup / Restore"),
]