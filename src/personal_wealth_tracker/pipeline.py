from __future__ import annotations

from pathlib import Path

from .categorizer import categorize_transactions
from .config import load_config
from .models import RunResult
from .nordea_pdf import parse_nordea_pdf
from .reporting import write_outputs
from .utils import normalize_month
from .workbook import commit_updates, create_backup, plan_updates


def run_pipeline(
    tracker_path: Path,
    statement_path: Path,
    config_dir: Path,
    year: int,
    month: str,
    output_dir: Path,
    commit: bool = False,
) -> RunResult:
    month = normalize_month(month)
    config = load_config(config_dir)

    transactions = parse_nordea_pdf(statement_path)
    categorized = categorize_transactions(transactions, config)
    updates = plan_updates(tracker_path, categorized, year, month, config)
    mode = "commit" if commit else "dry-run"

    output_workbook_path = None
    if commit:
        create_backup(tracker_path, Path("data/backups"))
        output_workbook_path = commit_updates(tracker_path, updates, config, Path("data/processed"))

    report_path, audit_path, categorized_csv_path, review_csv_path = write_outputs(
        output_dir=output_dir,
        mode=mode,
        year=year,
        month=month,
        source_statement=statement_path,
        tracker_path=tracker_path,
        categorized=categorized,
        updates=updates,
    )

    return RunResult(
        mode=mode,
        target_year=year,
        target_month=month,
        transactions=transactions,
        categorized_transactions=categorized,
        updates=updates,
        report_path=report_path,
        audit_path=audit_path,
        categorized_csv_path=categorized_csv_path,
        review_csv_path=review_csv_path,
        output_workbook_path=output_workbook_path,
    )
