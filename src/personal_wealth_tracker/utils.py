from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Transaction


MONTH_ALIASES = {
    "jan": "Jan",
    "january": "Jan",
    "feb": "Feb",
    "february": "Feb",
    "mar": "Mar",
    "march": "Mar",
    "apr": "Apr",
    "april": "Apr",
    "may": "May",
    "jun": "Jun",
    "june": "Jun",
    "jul": "Jul",
    "july": "Jul",
    "aug": "Aug",
    "august": "Aug",
    "sep": "Sep",
    "sept": "Sep",
    "september": "Sep",
    "oct": "Oct",
    "october": "Oct",
    "nov": "Nov",
    "november": "Nov",
    "dec": "Dec",
    "december": "Dec",
}
TRANSACTION_ID_SCHEME_VERSION = "stable-content-v2"


def parse_danish_decimal(value: str) -> Decimal:
    normalized = value.strip().replace(".", "").replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid Danish decimal: {value!r}") from exc


def parse_danish_date(value: str, fallback_year: int | None = None) -> date:
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    if fallback_year is not None:
        try:
            parsed = datetime.strptime(f"{value}.{fallback_year}", "%d.%m.%Y").date()
        except ValueError:
            pass
        else:
            return parsed

    raise ValueError(f"Invalid Danish date: {value!r}")


def normalize_month(value: str) -> str:
    key = value.strip().lower()
    if key not in MONTH_ALIASES:
        raise ValueError(f"Unsupported month: {value!r}")
    return MONTH_ALIASES[key]


def normalize_text(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text).strip().upper()


def transaction_hash(*parts: object) -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def assign_stable_transaction_ids(transactions: list[Transaction]) -> list[Transaction]:
    grouped: dict[tuple[object, ...], list[tuple[int, Transaction]]] = {}
    for index, transaction in enumerate(transactions):
        grouped.setdefault(_transaction_base_identity(transaction), []).append((index, transaction))

    occurrences: dict[int, int] = {}
    for items in grouped.values():
        for occurrence, (index, _) in enumerate(
            sorted(items, key=lambda item: _transaction_occurrence_sort_key(item[1])),
            start=1,
        ):
            occurrences[index] = occurrence

    return [
        replace(
            transaction,
            transaction_id=_stable_transaction_id(
                _transaction_base_identity(transaction), occurrences[index]
            ),
        )
        for index, transaction in enumerate(transactions)
    ]


def _stable_transaction_id(base_identity: tuple[object, ...], occurrence: int) -> str:
    payload = json.dumps(
        [TRANSACTION_ID_SCHEME_VERSION, *base_identity],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{TRANSACTION_ID_SCHEME_VERSION}:{digest}:{occurrence:03d}"


def _transaction_base_identity(transaction: Transaction) -> tuple[object, ...]:
    return (
        transaction.date.isoformat(),
        transaction.interest_date.isoformat() if transaction.interest_date else "",
        _decimal_identity(transaction.amount),
        transaction.currency.upper(),
        normalize_text(transaction.description),
        normalize_text(transaction.merchant or ""),
        _decimal_identity(transaction.original_amount),
        (transaction.original_currency or "").upper(),
        _decimal_identity(transaction.balance),
        tuple(sorted(_detail_identity(detail) for detail in transaction.details)),
    )


def _transaction_occurrence_sort_key(transaction: Transaction) -> tuple[object, ...]:
    return _transaction_base_identity(transaction)


def _decimal_identity(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value.normalize(), "f")


def _detail_identity(value: str) -> tuple[str, str]:
    key, separator, detail_value = value.partition("=")
    if not separator:
        return ("", normalize_text(value))
    return (normalize_text(key), normalize_text(detail_value))
