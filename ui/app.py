"""Main application window."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ui.components.dialogs import info
from ui.theme import APP_NAME, FONT_FAMILY, FONT_SIZE, SIDEBAR, SIDEBAR_ITEMS, SIDEBAR_TEXT


class POSApplication(ctk.CTk):
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.title(APP_NAME)
        self.geometry("1366x768")
        self.minsize(960, 640)
        self.current_user = None
        self.current_shift = None
        self.pages = {}
        self._build_shell()
        from ui.dialogs.login import LoginDialog
        self.login_dialog = LoginDialog(self, context["auth"], self.on_login)

    def _build_shell(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar, text="Integrated POS", font=(FONT_FAMILY, 18, "bold"), text_color="white").pack(padx=16, pady=(18, 18), anchor="w")
        self.nav_buttons = {}
        self.active_nav_key = None
        for key, label in SIDEBAR_ITEMS:
            btn = ctk.CTkButton(self.sidebar, text=label, anchor="w", height=34, corner_radius=6, fg_color="transparent", hover_color="#1F2937", text_color=SIDEBAR_TEXT, command=lambda k=key: self.navigate(k))
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(right, height=58, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        self.header_title = ctk.CTkLabel(header, text="Dashboard", font=(FONT_FAMILY, 18, "bold"))
        self.header_title.grid(row=0, column=0, sticky="w", padx=20, pady=16)
        self.user_label = ctk.CTkLabel(header, text="Not logged in", font=(FONT_FAMILY, FONT_SIZE))
        self.user_label.grid(row=0, column=1, sticky="e", padx=20)
        self.logout_btn = ctk.CTkButton(header, text="Logout", width=90, command=self.logout)
        self.logout_btn.grid(row=0, column=2, padx=(0, 20))

        self.content = ctk.CTkFrame(right, fg_color="#f3f4f6")
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.status_bar = ctk.CTkLabel(right, text="Ready", anchor="w", font=(FONT_FAMILY, 11), text_color="#64748B")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=4)
        self.after(100, self._safe_zoom)

    def on_login(self, user):
        self.current_user = user
        self.user_label.configure(text=f"{user.get('full_name') or user.get('username')} ({user.get('role')})")
        self.navigate("dashboard")

    def logout(self):
        self.current_user = None
        self.current_shift = None
        self.user_label.configure(text="Not logged in")
        for child in self.content.winfo_children():
            child.destroy()
        self.pages.clear()
        from ui.dialogs.login import LoginDialog
        self.login_dialog = LoginDialog(self, self.context["auth"], self.on_login)

    def set_status(self, text: str):
        self.status_bar.configure(text=text)

    def navigate(self, key: str):
        if self.current_user is None:
            return
        from ui.pages import PAGE_FACTORIES
        if key not in PAGE_FACTORIES:
            from ui.components.dialogs import info
            info(self, "Navigation", f"Page not implemented: {key}")
            return
        if self.content.winfo_children():
            for child in self.content.winfo_children():
                child.destroy()
        page = PAGE_FACTORIES[key](self.content, self)
        page.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        from ui.theme import SIDEBAR_ITEMS
        title = dict(SIDEBAR_ITEMS).get(key, key)
        self.header_title.configure(text=title)
        for nav_key, button in self.nav_buttons.items():
            if nav_key == key:
                button.configure(fg_color="#1E40AF", text_color="#FFFFFF", hover_color="#1E3A8A")
            else:
                button.configure(fg_color="transparent", text_color=SIDEBAR_TEXT, hover_color="#1F2937")
        self.set_status(f"Opened {title}")

    def _safe_zoom(self):
        try:
            self.state("zoomed")
        except Exception:
            pass