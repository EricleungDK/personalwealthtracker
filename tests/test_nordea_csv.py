from decimal import Decimal
from pathlib import Path

import pytest

from personal_wealth_tracker.nordea_csv import parse_nordea_csv


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
