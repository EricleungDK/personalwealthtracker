from pathlib import Path

from openpyxl import Workbook, load_workbook
import pytest

from personal_wealth_tracker.pipeline import run_pipeline
from personal_wealth_tracker.utils import TRANSACTION_ID_SCHEME_VERSION


FIXTURE = Path(__file__).parent / "fixtures" / "nordea_account_statement.redacted.pdf"


def test_pipeline_dry_run_writes_outputs_without_changing_workbook(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    workbook = load_workbook(tracker)
    try:
        sheet = workbook["Net worth"]
        assert sheet["C5"].value is None
        assert sheet["C6"].value is None
        assert sheet["C7"].value is None
    finally:
        workbook.close()

    assert result.mode == "dry-run"
    assert result.output_workbook_path is None
    assert len(result.transactions) == 3
    assert {update.category for update in result.updates} == {
        "Apple Cloud",
        "Full-time job (net)",
        "Traveling",
    }
    assert result.report_path.exists()
    assert result.audit_path.exists()
    assert result.categorized_csv_path.exists()
    assert result.review_csv_path.exists()
    assert result.review_xlsx_path == tmp_path / "reports" / "review_required_2026_apr.xlsx"
    assert result.review_xlsx_path.exists()


def test_pipeline_dry_run_reports_missing_period_creation_without_changing_workbook(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    workbook = load_workbook(tracker)
    try:
        sheet = workbook["Net worth"]
        sheet["C3"] = "Mar"
        workbook.save(tracker)
    finally:
        workbook.close()

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    original = load_workbook(tracker)
    try:
        assert original["Net worth"]["D3"].value is None
    finally:
        original.close()

    assert len(result.structure_changes) == 1
    assert result.structure_changes[0].change_type == "create_period"
    report = result.report_path.read_text(encoding="utf-8")
    assert "## Planned Structure Changes" in report
    assert "create_period: Apr 2026" in report


def test_pipeline_commit_writes_only_to_copied_workbook(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        commit=True,
    )

    original = load_workbook(tracker)
    copied = load_workbook(result.output_workbook_path)
    try:
        original_sheet = original["Net worth"]
        copied_sheet = copied["Net worth"]
        assert original_sheet["C5"].value is None
        assert original_sheet["C6"].value is None
        assert original_sheet["C7"].value is None
        assert copied_sheet["C5"].value == 25
        assert copied_sheet["C6"].value == 10000
        assert copied_sheet["C7"].value == 86.1
    finally:
        original.close()
        copied.close()

    assert result.mode == "commit"
    assert result.output_workbook_path is not None
    assert result.output_workbook_path.exists()
    assert list((tmp_path / "data" / "backups").glob("tracker_backup_*.xlsx"))


def test_monthly_commit_does_not_perform_currency_label_cleanup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    _set_workbook_label(tracker, "A1", "Tracker currency: EUR")

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        commit=True,
    )

    original = load_workbook(tracker)
    copied = load_workbook(result.output_workbook_path)
    try:
        assert original["Net worth"]["A1"].value == "Tracker currency: EUR"
        assert copied["Net worth"]["A1"].value == "Tracker currency: EUR"
    finally:
        original.close()
        copied.close()

    report = result.report_path.read_text(encoding="utf-8")
    assert "Workbook cleanup tasks: not run during monthly update." in report


def test_pipeline_review_csv_includes_skipped_derived_workbook_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir, salary_category="Income (net)")

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    review_csv = result.review_csv_path.read_text(encoding="utf-8")
    assert "workbook_update" in review_csv
    assert "Income (net)" in review_csv
    assert "Derived workbook row is formula-owned and not writable." in review_csv


def test_pipeline_applies_explicit_monthly_review_decisions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    reviewed_transaction = next(
        item
        for item in first_result.categorized_transactions
        if item.suggested_category == "Traveling"
    )
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        rows=[
            {
                "transaction_id": reviewed_transaction.transaction.transaction_id,
                "description": reviewed_transaction.transaction.description,
                "amount": str(reviewed_transaction.transaction.amount),
                "manual_category": "Apple Cloud",
            },
            {
                "transaction_id": first_result.categorized_transactions[0].transaction.transaction_id,
                "description": "ignored because blank manual category",
                "amount": "0",
                "manual_category": "",
            },
        ],
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        review_decisions_path=review_decisions,
    )

    reviewed = next(
        item
        for item in result.categorized_transactions
        if item.transaction.transaction_id == reviewed_transaction.transaction.transaction_id
    )
    assert reviewed.suggested_category == "Apple Cloud"
    assert reviewed.categorization_method == "monthly_review_decision"
    assert reviewed.review_required is False
    assert {update.category for update in result.updates} == {"Apple Cloud", "Full-time job (net)"}
    assert "monthly_review_decision" in result.categorized_csv_path.read_text(encoding="utf-8")
    assert "monthly_review_decision" in result.audit_path.read_text(encoding="utf-8")
    assert "- monthly_review_decision: 1" in result.report_path.read_text(encoding="utf-8")


def test_pipeline_preserves_review_decisions_when_input_is_default_review_output(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    output_dir = tmp_path / "reports"
    statement = tmp_path / "statement.csv"
    _create_tracker(tracker)
    _create_config(config_dir)
    _write(
        statement,
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        "2026/04/01;-42,50;957,50;DKK;UNKNOWN SHOP;Card purchase;1111;2222;Yes\n",
    )
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=output_dir,
    )
    review_decisions = first_result.review_xlsx_path
    reviewed_transaction = first_result.categorized_transactions[0]
    workbook = load_workbook(review_decisions)
    try:
        review_sheet = workbook["Review Required"]
        headers = {cell.value: index for index, cell in enumerate(review_sheet[1], start=1)}
        for row in range(2, review_sheet.max_row + 1):
            if (
                review_sheet.cell(row=row, column=headers["transaction_id"]).value
                == reviewed_transaction.transaction.transaction_id
            ):
                review_sheet.cell(row=row, column=headers["manual_category"]).value = "Apple Cloud"
                break
        else:
            raise AssertionError("review row not found")
        workbook.save(review_decisions)
    finally:
        workbook.close()

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=output_dir,
        review_decisions_path=review_decisions,
    )

    preserved = load_workbook(review_decisions, data_only=True)
    try:
        review_sheet = preserved["Review Required"]
        headers = {cell.value: index for index, cell in enumerate(review_sheet[1], start=1)}
        manual_values = [
            review_sheet.cell(row=row, column=headers["manual_category"]).value
            for row in range(2, review_sheet.max_row + 1)
        ]
    finally:
        preserved.close()

    assert "Apple Cloud" in manual_values
    assert result.review_xlsx_path == output_dir / "review_required_2026_apr_after_decisions.xlsx"
    assert result.review_xlsx_path.exists()
    assert "- monthly_review_decision: 1" in result.report_path.read_text(encoding="utf-8")


def test_pipeline_rejects_review_decisions_for_wrong_period(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    review_decisions = tmp_path / "review_required_2026_may.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="May",
        rows=[],
    )

    with pytest.raises(ValueError, match="review decisions.*May 2026.*Apr 2026"):
        run_pipeline(
            tracker_path=tracker,
            statement_path=FIXTURE,
            config_dir=config_dir,
            year=2026,
            month="Apr",
            output_dir=tmp_path / "reports",
            review_decisions_path=review_decisions,
        )


def test_pipeline_rejects_review_decisions_for_unknown_transaction_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        rows=[
            {
                "transaction_id": f"{TRANSACTION_ID_SCHEME_VERSION}:missing:001",
                "description": "stale row",
                "amount": "-1",
                "manual_category": "Apple Cloud",
            }
        ],
    )

    with pytest.raises(ValueError, match="not present in current statement"):
        run_pipeline(
            tracker_path=tracker,
            statement_path=FIXTURE,
            config_dir=config_dir,
            year=2026,
            month="Apr",
            output_dir=tmp_path / "reports",
            review_decisions_path=review_decisions,
        )


def test_monthly_review_decision_preserves_workbook_write_safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    transaction_id = first_result.categorized_transactions[0].transaction.transaction_id
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        rows=[
            {
                "transaction_id": transaction_id,
                "description": "manual derived row",
                "amount": "-1",
                "manual_category": "Income (net)",
            }
        ],
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        review_decisions_path=review_decisions,
    )

    income_update = next(update for update in result.updates if update.category == "Income (net)")
    assert income_update.write_action == "skip"
    assert income_update.reason == "Derived workbook row is formula-owned and not writable."


def test_pipeline_rejects_manual_review_category_missing_from_current_tracker(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=FIXTURE,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    transaction_id = first_result.categorized_transactions[0].transaction.transaction_id
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        rows=[
            {
                "transaction_id": transaction_id,
                "description": "manual category that is not in the tracker",
                "amount": "-1",
                "manual_category": "Missing Tracker Category",
            }
        ],
    )

    with pytest.raises(ValueError, match="manual_category.*Missing Tracker Category"):
        run_pipeline(
            tracker_path=tracker,
            statement_path=FIXTURE,
            config_dir=config_dir,
            year=2026,
            month="Apr",
            output_dir=tmp_path / "reports",
            review_decisions_path=review_decisions,
        )


def test_pipeline_rejects_review_decisions_with_unsupported_transaction_id_scheme(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    _create_tracker(tracker)
    _create_config(config_dir)
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        transaction_id_scheme="legacy-v0",
        rows=[],
    )

    with pytest.raises(ValueError, match="Unsupported review decision transaction ID scheme"):
        run_pipeline(
            tracker_path=tracker,
            statement_path=FIXTURE,
            config_dir=config_dir,
            year=2026,
            month="Apr",
            output_dir=tmp_path / "reports",
            review_decisions_path=review_decisions,
        )


def _create_tracker(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Net worth"
    sheet["C2"] = 2026
    sheet["C3"] = "Apr"
    sheet["B5"] = "Apple Cloud"
    sheet["B6"] = "Full-time job (net)"
    sheet["B7"] = "Traveling"
    sheet["B8"] = "Income (net)"
    workbook.save(path)
    workbook.close()


def _create_config(config_dir: Path, salary_category: str = "Full-time job (net)") -> None:
    config_dir.mkdir(parents=True)
    _write(
        config_dir / "settings.yaml",
        """
tracker:
  sheet_name: "Net worth"
  currency: "DKK"
  category_column: 2
  year_header_row: 2
  month_header_row: 3
statement:
  currency: "DKK"
confidence_thresholds:
  auto_write: 0.85
  review_required: 0.60
  reject_below: 0.60
writer:
  overwrite_fixed_rows: false
  highlight_auto_filled_cells: false
""",
    )
    _write(
        config_dir / "categories.yaml",
        f"""
categories:
  - "Apple Cloud"
  - "{salary_category}"
  - "Traveling"
aliases: {{}}
""",
    )
    _write(
        config_dir / "rules.yaml",
        f"""
historical_mappings:
  "APPLE.COM/BILL": "Apple Cloud"
rules:
  - category: "{salary_category}"
    match_keywords: ["salary"]
    direction: "income"
    confidence: 0.95
  - category: "Traveling"
    match_keywords: ["foreign card"]
    direction: "expense"
    confidence: 0.95
fixed_rows: []
""",
    )


def _write(path: Path, content: str) -> None:
    path.write_text(content.lstrip(), encoding="utf-8")


def _set_workbook_label(path: Path, cell: str, value: str) -> None:
    workbook = load_workbook(path)
    try:
        workbook["Net worth"][cell] = value
        workbook.save(path)
    finally:
        workbook.close()


def _write_review_decisions(
    path: Path,
    year: int,
    month: str,
    rows: list[dict[str, str]],
    transaction_id_scheme: str = TRANSACTION_ID_SCHEME_VERSION,
) -> None:
    workbook = Workbook()
    review_sheet = workbook.active
    review_sheet.title = "Review Required"
    review_sheet.append(
        [
            "transaction_id",
            "date",
            "description",
            "amount",
            "direction",
            "merchant_identity",
            "suggested_category",
            "confidence",
            "method",
            "reason",
            "manual_category",
            "learn_to_memory",
        ]
    )
    for row in rows:
        review_sheet.append(
            [
                row["transaction_id"],
                "2026-04-01",
                row["description"],
                row["amount"],
                "expense",
                "",
                "",
                "",
                "",
                "",
                row["manual_category"],
                "",
            ]
        )
    metadata_sheet = workbook.create_sheet("Run Metadata")
    for key, value in [
        ("reporting_year", year),
        ("reporting_month", month),
        ("statement_parser", "nordea-pdf"),
        ("generated_timestamp", "2026-05-16T10:00:00"),
        ("transaction_id_scheme", transaction_id_scheme),
    ]:
        metadata_sheet.append([key, value])
    workbook.save(path)
    workbook.close()
