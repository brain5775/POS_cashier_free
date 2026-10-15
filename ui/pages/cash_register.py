"""Cash register page."""

from __future__ import annotations

from decimal import Decimal

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class CashRegisterPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Cash Register", "Shifts and cash movements")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for text, command in [("Open Shift", self.open_shift), ("Cash In", lambda: self.move("cash_in")), ("Cash Out", lambda: self.move("cash_out")), ("Close Shift", self.close_shift)]:
            ctk.CTkButton(toolbar, text=text, height=34, command=command).pack(side="left", padx=(0, 6))
        ctk.CTkButton(toolbar, text="Refresh", height=34, fg_color="#64748B", hover_color="#475569", command=self.refresh).pack(side="left")
        self.status_label = ctk.CTkLabel(self.body, text="No open shift", font=(FONT_FAMILY, FONT_SIZE), text_color=MUTED)
        self.status_label.grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.table = DataTable(self.body, [("movement_type", "Type", 110), ("amount", "Amount", 100), ("reason", "Reason", 300), ("created_at", "Time", 180)])
        self.table.grid(row=2, column=0, sticky="nsew")
        self.body.grid_rowconfigure(2, weight=1)
        self.refresh()

    def refresh(self):
        shift = None
        if self.app.current_user:
            shift = self.app.context["cash"].current_shift(self.app.current_user["user_id"])
        self.app.current_shift = shift
        if shift:
            self.status_label.configure(text=f"Open shift: {shift['shift_id']} | expected {shift['expected_cash']}")
            rows = [m for m in self.app.context["cash"].movements.all() if m.get("shift_id") == shift["shift_id"]]
        else:
            self.status_label.configure(text="No open shift")
            rows = []
        self.table.set_rows(rows, id_column="cash_movement_id")

    def _dialog(self, title, width=360):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(title)
        dialog.transient(self.app)
        dialog.grab_set()
        dialog.geometry(f"{width}x240")
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        return dialog, frame

    def open_shift(self):
        dialog, frame = self._dialog("Open Shift", 320)
        amt = ctk.CTkEntry(frame, height=34, placeholder_text="Opening cash")
        amt.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        def save():
            try:
                shift = self.app.context["cash"].open_shift(self.app.current_user, amt.get() or "0")
                self.app.current_shift = shift
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Open", height=34, command=save).grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def move(self, movement_type):
        shift = self.app.current_shift or (self.app.context["cash"].current_shift(self.app.current_user["user_id"]) if self.app.current_user else None)
        if not shift:
            info(self.app, "No shift", "Open a shift first.")
            return
        dialog, frame = self._dialog("Cash Movement", 340)
        amt = ctk.CTkEntry(frame, height=34, placeholder_text="Amount")
        amt.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        reason = ctk.CTkEntry(frame, height=34, placeholder_text="Reason (required)")
        reason.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        def save():
            try:
                self.app.context["cash"].add_movement(shift["shift_id"], self.app.current_user, movement_type, amt.get(), reason.get())
                dialog.destroy()
                self.refresh()
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Save", height=34, command=save).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def close_shift(self):
        shift = self.app.current_shift or (self.app.context["cash"].current_shift(self.app.current_user["user_id"]) if self.app.current_user else None)
        if not shift:
            return
        dialog, frame = self._dialog("Close Shift", 340)
        amt = ctk.CTkEntry(frame, height=34, placeholder_text="Actual cash")
        amt.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        notes = ctk.CTkEntry(frame, height=34, placeholder_text="Notes")
        notes.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        def save():
            try:
                self.app.context["cash"].close_shift(self.app.current_user, shift["shift_id"], amt.get() or "0", notes.get())
                self.app.current_shift = None
                dialog.destroy()
                self.refresh()
                info(self.app, "Shift closed", "Shift reconciled.")
            except Exception as exc:
                info(self.app, "Error", str(exc))
        ctk.CTkButton(frame, text="Close", height=34, command=save).grid(row=2, column=0, sticky="ew", pady=(8, 0))