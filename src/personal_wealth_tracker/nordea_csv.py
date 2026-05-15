from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import Transaction
from .utils import parse_danish_decimal, transaction_hash


REQUIRED_HEADERS = (
    "Booking date",
    "Amount",
    "Balance",
    "Currency",
    "Name",
    "Title",
    "Sender",
    "Recipient",
    "Reconciled",
)
GENERIC_PROVIDER_NAMES = {"Vipps MobilePay"}


def parse_nordea_csv(path: Path, expected_currency: str = "DKK") -> list[Transaction]:
    expected_currency = expected_currency.upper()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        _validate_headers(reader.fieldnames)
        transactions = []
        for index, row in enumerate(reader):
            row_number = index + 2
            row_currency = (row.get("Currency") or "").strip().upper()
            if not row_currency:
                raise ValueError(f"Nordea CSV row {row_number} currency is missing.")
            if row_currency != expected_currency:
                raise ValueError(
                    f"Nordea CSV row {row_number} currency {row_currency!r} does not match "
                    f"expected currency {expected_currency!r}."
                )

            booked_date = datetime.strptime(row["Booking date"].strip(), "%Y/%m/%d").date()
            amount = parse_danish_decimal(row["Amount"])
            balance = parse_danish_decimal(row["Balance"]) if row.get("Balance") else None
            description = _derive_description(row)
            transaction_id = transaction_hash(booked_date, amount, description, index)
            transactions.append(
                Transaction(
                    transaction_id=transaction_id,
                    date=booked_date,
                    interest_date=None,
                    description=description,
                    amount=amount,
                    currency=row_currency,
                    direction="income" if amount >= 0 else "expense",
                    balance=balance,
                    merchant=description or None,
                    source_file=path,
                    details=_raw_details(row),
                )
            )
    return transactions


def _validate_headers(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("Nordea CSV is missing a header row.")
    missing = [header for header in REQUIRED_HEADERS if header not in fieldnames]
    if missing:
        raise ValueError(f"Nordea CSV is missing required headers: {', '.join(missing)}.")


def _derive_description(row: dict[str, str]) -> str:
    name = (row.get("Name") or "").strip()
    title = (row.get("Title") or "").strip()
    if name and name not in GENERIC_PROVIDER_NAMES:
        return name
    return title or name


def _raw_details(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(f"{key}={value}" for key, value in row.items())
