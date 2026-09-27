"""Commit Ledger: the category amounts each committed month wrote into the tracker.

The tracker is updated in place, so a re-commit of a month meets its own earlier values.
A cell still holding the ledger amount is tool-owned and may be rewritten or cleared; any
other value is the user's and stays protected.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from .models import TrackerUpdate


def load_committed_month(ledger_path: Path, year: int, month: str) -> dict[str, Decimal]:
    return {
        category: Decimal(amount)
        for category, amount in _read(ledger_path).get(_month_key(year, month), {}).items()
    }


def record_committed_month(
    ledger_path: Path, year: int, month: str, updates: list[TrackerUpdate]
) -> None:
    ledger = _read(ledger_path)
    ledger[_month_key(year, month)] = {
        update.category: str(update.amount)
        for update in updates
        if update.write_action == "write"
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_committed_value(existing_value: object, committed_amount: Decimal | None) -> bool:
    if committed_amount is None or isinstance(existing_value, bool):
        return False
    if not isinstance(existing_value, (int, float)):
        return False
    return Decimal(str(existing_value)) == committed_amount


def _read(ledger_path: Path) -> dict[str, dict[str, str]]:
    if not ledger_path.exists():
        return {}
    return json.loads(ledger_path.read_text(encoding="utf-8"))


def _month_key(year: int, month: str) -> str:
    return f"{year}-{month}"
