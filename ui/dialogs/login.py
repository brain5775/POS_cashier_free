"""Login dialog."""

from __future__ import annotations

import customtkinter as ctk

from ui.theme import CARD, FONT_FAMILY, FONT_SIZE, PRIMARY, SIDEBAR


class LoginDialog(ctk.CTkToplevel):
    def __init__(self, master, auth_service, on_success):
        super().__init__(master)
        self.auth_service = auth_service
        self.on_success = on_success
        self.title("Login")
        size_w, size_h = 400, 380
        x = (self.winfo_screenwidth() - size_w) // 2
        y = (self.winfo_screenheight() - size_h) // 2
        self.geometry(f"{size_w}x{size_h}+{x}+{y}")
        self.minsize(360, 360)
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()

        frame = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=24, pady=24)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="Integrated POS", font=(FONT_FAMILY, 24, "bold"), text_color=PRIMARY).grid(row=0, column=0, pady=(24, 4))
        ctk.CTkLabel(frame, text="Sign in to continue", font=(FONT_FAMILY, FONT_SIZE), text_color="#64748B").grid(row=1, column=0, pady=(0, 18))
        self.username = ctk.CTkEntry(frame, height=36, placeholder_text="Username")
        self.username.grid(row=2, column=0, sticky="ew", pady=6)
        self.password = ctk.CTkEntry(frame, height=36, placeholder_text="Password", show="*")
        self.password.grid(row=3, column=0, sticky="ew", pady=6)
        self.password.bind("<Return>", lambda e: self.submit())
        self.error = ctk.CTkLabel(frame, text="", text_color="#DC2626", font=(FONT_FAMILY, FONT_SIZE - 1), wraplength=300)
        self.error.grid(row=4, column=0, sticky="w", pady=(8, 4))
        ctk.CTkButton(frame, text="Login", height=38, fg_color=SIDEBAR, hover_color="#1E293B", command=self.submit).grid(row=5, column=0, sticky="ew", pady=(12, 24))

    def submit(self):
        try:
            user = self.auth_service.login(self.username.get(), self.password.get())
        except Exception as exc:
            self.error.configure(text=str(exc))
            return
        self.destroy()
        self.on_success(user)