"""Transaction journal coordinator."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.ids import new_id
from storage.csv_manager import CsvStore


class TransactionManager:
    def __init__(self, store: CsvStore):
        self.store = store

    def begin(self, operation: str, payload: dict[str, Any] | None = None) -> str:
        transaction_id = new_id("txn")
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        self.store.append("transaction_journal.csv", {
            "transaction_id": transaction_id,
            "operation": operation,
            "status": "started",
            "payload": json.dumps(payload or {}, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
            "completed_at": "",
            "error": "",
        })
        return transaction_id

    def set_status(self, transaction_id: str, status: str, error: str = "") -> None:
        rows = self.store.read("transaction_journal.csv")
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        for row in rows:
            if row["transaction_id"] == transaction_id:
                row["status"] = status
                row["updated_at"] = now
                row["error"] = error
                if status == "completed":
                    row["completed_at"] = now
                break
        self.store.write("transaction_journal.csv", rows)

    def complete(self, transaction_id: str) -> None:
        self.set_status(transaction_id, "completed")

    def fail(self, transaction_id: str, error: str) -> None:
        self.set_status(transaction_id, "failed", error)

    def get(self, transaction_id: str) -> dict[str, str] | None:
        for row in self.store.read("transaction_journal.csv"):
            if row["transaction_id"] == transaction_id:
                return row
        return None

    def pending(self) -> list[dict[str, str]]:
        return [row for row in self.store.read("transaction_journal.csv") if row["status"] not in ("completed", "failed")]

    def payload(self, transaction_id: str) -> dict[str, Any]:
        row = self.get(transaction_id)
        if not row:
            return {}
        try:
            return json.loads(row.get("payload", "") or "{}")
        except json.JSONDecodeError:
            return {}