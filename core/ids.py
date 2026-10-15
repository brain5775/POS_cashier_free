"""ID generation helpers."""

from __future__ import annotations

import uuid


def new_id(prefix: str = "") -> str:
    value = uuid.uuid4().hex[:12]
    return f"{prefix}{value}" if prefix else value