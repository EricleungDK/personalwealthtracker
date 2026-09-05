from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from personal_wealth_tracker.models import Transaction
from personal_wealth_tracker.config import AppConfig
from personal_wealth_tracker.models import (
    LocalLLMDiagnostics,
    StatementImportDiagnostic,
    WorkbookPlan,
)
from personal_wealth_tracker.pipeline import run_pipeline
from personal_wealth_tracker.statement_adapters import (
    NORMALIZED_TRANSACTION_FIELDS,
    StatementImportError,
    TrustedStatementImport,
    import_trusted_statement,
    resolve_statement_adapter,
)
from personal_wealth_tracker.utils import TRANSACTION_ID_SCHEME_VERSION


def test_trusted_statement_adapter_imports_known_csv_with_provenance(tmp_path):
    statement = tmp_path / "statement.csv"
    _write_csv(
        statement,
        [
            "2026/04/01;-10,00;990,00;DKK;GROCERY SHOP;Card purchase;1111;2222;Yes",
            "2026/04/02;100,00;1090,00;DKK;EMPLOYER;Salary;1111;2222;Yes",
        ],
    )

    result = import_trusted_statement(
        statement,
        statement_format="auto",
        expected_currency="DKK",
        year=2026,
        month="Apr",
    )

    assert result.adapter_name == "nordea-csv"
    assert result.parser_identity == "nordea-csv"
    assert result.source_statement == statement
    assert result.diagnostics == ()
    assert NORMALIZED_TRANSACTION_FIELDS == (
        "transaction_id",
        "date",
        "amount",
        "currency",
        "description",
        "direction",
        "source_file",
    )

    first = result.transactions[0]
    assert first.transaction_id.startswith(f"{TRANSACTION_ID_SCHEME_VERSION}:")
    assert first.date == date(2026, 4, 1)
    assert first.amount == Decimal("-10.00")
    assert first.currency == "DKK"
    assert first.description == "GROCERY SHOP"
    assert first.direction == "expense"
    assert first.source_file == statement


def test_resolve_statement_adapter_routes_known_formats_by_explicit_name_and_extension():
    assert resolve_statement_adapter(Path("statement.csv"), "auto").name == "nordea-csv"
    assert resolve_statement_adapter(Path("statement.pdf"), "auto").name == "nordea-pdf"
    assert resolve_statement_adapter(Path("statement.any"), "nordea-csv").name == "nordea-csv"
    assert resolve_statement_adapter(Path("statement.any"), "nordea-pdf").name == "nordea-pdf"


def test_trusted_statement_adapter_reports_duplicate_row_diagnostics(tmp_path):
    statement = tmp_path / "statement.csv"
    _write_csv(
        statement,
        [
            "2026/04/01;-10,00;990,00;DKK;GROCERY SHOP;Card purchase;1111;2222;Yes",
            "2026/04/01;-10,00;990,00;DKK;GROCERY SHOP;Card purchase;1111;2222;Yes",
        ],
    )

    result = import_trusted_statement(
        statement,
        statement_format="nordea-csv",
        expected_currency="DKK",
        year=2026,
        month="Apr",
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["duplicate_row"]
    assert result.diagnostics[0].severity == "warning"
    assert "Duplicate normalized transaction row" in result.diagnostics[0].message


def test_trusted_statement_adapter_rejects_out_of_period_transactions_with_diagnostics(
    tmp_path,
):
    statement = tmp_path / "statement.csv"
    _write_csv(
        statement,
        ["2026/05/01;-10,00;990,00;DKK;GROCERY SHOP;Card purchase;1111;2222;Yes"],
    )

    with pytest.raises(StatementImportError) as exc_info:
        import_trusted_statement(
            statement,
            statement_format="nordea-csv",
            expected_currency="DKK",
            year=2026,
            month="Apr",
        )

    assert [diagnostic.code for diagnostic in exc_info.value.diagnostics] == [
        "out_of_period"
    ]
    assert "outside target period Apr 2026" in str(exc_info.value)


def test_trusted_statement_adapter_wraps_parser_failures_as_diagnostics(tmp_path):
    statement = tmp_path / "statement.csv"
    _write_csv(
        statement,
        ["2026/04/01;-10,00;990,00;EUR;GROCERY SHOP;Card purchase;1111;2222;Yes"],
    )

    with pytest.raises(StatementImportError) as exc_info:
        import_trusted_statement(
            statement,
            statement_format="nordea-csv",
            expected_currency="DKK",
            year=2026,
            month="Apr",
        )

    assert [diagnostic.code for diagnostic in exc_info.value.diagnostics] == [
        "unsupported_currency"
    ]
    assert "currency 'EUR' does not match expected currency 'DKK'" in str(exc_info.value)


def test_trusted_statement_adapter_pdf_route_uses_existing_parser(monkeypatch, tmp_path):
    import personal_wealth_tracker.statement_adapters as adapters

    statement = tmp_path / "statement.pdf"
    statement.write_bytes(b"%PDF-1.4 synthetic placeholder")

    def fake_parse(path: Path, expected_currency: str) -> list[Transaction]:
        assert path == statement
        assert expected_currency == "DKK"
        return [
            Transaction(
                transaction_id=f"{TRANSACTION_ID_SCHEME_VERSION}:fake:001",
                date=date(2026, 4, 3),
                interest_date=None,
                description="PDF SYNTHETIC",
                amount=Decimal("-1.00"),
                currency="DKK",
                direction="expense",
                source_file=path,
            )
        ]

    monkeypatch.setattr(adapters, "parse_nordea_pdf", fake_parse)

    result = import_trusted_statement(
        statement,
        statement_format="auto",
        expected_currency="DKK",
        year=2026,
        month="Apr",
    )

    assert result.adapter_name == "nordea-pdf"
    assert result.parser_identity == "nordea-pdf"
    assert result.transactions[0].description == "PDF SYNTHETIC"


def test_pipeline_consumes_trusted_statement_adapter_result(monkeypatch, tmp_path):
    import personal_wealth_tracker.pipeline as pipeline

    transaction = _transaction(tmp_path / "statement.csv")
    diagnostic = StatementImportDiagnostic(
        severity="warning",
        code="duplicate_row",
        message="Duplicate normalized transaction row detected.",
    )
    captured = {}

    def fake_import_trusted_statement(statement_path, **kwargs):
        captured["statement_path"] = statement_path
        captured.update(kwargs)
        return TrustedStatementImport(
            adapter_name="synthetic-csv",
            parser_identity="synthetic-csv",
            source_statement=statement_path,
            transactions=[transaction],
            diagnostics=(diagnostic,),
        )

    monkeypatch.setattr(pipeline, "load_config", lambda _config_dir: _app_config())
    monkeypatch.setattr(pipeline, "import_trusted_statement", fake_import_trusted_statement)
    monkeypatch.setattr(pipeline, "load_category_memory", lambda _memory_dir: {})
    monkeypatch.setattr(pipeline, "categorize_transactions", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(pipeline, "disabled_diagnostics", lambda _settings: LocalLLMDiagnostics())
    monkeypatch.setattr(pipeline, "plan_workbook_changes", lambda *_args: WorkbookPlan([], []))
    monkeypatch.setattr(
        pipeline,
        "write_outputs",
        lambda **_kwargs: (
            tmp_path / "report.md",
            tmp_path / "audit.jsonl",
            tmp_path / "categorized.csv",
            tmp_path / "review.csv",
            tmp_path / "review.xlsx",
        ),
    )

    result = run_pipeline(
        tracker_path=tmp_path / "tracker.xlsx",
        statement_path=tmp_path / "statement.csv",
        config_dir=tmp_path / "config",
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        statement_format="auto",
    )

    assert captured == {
        "statement_path": tmp_path / "statement.csv",
        "statement_format": "auto",
        "expected_currency": "DKK",
        "year": 2026,
        "month": "Apr",
    }
    assert result.statement_parser == "synthetic-csv"
    assert result.transactions == [transaction]
    assert result.statement_import_diagnostics == (diagnostic,)


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text(
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )


def _transaction(source_file: Path) -> Transaction:
    return Transaction(
        transaction_id=f"{TRANSACTION_ID_SCHEME_VERSION}:fake:001",
        date=date(2026, 4, 3),
        interest_date=None,
        description="SYNTHETIC",
        amount=Decimal("-1.00"),
        currency="DKK",
        direction="expense",
        source_file=source_file,
    )


def _app_config() -> AppConfig:
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
        fixed_rows=frozenset(),
    )
