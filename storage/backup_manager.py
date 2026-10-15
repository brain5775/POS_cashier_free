"""Backup and restore helpers."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:
    def __init__(self, data_dir: Path | str, backup_dir: Path | str):
        self.data_dir = Path(data_dir).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "") -> Path:
        timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        backup_path = self.backup_dir / f"backup_{timestamp}{suffix}"
        backup_path.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.data_dir.glob("*.csv")):
            shutil.copy2(path, backup_path / path.name)
        manifest = {
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "files": {p.name: self._sha256(p) for p in sorted(backup_path.glob("*.csv"))},
        }
        (backup_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return backup_path

    def validate(self, backup_path: Path | str) -> tuple[bool, str]:
        path = Path(backup_path)
        manifest_path = path / "manifest.json"
        if not manifest_path.exists():
            return False, "Missing manifest."
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False, "Invalid manifest."
        files = manifest.get("files", {})
        if not files:
            return False, "No files recorded."
        for name, checksum in files.items():
            file_path = path / name
            if not file_path.exists():
                return False, f"Missing file: {name}"
            if self._sha256(file_path) != checksum:
                return False, f"Checksum mismatch: {name}"
        return True, "Backup is valid."

    def restore(self, backup_path: Path | str) -> Path:
        path = Path(backup_path)
        ok, message = self.validate(path)
        if not ok:
            raise ValueError(message)
        safety = self.create_backup("pre_restore")
        for source in path.glob("*.csv"):
            shutil.copy2(source, self.data_dir / source.name)
        return safety

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()