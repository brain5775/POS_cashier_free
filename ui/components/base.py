"""Base UI components."""

from __future__ import annotations

import tkinter.ttk as ttk

import customtkinter as ctk

from ui.theme import CARD, FONT_FAMILY, FONT_SIZE, MUTED, PRIMARY, TEXT


_STYLE_CONFIGURED = False


def configure_tree_styles():
    global _STYLE_CONFIGURED
    if _STYLE_CONFIGURED:
        return
    style = ttk.Style()
    try:
        style.theme_use("default")
    except Exception:
        pass
    style.configure("Premium.Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD, rowheight=28, font=(FONT_FAMILY, FONT_SIZE - 1))
    style.configure("Premium.Treeview.Heading", background=PRIMARY, foreground="#FFFFFF", font=(FONT_FAMILY, FONT_SIZE - 1, "bold"), relief="flat")
    style.map("Premium.Treeview", background=[("selected", PRIMARY)], foreground=[("selected", "#FFFFFF")])
    style.map("Premium.Treeview.Heading", background=[("active", "#1E40AF")])
    _STYLE_CONFIGURED = True


class BasePage(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str = ""):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=title, font=(FONT_FAMILY, 22, "bold"), text_color=TEXT, anchor="w").grid(row=0, column=0, sticky="w")
        if subtitle:
            ctk.CTkLabel(header, text=subtitle, font=(FONT_FAMILY, FONT_SIZE), text_color=MUTED, anchor="w", wraplength=900).grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)

    def set_status(self, text: str) -> None:
        pass


class DataTable(ctk.CTkFrame):
    def __init__(self, master, columns: list[tuple[str, str, int]]):
        super().__init__(master, fg_color=CARD, corner_radius=8)
        configure_tree_styles()
        self.columns = columns
        self.column_ids = [c[0] for c in columns]
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(self, columns=self.column_ids, show="headings", height=14, style="Premium.Treeview")
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        self.vsb.grid(row=0, column=1, sticky="ns", pady=(8, 0))
        self.hsb.grid(row=1, column=0, sticky="ew", padx=(8, 0))
        for cid, title, width in columns:
            self.tree.heading(cid, text=title)
            self.tree.column(cid, width=width, minwidth=max(60, min(width, 90)), anchor="w")
        self.tree.bind("<Double-1>", lambda e: None)

    def set_rows(self, rows: list[dict], id_column: str | None = None) -> None:
        for child in self.tree.get_children():
            self.tree.delete(child)
        for row in rows:
            values = [row.get(cid, "") for cid in self.column_ids]
            iid = row.get(id_column, "") if id_column else ""
            if iid:
                self.tree.insert("", "end", iid=str(iid), values=values)
            else:
                self.tree.insert("", "end", values=values)
        # zebra striping for readability
        for index, iid in enumerate(self.tree.get_children()):
            self.tree.item(iid, tags=("odd" if index % 2 else "even",))
        self.tree.tag_configure("even", background=CARD)
        self.tree.tag_configure("odd", background="#F1F5F9")

    def selected_id(self, id_column_index: int = 0) -> str | None:
        selection = self.tree.selection()
        if not selection:
            return None
        item = self.tree.item(selection[0])
        if item["values"]:
            return item["values"][id_column_index]
        return None

    def selected_iid(self) -> str | None:
        selection = self.tree.selection()
        return selection[0] if selection else None