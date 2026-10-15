"""Backup and restore page."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.base import BasePage, DataTable
from ui.components.dialogs import confirm, info
from ui.theme import FONT_FAMILY, FONT_SIZE, MUTED


class BackupPage(BasePage):
    def __init__(self, master, app):
        super().__init__(master, "Backup / Restore", "Data snapshots and recovery")
        self.app = app
        self._build()

    def _build(self):
        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(toolbar, text="Create Backup", height=34, command=self.create_backup).pack(side="left", padx=(0, 6))
        ctk.CTkButton(toolbar, text="Validate", height=34, command=self.validate).pack(side="left", padx=6)
        ctk.CTkButton(toolbar, text="Restore", height=34, fg_color="#DC2626", hover_color="#B91C1C", command=self.restore).pack(side="left", padx=6)
        ctk.CTkButton(toolbar, text="Refresh", height=34, fg_color="#64748B", hover_color="#475569", command=self.refresh).pack(side="left", padx=6)
        self.table = DataTable(self.body, [("name", "Backup", 360), ("created", "Status", 120)])
        self.table.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(1, weight=1)
        self.refresh()

    def _backup_paths(self):
        return sorted(self.app.context["backup"].backup_dir.glob("backup_*"), reverse=True)

    def refresh(self):
        rows = [{"name": p.name, "created": "available"} for p in self._backup_paths()]
        self.table.set_rows(rows)

    def selected_path(self):
        sel = self.table.selected_iid()
        if not sel:
            return None
        name = self.table.tree.item(sel)["values"][0]
        return self.app.context["backup"].backup_dir / str(name)

    def create_backup(self):
        try:
            path = self.app.context["backup"].create_backup("manual")
            info(self.app, "Backup", f"Created {path.name}")
            self.refresh()
        except Exception as exc:
            info(self.app, "Error", str(exc))

    def validate(self):
        path = self.selected_path()
        if not path:
            return
        ok, msg = self.app.context["backup"].validate(path)
        info(self.app, "Validation", msg)

    def restore(self):
        path = self.selected_path()
        if not path:
            return
        if not confirm(self.app, "Restore", "Restore this backup? Current data will be backed up first."):
            return
        try:
            safety = self.app.context["backup"].restore(path)
            info(self.app, "Restored", f"Safety backup: {safety.name}")
            self.refresh()
        except Exception as exc:
            info(self.app, "Error", str(exc))