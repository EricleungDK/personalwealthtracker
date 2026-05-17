from decimal import Decimal
from pathlib import Path

import pytest

from personal_wealth_tracker.nordea_csv import parse_nordea_csv
import personal_wealth_tracker.utils as utils


FIXTURE = Path(__file__).parent / "fixtures" / "nordea_transactions.redacted.csv"


def test_parse_redacted_nordea_csv_fixture():
    transactions = parse_nordea_csv(FIXTURE)

    assert len(transactions) == 5

    food = transactions[0]
    assert food.date.isoformat() == "2026-04-01"
    assert food.interest_date is None
    assert food.amount == Decimal("-123.45")
    assert food.balance == Decimal("9876.55")
    assert food.currency == "DKK"
    assert food.direction == "expense"
    assert food.description == "FOETEX SCANNGO"
    assert food.merchant == "FOETEX SCANNGO"

    mobilepay = transactions[1]
    assert mobilepay.description == "MobilePay Rejsekort"
    assert mobilepay.merchant == "MobilePay Rejsekort"

    salary = transactions[2]
    assert salary.amount == Decimal("25000.00")
    assert salary.direction == "income"
    assert salary.description == "NORDIC EMPLOYER PAYROLL"

    mastercard = transactions[3]
    assert mastercard.description == "MASTERCARD"
    assert mastercard.merchant == "MASTERCARD"

    unknown = transactions[4]
    assert unknown.description == "Unknown reference"
    assert unknown.merchant == "Unknown reference"

    assert "Sender" not in food.description
    assert "1111" not in food.description
    assert any(detail == "Name=FOETEX SCANNGO" for detail in food.details)
    assert any(detail == "Sender=1111 2222222222" for detail in food.details)


def test_rejects_missing_or_unexpected_row_currency(tmp_path):
    unexpected_currency = tmp_path / "unexpected-currency.csv"
    unexpected_currency.write_text(
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        "2026/04/01;-10,00;990,00;EUR;NETTO;Card purchase;1111;2222;Yes\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="row 2 currency 'EUR'.*'DKK'"):
        parse_nordea_csv(unexpected_currency, expected_currency="DKK")

    missing_currency = tmp_path / "missing-currency.csv"
    missing_currency.write_text(
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        "2026/04/01;-10,00;990,00;;NETTO;Card purchase;1111;2222;Yes\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="row 2 currency is missing"):
        parse_nordea_csv(missing_currency, expected_currency="DKK")


def test_csv_transaction_ids_are_stable_across_repeated_parses_order_and_path(tmp_path):
    rows = [
        _csv_row("2026/04/01", "-10,00", "990,00", "NETTO", "Card purchase"),
        _csv_row("2026/04/02", "-20,00", "970,00", "BAKERY", "Card purchase"),
        _csv_row("2026/04/02", "-20,00", "950,00", "BAKERY", "Card purchase"),
        _csv_row("2026/04/03", "100,00", "1050,00", "REFUND SHOP", "Refund"),
    ]
    original = tmp_path / "original.csv"
    reordered = tmp_path / "subfolder" / "renamed.csv"
    same_content_other_path = tmp_path / "same-content-other-path.csv"
    reordered.parent.mkdir()
    _write_csv(original, rows)
    _write_csv(same_content_other_path, rows)
    _write_csv(reordered, [rows[3], rows[1], rows[0], rows[2]])

    first_parse = parse_nordea_csv(original)
    repeated_parse = parse_nordea_csv(original)
    other_path_parse = parse_nordea_csv(same_content_other_path)
    reordered_parse = parse_nordea_csv(reordered)

    assert [tx.transaction_id for tx in repeated_parse] == [tx.transaction_id for tx in first_parse]
    assert [tx.transaction_id for tx in other_path_parse] == [tx.transaction_id for tx in first_parse]
    assert _ids_by_unique_description(reordered_parse)["NETTO"] == _ids_by_unique_description(first_parse)[
        "NETTO"
    ]
    assert _ids_by_unique_description(reordered_parse)["REFUND SHOP"] == _ids_by_unique_description(
        first_parse
    )["REFUND SHOP"]

    bakery_ids_by_balance = _ids_by_description_and_balance(first_parse, "BAKERY")
    reordered_bakery_ids_by_balance = _ids_by_description_and_balance(reordered_parse, "BAKERY")
    bakery_ids = list(bakery_ids_by_balance.values())
    assert reordered_bakery_ids_by_balance == bakery_ids_by_balance
    assert len(bakery_ids) == 2
    assert len(set(bakery_ids)) == 2
    assert all(
        tx.transaction_id.startswith(f"{utils.TRANSACTION_ID_SCHEME_VERSION}:")
        for tx in first_parse
    )
    assert any(tx.transaction_id.endswith(":001") for tx in first_parse)


def test_csv_duplicate_occurrences_are_stable_when_headers_are_reordered(tmp_path):
    canonical_headers = [
        "Booking date",
        "Amount",
        "Balance",
        "Currency",
        "Name",
        "Title",
        "Sender",
        "Recipient",
        "Reconciled",
    ]
    reordered_headers = [
        "Currency",
        "Recipient",
        "Sender",
        "Title",
        "Name",
        "Balance",
        "Amount",
        "Booking date",
        "Reconciled",
    ]
    row_a = {
        "Booking date": "2026/04/02",
        "Amount": "-20,00",
        "Balance": "970,00",
        "Currency": "DKK",
        "Name": "BAKERY",
        "Title": "Card purchase",
        "Sender": "Z-SENDER",
        "Recipient": "A-RECIPIENT",
        "Reconciled": "Yes",
    }
    row_b = {
        "Booking date": "2026/04/02",
        "Amount": "-20,00",
        "Balance": "970,00",
        "Currency": "DKK",
        "Name": "BAKERY",
        "Title": "Card purchase",
        "Sender": "A-SENDER",
        "Recipient": "Z-RECIPIENT",
        "Reconciled": "Yes",
    }
    canonical = tmp_path / "canonical.csv"
    reordered = tmp_path / "reordered.csv"
    _write_csv_dicts(canonical, canonical_headers, [row_a, row_b])
    _write_csv_dicts(reordered, reordered_headers, [row_a, row_b])

    canonical_transactions = parse_nordea_csv(canonical)
    reordered_transactions = parse_nordea_csv(reordered)

    assert _ids_by_sender(canonical_transactions) == _ids_by_sender(reordered_transactions)


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text(
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )


def _csv_row(date: str, amount: str, balance: str, name: str, title: str) -> str:
    return f"{date};{amount};{balance};DKK;{name};{title};1111;2222;Yes"


def _write_csv_dicts(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    lines = [";".join(headers)]
    lines.extend(";".join(row[header] for header in headers) for row in rows)
    path.write_text("\ufeff" + "\n".join(lines) + "\n", encoding="utf-8")


def _ids_by_unique_description(transactions):
    return {
        transaction.description: transaction.transaction_id
        for transaction in transactions
        if sum(1 for item in transactions if item.description == transaction.description) == 1
    }


def _ids_by_description_and_balance(transactions, description):
    return {
        transaction.balance: transaction.transaction_id
        for transaction in transactions
        if transaction.description == description
    }


def _ids_by_sender(transactions):
    return {
        next(
            detail for detail in transaction.details if detail.startswith("Sender=")
        ): transaction.transaction_id
        for transaction in transactions
    }
