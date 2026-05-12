from pathlib import Path

from openpyxl import Workbook, load_workbook

from personal_wealth_tracker.pipeline import run_pipeline


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
