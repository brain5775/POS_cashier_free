"""Validation helpers."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")


def parse_decimal(value: Any, field: str = "value", allow_blank: bool = False) -> Decimal:
    if value is None or str(value).strip() == "":
        if allow_blank:
            return Decimal("0")
        raise ValueError(f"{field} is required.")
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a valid number.") from exc


def non_negative_decimal(value: Any, field: str = "value") -> Decimal:
    result = parse_decimal(value, field)
    if result < 0:
        raise ValueError(f"{field} cannot be negative.")
    return result


def parse_int(value: Any, field: str = "value") -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer.") from exc


def required_text(value: Any, field: str, min_length: int = 1) -> str:
    result = "" if value is None else str(value).strip()
    if len(result) < min_length:
        raise ValueError(f"{field} is required.")
    return result


def optional_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def valid_email(value: Any) -> bool:
    text = optional_text(value)
    return text == "" or bool(EMAIL_RE.match(text))


def valid_phone(value: Any) -> bool:
    text = optional_text(value)
    return text == "" or bool(PHONE_RE.match(text))


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_iso(value: Any) -> datetime | None:
    text = optional_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None