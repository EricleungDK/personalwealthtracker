from pathlib import Path
from decimal import Decimal

from openpyxl import Workbook, load_workbook
import pytest

from personal_wealth_tracker.config import load_config
from personal_wealth_tracker.pipeline import run_pipeline
from personal_wealth_tracker.suggester import FakeSuggester
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


def test_pipeline_applies_exact_proxy_split_rule_without_double_counting_source(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_proxy_split_tracker(tracker)
    _create_proxy_split_config(config_dir)
    _write_revolut_statement(statement, amount="-9840,00")

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    assert len(result.transactions) == 1
    assert len(result.categorized_transactions) == 3
    source_transaction_id = result.transactions[0].transaction_id
    source_line = next(
        item
        for item in result.categorized_transactions
        if item.categorization_method == "proxy_split_source"
    )
    assert source_line.transaction.transaction_id == source_transaction_id
    assert source_line.suggested_category is None
    assert source_line.review_required is False
    assert source_line.split_rule == "revolut_family_transfer"
    assert source_line.split_role == "source"

    allocations = {
        item.suggested_category: item
        for item in result.categorized_transactions
        if item.categorization_method == "proxy_split_allocation"
    }
    assert set(allocations) == {"Dad", "Mom"}
    assert allocations["Dad"].transaction.transaction_id == (
        f"{source_transaction_id}:split:revolut_family_transfer:dad"
    )
    assert allocations["Mom"].transaction.transaction_id == (
        f"{source_transaction_id}:split:revolut_family_transfer:mom"
    )
    assert allocations["Dad"].transaction.amount == Decimal("-6560.00")
    assert allocations["Mom"].transaction.amount == Decimal("-3280.00")
    assert allocations["Dad"].source_transaction_id == source_transaction_id
    assert allocations["Mom"].source_transaction_id == source_transaction_id
    assert allocations["Dad"].split_rule == "revolut_family_transfer"
    assert allocations["Mom"].split_rule == "revolut_family_transfer"

    updates = {update.category: update for update in result.updates}
    assert set(updates) == {"Dad", "Mom"}
    assert updates["Dad"].amount == Decimal("6560.00")
    assert updates["Mom"].amount == Decimal("3280.00")
    assert source_transaction_id not in {
        transaction_id
        for update in result.updates
        for transaction_id in update.source_transactions
    }

    categorized_csv = result.categorized_csv_path.read_text(encoding="utf-8")
    assert "proxy_split_source" in categorized_csv
    assert "proxy_split_allocation" in categorized_csv
    assert f"{source_transaction_id}:split:revolut_family_transfer:dad" in categorized_csv
    assert f"{source_transaction_id}:split:revolut_family_transfer:mom" in categorized_csv

    review_csv = result.review_csv_path.read_text(encoding="utf-8")
    assert "proxy_split_source" in review_csv
    assert "proxy_split_allocation" in review_csv
    assert f"{source_transaction_id}:split:revolut_family_transfer:dad" in review_csv

    audit = result.audit_path.read_text(encoding="utf-8")
    assert '"categorization_method": "proxy_split_source"' in audit
    assert '"categorization_method": "proxy_split_allocation"' in audit
    assert f"{source_transaction_id}:split:revolut_family_transfer:dad" in audit
    assert "Dad: 6560.00" in result.report_path.read_text(encoding="utf-8")

    workbook = load_workbook(result.review_xlsx_path, data_only=True)
    try:
        audit_sheet = workbook["All Transactions"]
        headers = {cell.value: index for index, cell in enumerate(audit_sheet[1], start=1)}
        methods = [
            audit_sheet.cell(row=row, column=headers["method"]).value
            for row in range(2, audit_sheet.max_row + 1)
        ]
    finally:
        workbook.close()
    assert methods.count("proxy_split_source") == 1
    assert methods.count("proxy_split_allocation") == 2


def test_pipeline_emits_residual_proxy_split_review_line_for_larger_transfer(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_proxy_split_tracker(tracker)
    _create_proxy_split_config(config_dir)
    _write_revolut_statement(statement, amount="-12000,00")

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    source_transaction_id = result.transactions[0].transaction_id
    residual = next(
        item
        for item in result.categorized_transactions
        if item.categorization_method == "proxy_split_residual"
    )
    assert residual.transaction.transaction_id == (
        f"{source_transaction_id}:split:revolut_family_transfer:residual"
    )
    assert residual.transaction.amount == Decimal("-2160.00")
    assert residual.review_required is True
    assert residual.suggested_category is None
    assert residual.source_transaction_id == source_transaction_id
    assert residual.split_rule == "revolut_family_transfer"
    assert residual.split_role == "residual"
    assert residual.residual_amount == Decimal("2160.00")

    updates = {update.category: update for update in result.updates}
    assert set(updates) == {"Dad", "Mom"}
    assert "proxy_split_residual" in result.review_csv_path.read_text(encoding="utf-8")

    workbook = load_workbook(result.review_xlsx_path, data_only=True)
    try:
        review_sheet = workbook["Review Required"]
        headers = {cell.value: index for index, cell in enumerate(review_sheet[1], start=1)}
        review_ids = [
            review_sheet.cell(row=row, column=headers["transaction_id"]).value
            for row in range(2, review_sheet.max_row + 1)
        ]
    finally:
        workbook.close()
    assert residual.transaction.transaction_id in review_ids


def test_pipeline_applies_review_decision_to_residual_proxy_split_line_only(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_proxy_split_tracker(tracker)
    _create_proxy_split_config(config_dir)
    _write_revolut_statement(statement, amount="-12000,00")
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    residual = next(
        item
        for item in first_result.categorized_transactions
        if item.categorization_method == "proxy_split_residual"
    )
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        rows=[
            {
                "transaction_id": residual.transaction.transaction_id,
                "description": residual.transaction.description,
                "amount": str(residual.transaction.amount),
                "manual_category": "Traveling",
            }
        ],
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        review_decisions_path=review_decisions,
    )

    reviewed_residual = next(
        item
        for item in result.categorized_transactions
        if item.transaction.transaction_id == residual.transaction.transaction_id
    )
    assert reviewed_residual.suggested_category == "Traveling"
    assert reviewed_residual.categorization_method == "monthly_review_decision"
    assert reviewed_residual.review_required is False
    assert reviewed_residual.transaction.amount == Decimal("-2160.00")
    assert reviewed_residual.source_transaction_id == first_result.transactions[0].transaction_id

    updates = {update.category: update for update in result.updates}
    assert updates["Dad"].amount == Decimal("6560.00")
    assert updates["Mom"].amount == Decimal("3280.00")
    assert updates["Traveling"].amount == Decimal("2160.00")
    assert updates["Traveling"].source_transactions == (residual.transaction.transaction_id,)


def test_pipeline_keeps_underfunded_proxy_split_candidate_review_only(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_proxy_split_tracker(tracker)
    _create_proxy_split_config(config_dir)
    _write_revolut_statement(statement, amount="-9000,00")

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    assert len(result.categorized_transactions) == 1
    blocked = result.categorized_transactions[0]
    assert blocked.categorization_method == "proxy_split_blocked"
    assert blocked.review_required is True
    assert blocked.suggested_category is None
    assert blocked.split_rule == "revolut_family_transfer"
    assert blocked.split_role == "source"
    assert "below configured proxy split allocation total" in blocked.reason
    assert result.updates == []
    assert "proxy_split_blocked" in result.review_csv_path.read_text(encoding="utf-8")


def test_pipeline_blocks_multiple_proxy_split_candidates_in_one_reporting_month(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_proxy_split_tracker(tracker)
    _create_proxy_split_config(config_dir)
    _write(
        statement,
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        "2026/04/04;-9840,00;50000,00;DKK;REVOLUT;Transfer;1111;2222;Yes\n"
        "2026/04/18;-12000,00;38000,00;DKK;REVOLUT;Transfer;1111;2222;Yes\n",
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    assert len(result.categorized_transactions) == 2
    assert {item.categorization_method for item in result.categorized_transactions} == {
        "proxy_split_blocked"
    }
    assert all(item.review_required for item in result.categorized_transactions)
    assert all(
        "Multiple proxy split candidates" in item.reason
        for item in result.categorized_transactions
    )
    assert result.updates == []
    report = result.report_path.read_text(encoding="utf-8")
    assert "Multiple proxy split candidates" in report
    assert "Dad: 6560.00" not in report


def test_pipeline_allows_multiple_proxy_split_candidates_up_to_configured_limit(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_proxy_split_tracker(tracker)
    _create_proxy_split_config(config_dir, monthly_limit=2)
    _write(
        statement,
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        "2026/04/04;-9840,00;50000,00;DKK;REVOLUT;Transfer;1111;2222;Yes\n"
        "2026/04/18;-15000,00;35000,00;DKK;REVOLUT;Transfer;1111;2222;Yes\n",
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
    )

    assert len(result.transactions) == 2
    assert sum(
        1
        for item in result.categorized_transactions
        if item.categorization_method == "proxy_split_source"
    ) == 2
    assert sum(
        1
        for item in result.categorized_transactions
        if item.categorization_method == "proxy_split_allocation"
        and item.suggested_category == "Dad"
    ) == 2
    assert sum(
        1
        for item in result.categorized_transactions
        if item.categorization_method == "proxy_split_allocation"
        and item.suggested_category == "Mom"
    ) == 2
    assert not any(
        item.categorization_method == "proxy_split_blocked"
        for item in result.categorized_transactions
    )

    residuals = [
        item
        for item in result.categorized_transactions
        if item.categorization_method == "proxy_split_residual"
    ]
    assert len(residuals) == 1
    assert residuals[0].transaction.amount == Decimal("-5160.00")

    updates = {update.category: update for update in result.updates}
    assert updates["Dad"].amount == Decimal("13120.00")
    assert updates["Mom"].amount == Decimal("6560.00")
    assert "Multiple proxy split candidates" not in result.report_path.read_text(
        encoding="utf-8"
    )


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


def test_pipeline_accepts_manual_review_category_registered_as_missing_leaf(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_tracker(tracker)
    _create_category_registry_config(config_dir)
    _write_unknown_shop_statement(statement)
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    transaction = first_result.categorized_transactions[0].transaction
    config_path = config_dir / "categories.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            '      - "Traveling"\n',
            '      - "Traveling"\n      - "Pet Supplies"\n',
        ),
        encoding="utf-8",
    )
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        rows=[
            {
                "transaction_id": transaction.transaction_id,
                "description": transaction.description,
                "amount": str(transaction.amount),
                "manual_category": "Pet Supplies",
            }
        ],
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        review_decisions_path=review_decisions,
    )

    reviewed = result.categorized_transactions[0]
    assert reviewed.suggested_category == "Pet Supplies"
    assert reviewed.categorization_method == "monthly_review_decision"
    assert result.updates[0].category == "Pet Supplies"
    assert result.updates[0].reason == "Target category row not found."


def test_pipeline_local_llm_suggestion_is_review_only_and_reuses_review_fields(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_tracker(tracker)
    _create_category_registry_config(config_dir)
    _write_unknown_shop_statement(statement)
    suggester = FakeSuggester(
        {"UNKNOWN SHOP": ("Traveling", 0.68, "Merchant looks travel related.")}
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        local_llm_suggestions=True,
        suggester=suggester,
    )

    item = result.categorized_transactions[0]
    assert item.suggested_category == "Traveling"
    assert item.categorization_method == "local_llm_gemma"
    assert item.review_required is True
    assert result.updates[0].category == "Traveling"
    assert result.updates[0].write_action == "review"
    assert result.updates[0].reason == "One or more source transactions require review."

    report = result.report_path.read_text(encoding="utf-8")
    assert "## Local LLM Mode" in report
    assert "- Status: enabled" in report
    assert "- Eligible rows: 1" in report
    assert "- Provider calls attempted: 1" in report
    assert "- Existing-leaf suggestions: 1" in report
    assert "- local_llm_gemma: 1" in report

    audit = result.audit_path.read_text(encoding="utf-8")
    assert '"record_type": "local_llm_summary"' in audit
    assert '"existing_leaf_suggestions": 1' in audit
    assert '"categorization_method": "local_llm_gemma"' in audit

    workbook = load_workbook(result.review_xlsx_path, data_only=True)
    try:
        review_sheet = workbook["Review Required"]
        headers = {cell.value: index for index, cell in enumerate(review_sheet[1], start=1)}
        assert "llm_suggested_category" not in headers
        assert "llm_reason" not in headers
        assert review_sheet.cell(row=2, column=headers["suggested_category"]).value == "Traveling"
        assert review_sheet.cell(row=2, column=headers["method"]).value == "local_llm_gemma"
        assert "Merchant looks travel related." in review_sheet.cell(
            row=2, column=headers["reason"]
        ).value
    finally:
        workbook.close()


def test_pipeline_includes_reviewed_policy_in_local_llm_prompt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    memory_dir = tmp_path / "data" / "category_memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "reviewed_policy.local.md").write_text(
        "\n".join(
            [
                "# Reviewed Policy",
                "",
                "<!-- AUTO-GENERATED REVIEWED EXAMPLES START -->",
                "- Merchant identity: `MOBILEPAY REJSEKORT` -> `Traveling`",
                "<!-- AUTO-GENERATED REVIEWED EXAMPLES END -->",
                "",
                "## Manual Guidance",
                "",
                "- Prefer no_suggestion for unknown private transfers.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _create_tracker(tracker)
    _create_category_registry_config(config_dir)
    _write_unknown_shop_statement(statement)
    suggester = FakeSuggester({})

    run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        category_memory_dir=memory_dir,
        local_llm_suggestions=True,
        suggester=suggester,
    )

    _, context = suggester.calls[0]
    assert "MOBILEPAY REJSEKORT" in context.reviewed_policy
    assert "unknown private transfers" in context.reviewed_policy
    assert set(context.leaf_glossary) == {"Apple Cloud", "Traveling", "Full-time job (net)"}


def test_pipeline_registers_new_leaf_category_from_review_decisions(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_tracker(tracker)
    _create_category_registry_config(config_dir)
    _write_unknown_shop_statement(statement)

    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    transaction = first_result.categorized_transactions[0].transaction
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        include_new_category_columns=True,
        rows=[
            {
                "transaction_id": transaction.transaction_id,
                "description": transaction.description,
                "amount": str(transaction.amount),
                "manual_category": "",
                "new_parent_category": "Living expenses",
                "new_leaf_category": "Pet Supplies",
            }
        ],
    )

    result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "reports",
        review_decisions_path=review_decisions,
    )

    reviewed = result.categorized_transactions[0]
    assert reviewed.suggested_category == "Pet Supplies"
    assert reviewed.categorization_method == "monthly_review_decision"
    assert reviewed.review_required is False
    assert result.output_workbook_path is None
    update = result.updates[0]
    assert update.category == "Pet Supplies"
    assert update.write_action == "review"
    assert update.reason == "Target category row not found."

    config = load_config(config_dir)
    assert "Pet Supplies" in config.category_registry.leaf_categories
    assert config.category_registry.children_by_parent["Living expenses"] == (
        "Apple Cloud",
        "Traveling",
        "Pet Supplies",
    )
    report = result.report_path.read_text(encoding="utf-8")
    assert "## Category Registry Updates" in report
    assert "Pet Supplies under Living expenses" in report
    audit = result.audit_path.read_text(encoding="utf-8")
    assert '"record_type": "category_registry_addition"' in audit
    assert '"leaf_category": "Pet Supplies"' in audit


def test_pipeline_rejects_new_leaf_category_duplicate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_tracker(tracker)
    _create_category_registry_config(config_dir)
    _write_unknown_shop_statement(statement)
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        include_new_category_columns=True,
        rows=[
            {
                "transaction_id": first_result.transactions[0].transaction_id,
                "description": "duplicate leaf",
                "amount": "-1",
                "manual_category": "",
                "new_parent_category": "Living expenses",
                "new_leaf_category": " apple cloud ",
            }
        ],
    )

    with pytest.raises(ValueError, match="Duplicate category label.*Apple Cloud.*apple cloud"):
        run_pipeline(
            tracker_path=tracker,
            statement_path=statement,
            config_dir=config_dir,
            year=2026,
            month="Apr",
            output_dir=tmp_path / "reports",
            review_decisions_path=review_decisions,
        )


def test_pipeline_rejects_new_leaf_category_for_invalid_parent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_tracker(tracker)
    _create_category_registry_config(config_dir)
    _write_unknown_shop_statement(statement)
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        include_new_category_columns=True,
        rows=[
            {
                "transaction_id": first_result.transactions[0].transaction_id,
                "description": "invalid parent",
                "amount": "-1",
                "manual_category": "",
                "new_parent_category": "Income (net)",
                "new_leaf_category": "Pet Supplies",
            }
        ],
    )

    with pytest.raises(ValueError, match="new_parent_category.*Income \\(net\\).*not allowed"):
        run_pipeline(
            tracker_path=tracker,
            statement_path=statement,
            config_dir=config_dir,
            year=2026,
            month="Apr",
            output_dir=tmp_path / "reports",
            review_decisions_path=review_decisions,
        )


def test_pipeline_rejects_review_row_with_manual_and_new_leaf_category(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    tracker = tmp_path / "tracker.xlsx"
    config_dir = tmp_path / "config"
    statement = tmp_path / "statement.csv"
    _create_tracker(tracker)
    _create_category_registry_config(config_dir)
    _write_unknown_shop_statement(statement)
    first_result = run_pipeline(
        tracker_path=tracker,
        statement_path=statement,
        config_dir=config_dir,
        year=2026,
        month="Apr",
        output_dir=tmp_path / "first_reports",
    )
    review_decisions = tmp_path / "review_required_2026_apr.xlsx"
    _write_review_decisions(
        review_decisions,
        year=2026,
        month="Apr",
        include_new_category_columns=True,
        rows=[
            {
                "transaction_id": first_result.transactions[0].transaction_id,
                "description": "conflicting row",
                "amount": "-1",
                "manual_category": "Apple Cloud",
                "new_parent_category": "Living expenses",
                "new_leaf_category": "Pet Supplies",
            }
        ],
    )

    with pytest.raises(ValueError, match="manual_category.*new_leaf_category"):
        run_pipeline(
            tracker_path=tracker,
            statement_path=statement,
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


def _create_proxy_split_tracker(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Net worth"
    sheet["C2"] = 2026
    sheet["C3"] = "Apr"
    sheet["B5"] = "Dad"
    sheet["B6"] = "Mom"
    sheet["B7"] = "Traveling"
    workbook.save(path)
    workbook.close()


def _create_proxy_split_config(config_dir: Path, monthly_limit: int = 1) -> None:
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
        """
category_registry:
  - label: "Living expenses"
    type: "parent"
    allow_new_children: true
    children:
      - "Dad"
      - "Mom"
      - "Traveling"
aliases: {}
""",
    )
    _write(config_dir / "rules.yaml", "historical_mappings: {}\nrules: []\nfixed_rows: []\n")
    _write(
        config_dir / "rules.local.yaml",
        f"""
proxy_split_rules:
  - name: revolut_family_transfer
    match_keywords: [revolut]
    direction: expense
    conversion_rate: "0.82"
    monthly_limit: {monthly_limit}
    allocations:
      - role: dad
        category: Dad
        base_amount: "8000"
      - role: mom
        category: Mom
        base_amount: "4000"
""",
    )


def _write_revolut_statement(path: Path, amount: str) -> None:
    _write(
        path,
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        f"2026/04/04;{amount};50000,00;DKK;REVOLUT;Transfer;1111;2222;Yes\n",
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


def _create_category_registry_config(config_dir: Path) -> None:
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
        """
category_registry:
  - label: "Living expenses"
    type: "parent"
    allow_new_children: true
    children:
      - "Apple Cloud"
      - "Traveling"
  - label: "Income (net)"
    type: "derived"
  - "Full-time job (net)"
aliases: {}
""",
    )
    _write(
        config_dir / "rules.yaml",
        """
historical_mappings: {}
rules: []
fixed_rows: []
""",
    )


def _write_unknown_shop_statement(path: Path) -> None:
    _write(
        path,
        "\ufeffBooking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled\n"
        "2026/04/01;-42,50;957,50;DKK;UNKNOWN SHOP;Card purchase;1111;2222;Yes\n",
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
    include_new_category_columns: bool = False,
) -> None:
    workbook = Workbook()
    review_sheet = workbook.active
    review_sheet.title = "Review Required"
    headers = [
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
    ]
    if include_new_category_columns:
        headers.extend(["new_parent_category", "new_leaf_category"])
    headers.append("learn_to_memory")
    review_sheet.append(headers)
    for row in rows:
        payload = {
            "transaction_id": row["transaction_id"],
            "date": "2026-04-01",
            "description": row["description"],
            "amount": row["amount"],
            "direction": "expense",
            "merchant_identity": "",
            "suggested_category": "",
            "confidence": "",
            "method": "",
            "reason": "",
            "manual_category": row["manual_category"],
            "new_parent_category": row.get("new_parent_category", ""),
            "new_leaf_category": row.get("new_leaf_category", ""),
            "learn_to_memory": "",
        }
        review_sheet.append([payload[header] for header in headers])
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
