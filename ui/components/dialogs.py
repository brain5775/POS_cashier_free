"""Dialog helpers."""

from __future__ import annotations

import customtkinter as ctk

from ui.theme import FONT_FAMILY, FONT_SIZE


def _place(dialog, width, height):
    dialog.update_idletasks()
    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()
    width = min(width, screen_w - 40)
    height = min(height, screen_h - 60)
    x = max(10, (screen_w - width) // 2)
    y = max(10, (screen_h - height) // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")
    dialog.minsize(min(320, width), min(160, height))


def info(master, title: str, message: str) -> None:
    dialog = ctk.CTkToplevel(master)
    dialog.title(title)
    _place(dialog, 440, 180)
    dialog.resizable(True, True)
    frame = ctk.CTkFrame(dialog, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    ctk.CTkLabel(frame, text=message, wraplength=380, font=(FONT_FAMILY, FONT_SIZE), anchor="w", justify="left").pack(fill="both", expand=True)
    ctk.CTkButton(frame, text="OK", width=100, command=dialog.destroy).pack(pady=(12, 0))
    dialog.transient(master)
    dialog.grab_set()
    master.wait_window(dialog)


def confirm(master, title: str, message: str) -> bool:
    result = {"value": False}

    def yes():
        result["value"] = True
        dialog.destroy()

    dialog = ctk.CTkToplevel(master)
    dialog.title(title)
    _place(dialog, 460, 190)
    dialog.resizable(True, True)
    frame = ctk.CTkFrame(dialog, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    ctk.CTkLabel(frame, text=message, wraplength=400, font=(FONT_FAMILY, FONT_SIZE), anchor="w", justify="left").pack(fill="both", expand=True)
    buttons = ctk.CTkFrame(frame, fg_color="transparent")
    buttons.pack(pady=(12, 0))
    ctk.CTkButton(buttons, text="Yes", width=100, command=yes).pack(side="left", padx=6)
    ctk.CTkButton(buttons, text="No", width=100, fg_color="#64748B", hover_color="#475569", command=dialog.destroy).pack(side="left", padx=6)
    dialog.transient(master)
    dialog.grab_set()
    master.wait_window(dialog)
    return result["value"]