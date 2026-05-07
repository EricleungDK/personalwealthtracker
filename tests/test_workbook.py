from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook, load_workbook

from personal_wealth_tracker.config import AppConfig
from personal_wealth_tracker.models import CategorizedTransaction, Transaction
from personal_wealth_tracker.workbook import commit_updates, plan_updates


def test_plan_updates_aggregates_and_marks_writeable_empty_cells(tmp_path):
    tracker = _workbook_path(tmp_path)
    _create_workbook(tracker)

    updates = plan_updates(
        tracker,
        [
            _categorized("tx-food-1", "Food& Drinks (monthly)", "-10.50"),
            _categorized("tx-food-2", "Food& Drinks (monthly)", "-20.25"),
        ],
        2026,
        "Apr",
        _config(),
    )

    assert len(updates) == 1
    assert updates[0].category == "Food& Drinks (monthly)"
    assert updates[0].amount == Decimal("30.75")
    assert updates[0].target_cell == "C5"
    assert updates[0].write_action == "write"


def test_plan_updates_protects_formula_manual_fixed_and_review_rows(tmp_path):
    tracker = _workbook_path(tmp_path)
    _create_workbook(tracker)

    updates = {
        update.category: update
        for update in plan_updates(
            tracker,
            [
                _categorized("tx-formula", "Formula Category", "-1.00"),
                _categorized("tx-manual", "Manual Category", "-2.00"),
                _categorized("tx-fixed", "Fixed Category", "-3.00"),
                _categorized("tx-review", "Review Category", "-4.00", review_required=True),
                _categorized("tx-missing", "Missing Category", "-5.00"),
            ],
            2026,
            "Apr",
            _config(fixed_rows=frozenset({"Fixed Category"})),
        )
    }

    assert updates["Formula Category"].write_action == "skip"
    assert updates["Formula Category"].reason == "Target cell contains a formula."
    assert updates["Manual Category"].write_action == "review"
    assert updates["Manual Category"].reason == "Target cell already contains a manual value."
    assert updates["Fixed Category"].write_action == "skip"
    assert updates["Fixed Category"].reason == "Fixed row is protected by config."
    assert updates["Review Category"].write_action == "review"
    assert updates["Review Category"].reason == "One or more source transactions require review."
    assert updates["Missing Category"].write_action == "review"
    assert updates["Missing Category"].reason == "Target category row not found."


def test_commit_updates_writes_only_eligible_updates_to_copied_workbook(tmp_path):
    tracker = _workbook_path(tmp_path)
    _create_workbook(tracker)
    config = _config(fixed_rows=frozenset({"Fixed Category"}))
    updates = plan_updates(
        tracker,
        [
            _categorized("tx-food", "Food& Drinks (monthly)", "-30.00"),
            _categorized("tx-formula", "Formula Category", "-1.00"),
            _categorized("tx-manual", "Manual Category", "-2.00"),
            _categorized("tx-fixed", "Fixed Category", "-3.00"),
        ],
        2026,
        "Apr",
        config,
    )

    output_path = commit_updates(tracker, updates, config, tmp_path / "processed")

    original = load_workbook(tracker)
    copied = load_workbook(output_path, data_only=False)
    try:
        original_sheet = original["Net worth"]
        copied_sheet = copied["Net worth"]
        assert original_sheet["C5"].value is None
        assert copied_sheet["C5"].value == 30
        assert copied_sheet["C6"].value == "=1+1"
        assert copied_sheet["C7"].value == 123
        assert copied_sheet["C8"].value is None
    finally:
        original.close()
        copied.close()


def _create_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Net worth"
    sheet["C2"] = 2026
    sheet["C3"] = "Apr"
    sheet["B5"] = "Food& Drinks (monthly)"
    sheet["B6"] = "Formula Category"
    sheet["C6"] = "=1+1"
    sheet["B7"] = "Manual Category"
    sheet["C7"] = 123
    sheet["B8"] = "Fixed Category"
    sheet["B9"] = "Review Category"
    workbook.save(path)
    workbook.close()


def _workbook_path(tmp_path) -> Path:
    return tmp_path / "tracker.xlsx"


def _config(fixed_rows: frozenset[str] = frozenset()) -> AppConfig:
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
        categories=(),
        aliases={},
        historical_mappings={},
        rules=(),
        fixed_rows=fixed_rows,
    )


def _categorized(
    transaction_id: str,
    category: str,
    amount: str,
    review_required: bool = False,
) -> CategorizedTransaction:
    return CategorizedTransaction(
        transaction=Transaction(
            transaction_id=transaction_id,
            date=date(2026, 4, 30),
            interest_date=None,
            description="REDACTED",
            amount=Decimal(amount),
            currency="DKK",
            direction="expense",
        ),
        suggested_category=category,
        confidence=0.9,
        categorization_method="rule",
        review_required=review_required,
        reason="Test transaction",
    )
