from dataclasses import replace
from datetime import date
from decimal import Decimal

from personal_wealth_tracker.categorizer import categorize_transactions
from personal_wealth_tracker.config import AppConfig, RecurringRule, Rule
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
        recurring_rules=(
            RecurringRule(
                category="Mobile phone (monthly)",
                amount=Decimal("99.00"),
                amount_tolerance=Decimal("1.00"),
                day_min=25,
                day_max=31,
                match_keywords=("telecom",),
                direction="expense",
                confidence=0.95,
            ),
        ),
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


def test_refund_keyword_rule_matches_expense_category_for_netting():
    result = categorize_transactions([_transaction("NETTO REFUND", "25.00")], _config())[0]

    assert result.suggested_category == "Food& Drinks (monthly)"
    assert result.categorization_method == "rule"
    assert not result.review_required
    assert "Refund" in result.reason


def test_vague_refund_without_category_match_requires_review():
    result = categorize_transactions([_transaction("REFUND", "25.00")], _config())[0]

    assert result.suggested_category is None
    assert result.review_required
    assert result.reason == (
        "Refund-like transaction needs review because no deterministic category matched."
    )


def test_deterministic_expense_claim_maps_to_existing_expense_claims_category():
    base_config = _config()
    config = replace(
        base_config,
        categories=(*base_config.categories, "Expense claims"),
        rules=(
            *base_config.rules,
            Rule("Expense claims", ("expense claim", "reimbursement"), "income", 0.95),
        ),
    )

    result = categorize_transactions([_transaction("ACME EXPENSE CLAIM", "125.00")], config)[0]

    assert result.suggested_category == "Expense claims"
    assert result.categorization_method == "rule"
    assert not result.review_required
    assert "Expense claim" in result.reason


def test_recurring_rule_matches_before_keyword_rules():
    result = categorize_transactions([_transaction("PRIVATE TELECOM", "-99.50")], _config())[0]

    assert result.suggested_category == "Mobile phone (monthly)"
    assert result.categorization_method == "recurring"


def test_unmatched_requires_review():
    result = categorize_transactions([_transaction("UNKNOWN", "-100.00")], _config())[0]

    assert result.suggested_category is None
    assert result.review_required
