from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from personal_wealth_tracker.config import AppConfig
from personal_wealth_tracker.models import CategorizedTransaction, LocalLLMAvailability, Transaction
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


def test_pipeline_auto_routes_csv_statement_to_nordea_csv(monkeypatch, tmp_path):
    _stub_pipeline_dependencies(monkeypatch)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_csv",
        lambda _path, expected_currency: [_transaction(date(2026, 4, 1))],
    )

    result = run_pipeline(
        tracker_path=Path("tracker.xlsx"),
        statement_path=Path("statement.csv"),
        config_dir=Path("config"),
        year=2026,
        month="Apr",
        output_dir=tmp_path,
    )

    assert result.statement_parser == "nordea-csv"
    assert len(result.transactions) == 1


def test_pipeline_auto_routes_pdf_statement_to_nordea_pdf(monkeypatch, tmp_path):
    _stub_pipeline_dependencies(monkeypatch)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_pdf",
        lambda _path, expected_currency: [_transaction(date(2026, 4, 2))],
    )

    result = run_pipeline(
        tracker_path=Path("tracker.xlsx"),
        statement_path=Path("statement.PDF"),
        config_dir=Path("config"),
        year=2026,
        month="Apr",
        output_dir=tmp_path,
    )

    assert result.statement_parser == "nordea-pdf"
    assert len(result.transactions) == 1


def test_pipeline_explicit_statement_format_overrides_extension(monkeypatch, tmp_path):
    _stub_pipeline_dependencies(monkeypatch)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_csv",
        lambda _path, expected_currency: [_transaction(date(2026, 4, 3))],
    )

    result = run_pipeline(
        tracker_path=Path("tracker.xlsx"),
        statement_path=Path("statement.pdf"),
        config_dir=Path("config"),
        year=2026,
        month="Apr",
        output_dir=tmp_path,
        statement_format="nordea-csv",
    )

    assert result.statement_parser == "nordea-csv"
    assert len(result.transactions) == 1


def test_pipeline_explicit_pdf_statement_format_overrides_csv_extension(monkeypatch, tmp_path):
    _stub_pipeline_dependencies(monkeypatch)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_pdf",
        lambda _path, expected_currency: [_transaction(date(2026, 4, 4))],
    )

    result = run_pipeline(
        tracker_path=Path("tracker.xlsx"),
        statement_path=Path("statement.csv"),
        config_dir=Path("config"),
        year=2026,
        month="Apr",
        output_dir=tmp_path,
        statement_format="nordea-pdf",
    )

    assert result.statement_parser == "nordea-pdf"
    assert len(result.transactions) == 1


def test_pipeline_auto_rejects_unsupported_statement_extension(monkeypatch, tmp_path):
    _stub_pipeline_dependencies(monkeypatch)

    with pytest.raises(ValueError, match="Could not infer statement format.*statement-format"):
        run_pipeline(
            tracker_path=Path("tracker.xlsx"),
            statement_path=Path("statement.txt"),
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


def test_pipeline_preserves_target_period_validation_after_csv_parsing(monkeypatch, tmp_path):
    _stub_pipeline_dependencies(monkeypatch)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_csv",
        lambda _path, expected_currency: [_transaction(date(2026, 5, 1))],
    )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("categorization should not run for out-of-period statements")

    monkeypatch.setattr("personal_wealth_tracker.pipeline.categorize_transactions", fail_if_called)

    with pytest.raises(ValueError, match="outside target period Apr 2026"):
        run_pipeline(
            tracker_path=Path("tracker.xlsx"),
            statement_path=Path("statement.csv"),
            config_dir=Path("config"),
            year=2026,
            month="Apr",
            output_dir=tmp_path,
        )


def test_pipeline_does_not_call_local_llm_client_when_mode_is_disabled(monkeypatch, tmp_path):
    _stub_pipeline_dependencies(monkeypatch)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_csv",
        lambda _path, expected_currency: [_transaction(date(2026, 4, 1))],
    )

    class FailingClient:
        def check_availability(self, _config):
            raise AssertionError("local LLM client should not be called without explicit opt-in")

    result = run_pipeline(
        tracker_path=Path("tracker.xlsx"),
        statement_path=Path("statement.csv"),
        config_dir=Path("config"),
        year=2026,
        month="Apr",
        output_dir=tmp_path,
        local_llm_client=FailingClient(),
    )

    assert result.local_llm_diagnostics.enabled is False


def test_pipeline_keeps_review_output_when_local_llm_provider_is_unavailable(
    monkeypatch, tmp_path
):
    _stub_pipeline_dependencies(monkeypatch)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.parse_nordea_csv",
        lambda _path, expected_currency: [_transaction(date(2026, 4, 1))],
    )

    class UnavailableClient:
        def check_availability(self, _config):
            return LocalLLMAvailability(
                available=False,
                model=None,
                warning="Ollama is unavailable at http://localhost:11434.",
            )

    result = run_pipeline(
        tracker_path=Path("tracker.xlsx"),
        statement_path=Path("statement.csv"),
        config_dir=Path("config"),
        year=2026,
        month="Apr",
        output_dir=tmp_path,
        local_llm_suggestions=True,
        local_llm_client=UnavailableClient(),
    )

    assert result.categorized_transactions[0].categorization_method == "unmatched"
    assert result.categorized_transactions[0].review_required is True
    assert result.local_llm_diagnostics.enabled is True
    assert result.local_llm_diagnostics.provider_failure_count == 1
    assert result.local_llm_diagnostics.warnings == (
        "Ollama is unavailable at http://localhost:11434.",
    )
    report = result.report_path.read_text(encoding="utf-8")
    assert "## Local LLM Mode" in report
    assert "- Status: enabled" in report
    assert "- Provider failures: 1" in report
    assert "Ollama is unavailable" in report
    audit = result.audit_path.read_text(encoding="utf-8")
    assert '"record_type": "local_llm_warning"' in audit
    assert "Ollama is unavailable" in audit


def _empty_workbook_plan():
    from personal_wealth_tracker.models import WorkbookPlan

    return WorkbookPlan(updates=[], structure_changes=[])


def _stub_pipeline_dependencies(monkeypatch):
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
    monkeypatch.setattr("personal_wealth_tracker.pipeline.load_category_memory", lambda _path: None)
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.categorize_transactions",
        lambda transactions, *_args, **_kwargs: [
            CategorizedTransaction(
                transaction=transaction,
                suggested_category=None,
                confidence=0.0,
                categorization_method="unmatched",
                review_required=True,
                reason="No category match.",
            )
            for transaction in transactions
        ],
    )
    monkeypatch.setattr(
        "personal_wealth_tracker.pipeline.plan_workbook_changes",
        lambda *_args, **_kwargs: _empty_workbook_plan(),
    )
