from datetime import date
from decimal import Decimal

from personal_wealth_tracker.categorizer import categorize_transactions
from personal_wealth_tracker.config import AppConfig, Rule
from personal_wealth_tracker.models import Transaction


def _config() -> AppConfig:
    return AppConfig(
        sheet_name="Net worth",
        tracker_currency="DKK",
        category_column=2,
        year_header_row=2,
        month_header_row=3,
        statement_currency="DKK",
        auto_write_threshold=0.85,
        review_threshold=0.60,
        reject_threshold=0.60,
        overwrite_fixed_rows=False,
        highlight_auto_filled_cells=False,
        categories=("Apple Cloud", "Food& Drinks (monthly)"),
        aliases={},
        historical_mappings={"APPLE.COM/BILL": "Apple Cloud"},
        rules=(Rule("Food& Drinks (monthly)", ("netto",), "expense", 0.9),),
        fixed_rows=frozenset(),
    )


def _transaction(description: str, amount: str) -> Transaction:
    return Transaction(
        transaction_id="tx1",
        date=date(2026, 4, 30),
        interest_date=None,
        description=description,
        amount=Decimal(amount),
        currency="DKK",
        direction="income" if Decimal(amount) >= 0 else "expense",
    )


def test_historical_mapping_wins():
    result = categorize_transactions([_transaction("APPLE.COM/BILL", "-25.00")], _config())[0]

    assert result.suggested_category == "Apple Cloud"
    assert result.categorization_method == "historical"
    assert not result.review_required


def test_keyword_rule_matches():
    result = categorize_transactions([_transaction("NETTO KOEBENHAVN", "-100.00")], _config())[0]

    assert result.suggested_category == "Food& Drinks (monthly)"
    assert result.categorization_method == "rule"


def test_unmatched_requires_review():
    result = categorize_transactions([_transaction("UNKNOWN", "-100.00")], _config())[0]

    assert result.suggested_category is None
    assert result.review_required
