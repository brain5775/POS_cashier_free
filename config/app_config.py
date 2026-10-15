"""Application-wide configuration and path resolution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SETTINGS = {
    "business_name": "Rey Retail",
    "business_address": "",
    "business_phone": "",
    "business_email": "",
    "currency": "IDR",
    "tax_rate": "0.00",
    "tax_mode": "exclusive",  # exclusive or inclusive
    "receipt_header": "Thank you for shopping with us.",
    "receipt_footer": "Powered by Integrated POS",
    "theme": "light",
    "language": "en",
    "default_low_stock": "5",
    "allow_negative_stock": "false",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "number_format": "#,##0.00",
}


@dataclass
class AppConfig:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DEFAULT_DATA_DIR
    backup_dir: Path | None = None
    log_dir: Path | None = None

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir).resolve()
        self.backup_dir = Path(self.backup_dir).resolve() if self.backup_dir else (self.project_root / "backups").resolve()
        self.log_dir = Path(self.log_dir).resolve() if self.log_dir else (self.project_root / "logs").resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def settings_path(self) -> Path:
        return self.data_dir / "settings.csv"


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from a small JSON file, falling back to defaults."""
    config_path = config_path or (PROJECT_ROOT / "config" / "app.json")
    if config_path.exists():
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
            return AppConfig(
                project_root=PROJECT_ROOT,
                data_dir=Path(payload.get("data_dir", DEFAULT_DATA_DIR)),
                backup_dir=Path(payload.get("backup_dir")) if payload.get("backup_dir") else None,
                log_dir=Path(payload.get("log_dir")) if payload.get("log_dir") else None,
            )
        except (OSError, ValueError, TypeError):
            pass
    return AppConfig()