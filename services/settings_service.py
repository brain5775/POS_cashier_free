"""Settings management backed by settings.csv."""

from __future__ import annotations

from core.validation import iso_now, optional_text
from storage.csv_manager import CsvStore, Repository


class SettingsService:
    DEFAULTS = {}

    def __init__(self, store: CsvStore, defaults: dict | None = None):
        self.store = store
        self.settings = Repository(store, "settings.csv", "setting_key")
        self.defaults = defaults or {}
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        existing = {r["setting_key"]: r for r in self.settings.all()}
        now = iso_now()
        for key, value in self.defaults.items():
            if key not in existing:
                self.settings.insert({"setting_key": key, "setting_value": str(value), "updated_at": now})

    def all(self) -> dict[str, str]:
        result = dict(self.defaults)
        for row in self.settings.all():
            result[row["setting_key"]] = row["setting_value"]
        return result

    def get(self, key: str, default: str = "") -> str:
        row = self.settings.get(key)
        if row:
            return row.get("setting_value", default)
        return self.defaults.get(key, default)

    def set(self, key: str, value, actor=None) -> None:
        now = iso_now()
        existing = self.settings.get(key)
        if existing:
            self.settings.update(key, {"setting_value": str(value), "updated_at": now})
        else:
            self.settings.insert({"setting_key": key, "setting_value": str(value), "updated_at": now})

    def update_many(self, values: dict, actor=None) -> None:
        for key, value in values.items():
            self.set(key, value, actor)