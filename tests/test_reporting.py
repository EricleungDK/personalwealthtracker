from datetime import date
from decimal import Decimal

from personal_wealth_tracker.models import (
    CategorizedTransaction,
    TrackerUpdate,
    Transaction,
    WorkbookStructureChange,
)
from personal_wealth_tracker.reporting import write_outputs


def test_report_includes_refund_and_expense_claim_source_reasons(tmp_path):
    categorized = [
        _categorized(
            "tx-refund",
            "NETTO REFUND",
            "25.00",
            "Food& Drinks (monthly)",
            "Refund matched expense keyword rule; nets against category in reporting month.",
        ),
        _categorized(
            "tx-claim",
            "ACME EXPENSE CLAIM",
            "125.00",
            "Expense claims",
            "Expense claim keyword rule match.",
        ),
    ]
    updates = [
        _update(
            "Food& Drinks (monthly)",
            Decimal("-25.00"),
            ("tx-refund",),
            "D5",
        ),
        _update(
            "Expense claims",
            Decimal("125.00"),
            ("tx-claim",),
            "D22",
        ),
    ]

    report_path, _, _, _ = write_outputs(
        output_dir=tmp_path,
        mode="dry-run",
        year=2026,
        month="May",
        source_statement=tmp_path / "statement.pdf",
        tracker_path=tmp_path / "tracker.xlsx",
        categorized=categorized,
        updates=updates,
    )

    report = report_path.read_text(encoding="utf-8")
    assert "Refund matched expense keyword rule" in report
    assert "Expense claim keyword rule match." in report


def test_report_and_audit_include_planned_period_creation(tmp_path):
    report_path, audit_path, _, _ = write_outputs(
        output_dir=tmp_path,
        mode="dry-run",
        year=2026,
        month="Apr",
        source_statement=tmp_path / "statement.pdf",
        tracker_path=tmp_path / "tracker.xlsx",
        categorized=[],
        updates=[],
        structure_changes=[
            WorkbookStructureChange(
                change_type="create_period",
                target_year=2026,
                target_months=("Apr",),
                source_range="C:C",
                target_range="D:D",
                write_action="write",
                reason="Create missing Apr 2026 period from C:C.",
            )
        ],
    )

    report = report_path.read_text(encoding="utf-8")
    assert "## Planned Structure Changes" in report
    assert "create_period: Apr 2026, C:C -> D:D (write;" in report

    audit = audit_path.read_text(encoding="utf-8")
    assert '"record_type": "workbook_structure_change"' in audit
    assert '"change_type": "create_period"' in audit
    assert '"target_months": ["Apr"]' in audit


def test_report_and_audit_include_statement_parser(tmp_path):
    categorized = [
        _categorized(
            "tx-food",
            "FOETEX SCANNGO",
            "-123.45",
            "Food& Drinks (monthly)",
            "Keyword rule match.",
        )
    ]

    report_path, audit_path, _, _ = write_outputs(
        output_dir=tmp_path,
        mode="dry-run",
        year=2026,
        month="Apr",
        source_statement=tmp_path / "statement.csv",
        statement_parser="nordea-csv",
        tracker_path=tmp_path / "tracker.xlsx",
        categorized=categorized,
        updates=[],
        structure_changes=[
            WorkbookStructureChange(
                change_type="create_period",
                target_year=2026,
                target_months=("Apr",),
                source_range="C:C",
                target_range="D:D",
                write_action="write",
                reason="Create missing Apr 2026 period from C:C.",
            )
        ],
    )

    report = report_path.read_text(encoding="utf-8")
    assert "- Statement parser: nordea-csv" in report

    audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert '"statement_parser": "nordea-csv"' in audit_lines[0]
    assert '"statement_parser": "nordea-csv"' in audit_lines[1]


def _categorized(
    transaction_id: str,
    description: str,
    amount: str,
    category: str,
    reason: str,
) -> CategorizedTransaction:
    amount_value = Decimal(amount)
    return CategorizedTransaction(
        transaction=Transaction(
            transaction_id=transaction_id,
            date=date(2026, 5, 15),
            interest_date=None,
            description=description,
            amount=amount_value,
            currency="DKK",
            direction="income" if amount_value >= Decimal("0") else "expense",
        ),
        suggested_category=category,
        confidence=0.95,
        categorization_method="rule",
        review_required=False,
        reason=reason,
    )


def _update(
    category: str,
    amount: Decimal,
    source_transactions: tuple[str, ...],
    target_cell: str,
) -> TrackerUpdate:
    return TrackerUpdate(
        year=2026,
        month="May",
        category=category,
        amount=amount,
        source_transactions=source_transactions,
        target_row=5,
        target_column=4,
        target_cell=target_cell,
        existing_value=None,
        write_action="write",
        reason="Eligible for commit mode write.",
    )
