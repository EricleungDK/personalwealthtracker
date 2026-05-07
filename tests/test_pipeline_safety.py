from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from personal_wealth_tracker.config import AppConfig
from personal_wealth_tracker.models import Transaction
from personal_wealth_tracker.pipeline import _validate_target_period, run_pipeline


def _transaction(transaction_date: date) -> Transaction:
    return Transaction(
        transaction_id=f"tx-{transaction_date.isoformat()}",
        date=transaction_date,
        interest_date=None,
        description="REDACTED",
        amount=Decimal("-1.00"),
        currency="DKK",
        direction="expense",
    )


def test_validate_target_period_accepts_matching_month():
    _validate_target_period([_transaction(date(2026, 4, 30))], 2026, "Apr")


def test_validate_target_period_rejects_out_of_period_transactions():
    with pytest.raises(ValueError, match="outside target period Apr 2026"):
        _validate_target_period(
            [_transaction(date(2026, 4, 30)), _transaction(date(2026, 5, 1))],
            2026,
            "Apr",
        )


def test_pipeline_rejects_tracker_statement_currency_mismatch(monkeypatch, tmp_path):
    config = AppConfig(
        sheet_name="Net worth",
        tracker_currency="DKK",
        category_column=2,
        year_header_row=2,
        month_header_row=3,
        statement_currency="EUR",
        auto_write_threshold=0.85,
        review_threshold=0.60,
        reject_threshold=0.60,
        overwrite_fixed_rows=False,
        highlight_auto_filled_cells=False,
        categories=(),
        aliases={},
        historical_mappings={},
        rules=(),
        fixed_rows=frozenset(),
    )
    monkeypatch.setattr("personal_wealth_tracker.pipeline.load_config", lambda _path: config)

    with pytest.raises(ValueError, match="must match statement currency"):
        run_pipeline(
            tracker_path=Path("tracker.xlsx"),
            statement_path=Path("statement.pdf"),
            config_dir=Path("config"),
            year=2026,
            month="Apr",
            output_dir=tmp_path,
        )


def test_pipeline_rejects_out_of_period_before_categorization(monkeypatch, tmp_path):
    config = AppConfig(
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
        fixed_rows=frozenset(),
    )
    monkeypatch.setattr("personal_wealth_tracker.pipeline.load_config", lambda _path: config)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_pdf",
        lambda _path, expected_currency: [_transaction(date(2026, 5, 1))],
    )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("categorization should not run for out-of-period statements")

    monkeypatch.setattr("personal_wealth_tracker.pipeline.categorize_transactions", fail_if_called)

    with pytest.raises(ValueError, match="outside target period Apr 2026"):
        run_pipeline(
            tracker_path=Path("tracker.xlsx"),
            statement_path=Path("statement.pdf"),
            config_dir=Path("config"),
            year=2026,
            month="Apr",
            output_dir=tmp_path,
        )
