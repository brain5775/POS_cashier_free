"""User management page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class UsersPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "User Management", "Manage accounts and roles")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(toolbar, text="Add User", height=34, command=self.add_user).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(toolbar, text="Deactivate", height=34, fg_color="#DC2626", hover_color="#B91C1C", command=self.deactivate_user).grid(row=0, column=1, padx=4)
        ctk.CTkButton(toolbar, text="Refresh", height=34, fg_color="#64748B", hover_color="#475569", command=self.refresh).grid(row=0, column=2, padx=4)
        self.table = DataTable(self.body, [("username", "Username", 150), ("full_name", "Name", 190), ("role", "Role", 130), ("is_active", "Active", 80), ("last_login_at", "Last Login", 180)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self):
        rows = self.app.context["auth"].users.all()
        self.table.set_rows(rows, id_column="user_id")

    def add_user(self):
        self.app.context["auth"].seed_roles()
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add User")
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry("440x360")
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="Username", font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=0, column=0, sticky="w", pady=(0, 2))
        username = ctk.CTkEntry(frame, height=34)
        username.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(frame, text="Full name", font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=2, column=0, sticky="w", pady=(0, 2))
        full_name = ctk.CTkEntry(frame, height=34)
        full_name.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(frame, text="Role", font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=4, column=0, sticky="w", pady=(0, 2))
        role = ctk.CTkComboBox(frame, height=34, values=["Administrator", "Manager", "Cashier", "Inventory Staff"])
        role.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(frame, text="Password", font=(FONT_FAMILY, FONT_SIZE - 1), text_color=MUTED).grid(row=6, column=0, sticky="w", pady=(0, 2))
        password = ctk.CTkEntry(frame, height=34, show="*")
        password.grid(row=7, column=0, sticky="ew", pady=(0, 8))
        def save():
            try:
                self.app.context["auth"].create_user(self.app.current_user, username.get(), full_name.get(), role.get(), password.get(), True)
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Save", height=34, command=save).grid(row=8, column=0, sticky="ew", pady=(8, 0))

    def deactivate_user(self):
        uid = self.table.selected_iid()
        if not uid:
            return
        try:
            self.app.context["auth"].set_active(self.app.current_user, uid, False)
            self.refresh()
        except Exception as exc:
            info(self.app, "Error", str(exc))