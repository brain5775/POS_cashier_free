"""CSV persistence utilities."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Any

from config.app_config import AppConfig
from storage.csv_schemas import SCHEMAS
from storage.file_lock import LockManager


class CsvStore:
    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.lock_manager = LockManager(self.data_dir)
        self.ensure_files()

    def ensure_files(self) -> None:
        for filename, headers in SCHEMAS.items():
            path = self.data_dir / filename
            if not path.exists():
                with path.open("w", encoding="utf-8", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=headers)
                    writer.writeheader()

    def path(self, filename: str) -> Path:
        return self.data_dir / filename

    def headers(self, filename: str) -> list[str]:
        return list(SCHEMAS[filename])

    def read(self, filename: str) -> list[dict[str, str]]:
        path = self.path(filename)
        if not path.exists():
            self.ensure_files()
        with self.lock_manager:
            with path.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                if reader.fieldnames != SCHEMAS[filename]:
                    missing = [h for h in SCHEMAS[filename] if h not in (reader.fieldnames or [])]
                    extra = [h for h in (reader.fieldnames or []) if h not in SCHEMAS[filename]]
                    if missing or extra:
                        raise ValueError(f"Schema mismatch in {filename}: missing={missing}, extra={extra}")
                return [self._normalize(filename, row) for row in reader]

    def write(self, filename: str, rows: list[dict[str, Any]]) -> None:
        headers = SCHEMAS[filename]
        path = self.path(filename)
        with self.lock_manager:
            fd, temp_name = tempfile.mkstemp(prefix=f".{filename}.", suffix=".tmp", dir=str(self.data_dir))
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=headers, extrasaction="ignore")
                    writer.writeheader()
                    for row in rows:
                        writer.writerow({header: self._serialize(row.get(header, "")) for header in headers})
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(temp_name, path)
            finally:
                if os.path.exists(temp_name):
                    os.remove(temp_name)

    def append(self, filename: str, row: dict[str, Any]) -> None:
        rows = self.read(filename)
        rows.append(row)
        self.write(filename, rows)

    @staticmethod
    def _normalize(filename: str, row: dict[str, str | None]) -> dict[str, str]:
        return {header: ("" if row.get(header) is None else str(row[header])) for header in SCHEMAS[filename]}

    @staticmethod
    def _serialize(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)


class Repository:
    def __init__(self, store: CsvStore, filename: str, id_field: str):
        self.store = store
        self.filename = filename
        self.id_field = id_field

    def all(self) -> list[dict[str, str]]:
        return self.store.read(self.filename)

    def get(self, record_id: str) -> dict[str, str] | None:
        for row in self.all():
            if row.get(self.id_field) == record_id:
                return row
        return None

    def find(self, predicate) -> list[dict[str, str]]:
        return [row for row in self.all() if predicate(row)]

    def one(self, predicate) -> dict[str, str] | None:
        for row in self.all():
            if predicate(row):
                return row
        return None

    def insert(self, row: dict[str, Any]) -> None:
        rows = self.all()
        rows.append(row)
        self.store.write(self.filename, rows)

    def update(self, record_id: str, patch: dict[str, Any]) -> bool:
        rows = self.all()
        changed = False
        for row in rows:
            if row.get(self.id_field) == record_id:
                row.update(patch)
                changed = True
                break
        if changed:
            self.store.write(self.filename, rows)
        return changed

    def delete_physical(self, record_id: str) -> bool:
        rows = self.all()
        new_rows = [row for row in rows if row.get(self.id_field) != record_id]
        if len(new_rows) == len(rows):
            return False
        self.store.write(self.filename, new_rows)
        return True

    def replace_all(self, rows: list[dict[str, Any]]) -> None:
        self.store.write(self.filename, rows)