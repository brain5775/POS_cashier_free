"""Cash register shifts and movements."""

from __future__ import annotations

from decimal import Decimal

from core.exceptions import PermissionError, NotFoundError, ValidationError
from core.ids import new_id
from core.permissions import has_permission
from core.validation import iso_now, optional_text, required_text
from storage.csv_manager import CsvStore, Repository


class CashRegisterService:
    def __init__(self, store: CsvStore, audit=None):
        self.store = store
        self.shifts = Repository(store, "cash_register_shifts.csv", "shift_id")
        self.movements = Repository(store, "cash_movements.csv", "cash_movement_id")
        self.audit = audit

    def current_shift(self, user_id: str) -> dict | None:
        for row in self.shifts.all():
            if row.get("user_id") == user_id and row.get("status") == "open":
                return row
        return None

    def open_shift(self, actor, opening_cash: Decimal | str) -> dict:
        if actor is not None and not has_permission(actor, "cash_register.use"):
            raise PermissionError("Missing permission: cash_register.use")
        user_id = (actor or {}).get("user_id", "")
        if self.current_shift(user_id):
            raise ValidationError("A shift is already open.")
        now = iso_now()
        row = {
            "shift_id": new_id("shf"),
            "user_id": user_id,
            "opened_at": now,
            "closed_at": "",
            "opening_cash": str(Decimal(str(opening_cash))),
            "closing_cash": "",
            "expected_cash": "",
            "cash_sales": "0",
            "cash_refunds": "0",
            "cash_in": "0",
            "cash_out": "0",
            "status": "open",
            "notes": "",
        }
        self.shifts.insert(row)
        if self.audit:
            self.audit.log(user_id, "open_shift", "shift", row["shift_id"], str(opening_cash))
        return row

    def add_movement(self, shift_id: str, actor, movement_type: str, amount: Decimal | str, reason: str, reference_type: str = "", reference_id: str = "") -> dict:
        if self.shifts.get(shift_id) is None:
            raise NotFoundError("Shift not found.")
        movement_type = required_text(movement_type, "Movement type")
        reason = required_text(reason, "Reason")
        amount = Decimal(str(amount))
        row = {
            "cash_movement_id": new_id("cmv"),
            "shift_id": shift_id,
            "user_id": (actor or {}).get("user_id", ""),
            "movement_type": movement_type,
            "amount": str(amount),
            "reason": reason,
            "reference_type": reference_type or "",
            "reference_id": reference_id or "",
            "created_at": iso_now(),
        }
        self.movements.insert(row)
        self._recalculate(shift_id)
        return row

    def _recalculate(self, shift_id: str) -> None:
        shift = self.shifts.get(shift_id)
        if not shift:
            return
        sales = Decimal("0"); refunds = Decimal("0"); cash_in = Decimal("0"); cash_out = Decimal("0")
        for m in self.movements.find(lambda r: r.get("shift_id") == shift_id):
            amount = Decimal(m.get("amount") or "0")
            mtype = m.get("movement_type", "").lower()
            if mtype in ("sale", "cash_sale"):
                sales += amount
            elif mtype in ("refund", "cash_refund"):
                refunds += amount
            elif mtype in ("cash_in", "in"):
                cash_in += amount
            elif mtype in ("cash_out", "out"):
                cash_out += amount
        opening = Decimal(shift.get("opening_cash") or "0")
        expected = opening + sales - refunds + cash_in - cash_out
        self.shifts.update(shift_id, {
            "cash_sales": str(sales),
            "cash_refunds": str(refunds),
            "cash_in": str(cash_in),
            "cash_out": str(cash_out),
            "expected_cash": str(expected),
        })

    def close_shift(self, actor, shift_id: str, actual_cash: Decimal | str, notes: str = "") -> dict:
        if actor is not None and not has_permission(actor, "cash_register.manage"):
            # cashier can close own shift? allow if same user
            if (actor or {}).get("user_id") != (self.shifts.get(shift_id) or {}).get("user_id"):
                raise PermissionError("Missing permission: cash_register.manage")
        shift = self.shifts.get(shift_id)
        if not shift or shift.get("status") != "open":
            raise NotFoundError("Open shift not found.")
        self._recalculate(shift_id)
        shift = self.shifts.get(shift_id)
        actual = Decimal(str(actual_cash))
        expected = Decimal(shift.get("expected_cash") or "0")
        variance = actual - expected
        now = iso_now()
        self.shifts.update(shift_id, {
            "closed_at": now,
            "closing_cash": str(actual),
            "expected_cash": str(expected),
            "status": "closed",
            "notes": (optional_text(notes) + f" Variance: {variance}").strip(),
        })
        if self.audit:
            self.audit.log((actor or {}).get("user_id", ""), "close_shift", "shift", shift_id, str(variance))
        return self.shifts.get(shift_id)

    def reconcile(self, shift_id: str) -> dict:
        shift = self.shifts.get(shift_id)
        if not shift:
            raise NotFoundError("Shift not found.")
        self._recalculate(shift_id)
        return self.shifts.get(shift_id)