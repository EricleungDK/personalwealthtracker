from decimal import Decimal
from pathlib import Path

import pytest

from personal_wealth_tracker.nordea_pdf import parse_nordea_pdf


FIXTURE = Path(__file__).parent / "fixtures" / "nordea_account_statement.redacted.pdf"


def test_parse_redacted_nordea_pdf_fixture():
    transactions = parse_nordea_pdf(FIXTURE)

    assert len(transactions) == 3

    first = transactions[0]
    assert first.date.isoformat() == "2026-04-30"
    assert first.interest_date and first.interest_date.isoformat() == "2026-04-30"
    assert first.amount == Decimal("-25.00")
    assert first.balance == Decimal("9975.00")
    assert first.currency == "DKK"
    assert first.direction == "expense"
    assert first.description == "REDACTED APPLE.COM/BILL"

    income = transactions[1]
    assert income.amount == Decimal("10000.00")
    assert income.direction == "income"

    foreign = transactions[2]
    assert foreign.original_amount == Decimal("123.45")
    assert foreign.original_currency == "NOK"
    assert "REDACTED FOREIGN CARD" in foreign.description
    assert "indsigelse" not in foreign.description.lower()


def test_rejects_unexpected_statement_currency():
    with pytest.raises(ValueError, match="currency"):
        parse_nordea_pdf(FIXTURE, expected_currency="EUR")
