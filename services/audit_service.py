"""Audit logging service."""

from __future__ import annotations

from datetime import datetime

from core.ids import new_id
from storage.csv_manager import CsvStore


class AuditService:
    def __init__(self, store: CsvStore):
        self.store = store

    def log(self, user_id: str, action: str, entity_type: str = "", entity_id: str = "", details: str = "") -> None:
        self.store.append("audit_logs.csv", {
            "audit_id": new_id("aud"),
            "user_id": user_id or "",
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        })