from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from personal_wealth_tracker.categorizer import categorize_transactions
from personal_wealth_tracker.category_memory import CategoryMemory, CategoryMemoryMapping
from personal_wealth_tracker.config import AppConfig, RecurringRule, Rule, load_config
from personal_wealth_tracker.models import Authority, Transaction


def _config() -> AppConfig:
    return AppConfig(
        sheet_name="Net worth",
        tracker_currency="DKK",
        category_column=2,
        year_header_row=2,
        month_header_row=3,
        statement_currency="DKK",
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


def test_category_memory_overrides_historical_mappings():
    memory = CategoryMemory(
        mappings=(
            CategoryMemoryMapping(
                merchant_identity="APPLE.COM/BILL",
                category="Food& Drinks (monthly)",
                source_transaction_ids=("reviewed-apple",),
            ),
        )
    )

    result = categorize_transactions(
        [_transaction("APPLE.COM/BILL", "-25.00")],
        _config(),
        category_memory=memory,
    )[0]

    assert result.suggested_category == "Food& Drinks (monthly)"
    assert result.categorization_method == "category_memory"
    assert not result.review_required


def test_guidance_alias_categorises_ahead_of_historical_recurring_and_rule_tiers():
    config = replace(
        _config(),
        guidance_aliases={
            "apple.com": "Lunch (monthly)",
            "telecom": "Lunch (monthly)",
            "canteen": "Lunch (monthly)",
        },
        rules=(Rule("Food& Drinks (monthly)", ("canteen",), "expense", 0.9),),
    )

    results = categorize_transactions(
        [
            _transaction("APPLE.COM/BILL", "-25.00"),
            _transaction("PRIVATE TELECOM", "-99.50"),
            _transaction("CANTEEN NORTH 12", "-45.00"),
        ],
        config,
    )

    assert [result.suggested_category for result in results] == ["Lunch (monthly)"] * 3
    assert {result.categorization_method for result in results} == {"guidance_alias"}
    assert all(result.authority is Authority.auto for result in results)


def test_guidance_alias_refund_nets_against_alias_category():
    config = replace(_config(), guidance_aliases={"canteen": "Lunch (monthly)"})

    result = categorize_transactions([_transaction("CANTEEN NORTH REFUND", "45.00")], config)[0]

    assert result.suggested_category == "Lunch (monthly)"
    assert result.reason == (
        "Refund matched guidance alias; nets against category in reporting month."
    )


def test_category_memory_overrides_guidance_alias():
    memory = CategoryMemory(
        mappings=(
            CategoryMemoryMapping(
                merchant_identity="CANTEEN NORTH",
                category="Food& Drinks (monthly)",
                source_transaction_ids=("reviewed-canteen",),
            ),
        )
    )
    config = replace(_config(), guidance_aliases={"canteen": "Lunch (monthly)"})

    result = categorize_transactions(
        [_transaction("CANTEEN NORTH", "-45.00")], config, category_memory=memory
    )[0]

    assert result.suggested_category == "Food& Drinks (monthly)"
    assert result.categorization_method == "category_memory"


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


def test_category_memory_overrides_recurring_rules():
    memory = CategoryMemory(
        mappings=(
            CategoryMemoryMapping(
                merchant_identity="PRIVATE TELECOM",
                category="Food& Drinks (monthly)",
                source_transaction_ids=("reviewed-telecom",),
            ),
        )
    )

    result = categorize_transactions(
        [_transaction("PRIVATE TELECOM", "-99.50")],
        _config(),
        category_memory=memory,
    )[0]

    assert result.suggested_category == "Food& Drinks (monthly)"
    assert result.categorization_method == "category_memory"


def test_unmatched_requires_review():
    result = categorize_transactions([_transaction("UNKNOWN", "-100.00")], _config())[0]

    assert result.suggested_category is None
    assert result.review_required


def test_deterministic_match_above_auto_cap_requires_review():
    result = categorize_transactions([_transaction("NETTO", "-1000.01")], _config())[0]

    assert result.suggested_category == "Food& Drinks (monthly)"
    assert result.authority is Authority.review
    assert result.authority_reason == "Amount 1000.01 is above the auto cap 1000."


def test_never_auto_category_requires_review_even_from_confident_rule():
    config = replace(
        _config(),
        trust_policy=replace(
            _config().trust_policy,
            never_auto_categories=frozenset({"Food& Drinks (monthly)"}),
        ),
    )

    result = categorize_transactions([_transaction("NETTO", "-50.00")], config)[0]

    assert result.authority is Authority.review
    assert result.authority_reason == "Food& Drinks (monthly) is a never-auto category."


def test_low_confidence_rule_requires_review():
    config = replace(_config(), rules=(Rule("Food& Drinks (monthly)", ("netto",), "expense", 0.7),))

    result = categorize_transactions([_transaction("NETTO", "-50.00")], config)[0]

    assert result.authority is Authority.review
    assert "below the auto threshold" in result.authority_reason


def test_project_config_maps_mastercard_by_transaction_direction():
    config = load_config(Path("config"))

    negative, positive = categorize_transactions(
        [
            _transaction("MASTERCARD", "-4000.00"),
            _transaction("MASTERCARD", "400.00"),
        ],
        config,
    )

    assert negative.suggested_category == "Nordea Credit Card"
    assert negative.confidence == 0.98
    assert negative.authority is Authority.review
    assert "above the auto cap" in negative.authority_reason
    assert positive.suggested_category == "Mastercard refund"
    assert positive.confidence == 0.98
    assert positive.authority is Authority.auto


def test_project_config_uses_csv_merchant_descriptions_for_known_categories_only():
    config = load_config(Path("config"))

    google_one, cbb_mobil, mobilepay_rejsekort = categorize_transactions(
        [
            _transaction("GOOGLE ONE", "-25.00"),
            _transaction("CBB MOBIL", "-99.00"),
            _transaction("MobilePay Rejsekort", "-150.00"),
        ],
        config,
    )

    assert google_one.suggested_category == "Google Cloud"
    assert not google_one.review_required
    assert cbb_mobil.suggested_category == "Mobile phone (monthly)"
    assert not cbb_mobil.review_required
    assert mobilepay_rejsekort.suggested_category is None
    assert mobilepay_rejsekort.review_required
